from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    import matplotlib.pyplot as plt
    PLOTLY_AVAILABLE = False

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analytics.curve import build_futures_curve, classify_curve, add_curve_metrics, add_convenience_yield
from analytics.hedging import hedge_summary, hedge_scenarios
from analytics.risk import historical_var, stress_test, realized_volatility
from analytics.spread import spread_analysis, zscore_signal
from analytics.commodity_metrics import curve_tightness_score, scenario_library, pnl_attribution
from data.market_data import load_history
from database.sqlite_store import save_dataframe, DB_PATH
from models.black76 import black76_greeks
from models.ml_signals import train_direction_model, anomaly_detection
from utils.config import COMMODITY_CONFIG, CONTRACT_LABELS

st.set_page_config(
    page_title="Commodity Trading Desk Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
    .main-header {
        padding: 1.2rem 1.4rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #101828 0%, #1D2939 55%, #344054 100%);
        color: white;
        margin-bottom: 1rem;
    }
    .main-header h1 {margin: 0; font-size: 2.15rem;}
    .main-header p {margin: .35rem 0 0 0; color: #D0D5DD;}
    .desk-card {
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid #EAECF0;
        background: #FFFFFF;
        box-shadow: 0 1px 2px rgba(16,24,40,.06);
    }
    .small-muted {font-size: .88rem; color: #667085;}
    .section-note {
        padding: .85rem 1rem;
        border-left: 4px solid #344054;
        background: #F9FAFB;
        border-radius: 10px;
        margin-top: .6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def money(x: float) -> str:
    return f"${x:,.0f}"


def pct(x: float) -> str:
    return f"{x:.2%}"


def excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe = df.copy()
            for col in safe.select_dtypes(include=["datetimetz"]).columns:
                safe[col] = safe[col].dt.tz_localize(None)
            safe.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()


def line_chart(df: pd.DataFrame, x: str, y: str, title: str):
    if PLOTLY_AVAILABLE:
        fig = px.line(df, x=x, y=y, title=title)
        fig.update_layout(height=430, margin=dict(l=20, r=20, t=55, b=20), hovermode="x unified")
        return fig
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df[x], df[y])
    ax.set_title(title)
    ax.grid(True)
    return fig


def curve_chart(curve: pd.DataFrame, title: str):
    if PLOTLY_AVAILABLE:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=curve["contract"], y=curve["futures_price"], mode="lines+markers", name="Futures"))
        fig.update_layout(title=title, xaxis_title="Contract", yaxis_title="Futures price", height=430, margin=dict(l=20, r=20, t=55, b=20))
        return fig
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(curve["contract"], curve["futures_price"], marker="o")
    ax.set_title(title)
    ax.grid(True)
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str):
    if PLOTLY_AVAILABLE:
        fig = px.bar(df, x=x, y=y, title=title)
        fig.update_layout(height=420, margin=dict(l=20, r=20, t=55, b=20))
        return fig
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(df[x], df[y])
    ax.set_title(title)
    ax.grid(True)
    return fig


def show_chart(fig):
    if PLOTLY_AVAILABLE:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.pyplot(fig)


st.markdown(
    """
    <div class="main-header">
        <h1>Commodity Trading Desk Dashboard</h1>
        <p>Futures curve analytics, physical hedging, risk monitoring, spread analysis, Black-76 Greeks, ML signals and SQL reporting.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Desk inputs")
    commodity = st.selectbox("Commodity universe", list(COMMODITY_CONFIG.keys()))
    config = COMMODITY_CONFIG[commodity]
    period = st.selectbox("Historical market-data window", ["6mo", "1y", "2y", "5y"], index=1)

    st.divider()
    st.subheader("Cost-of-carry assumptions")
    risk_free_rate = st.number_input("Risk-free rate", 0.0, 0.20, 0.035, 0.005, format="%.3f")
    storage_cost = st.number_input("Storage / carry cost", 0.0, 0.30, 0.015, 0.005, format="%.3f")

    st.divider()
    st.subheader("Curve marks")
    st.caption("Public data rarely gives a full clean curve. These marks simulate desk curve inputs and can be replaced by Bloomberg/Refinitiv.")
    prices = []
    for label, default in zip(CONTRACT_LABELS, config["fallback_curve"]):
        prices.append(st.number_input(f"{label} futures", min_value=0.01, value=float(default), step=0.10, format="%.2f"))

    st.divider()
    st.subheader("Physical book / hedge")
    exposure = st.number_input(
        f"Exposure in {config['unit']}",
        min_value=0.0,
        value=100000.0 if config["unit"] == "barrels" else 50000.0,
        step=1000.0,
    )
    hedge_ratio = st.slider("Hedge ratio", 0.0, 1.0, 1.0, 0.05)
    hedge_contract = st.selectbox("Hedge contract", CONTRACT_LABELS, index=2)

history, source = load_history(config["ticker"], prices[0], period)
spot = float(history["price"].dropna().iloc[-1])
curve = build_futures_curve(CONTRACT_LABELS, prices, datetime.today())
curve = add_convenience_yield(add_curve_metrics(curve), spot, risk_free_rate, storage_cost)
curve_type = classify_curve(curve)
curve_score = curve_tightness_score(curve)

hedge_price = float(curve.loc[curve["contract"] == hedge_contract, "futures_price"].iloc[0])
h_summary = hedge_summary(exposure, hedge_price, config["contract_size"], hedge_ratio)
h_scenarios = hedge_scenarios(exposure, hedge_price, config["contract_size"], int(h_summary["rounded_contracts"]))
position_notional = exposure * spot
var95 = historical_var(history["daily_return"], position_notional, 0.95)
vol = realized_volatility(history["daily_return"])
stress = stress_test(exposure, spot)
scenarios = scenario_library(commodity, exposure, spot)
pnl_attr = pnl_attribution(exposure, spot, curve, hedge_contract, config["contract_size"], int(h_summary["rounded_contracts"]))
ml_result = train_direction_model(history)
anomalies = anomaly_detection(history)

# Desk overview cards
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Latest price", f"{spot:,.2f}", config["currency"])
c2.metric("Curve regime", curve_type)
c3.metric("Prompt spread M1-M3", f"{curve_score['prompt_spread']:,.2f}")
c4.metric("Realized vol", f"{vol:.1%}")
c5.metric("1d VaR 95%", money(var95))

st.markdown(
    f"""
    <div class="section-note">
    <b>Commodity context:</b> {config['benchmark']} — {config['exchange']}.<br>
    <b>Curve read:</b> {config['curve_read']}<br>
    <span class="small-muted">Data source: {source}. Public data is used for demo purposes; desk implementation should connect to Bloomberg, Refinitiv, ICE/CME or internal market-data systems.</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

tabs = st.tabs([
    "Desk overview",
    "Curve & carry",
    "Physical hedge",
    "Risk & P&L",
    "Commodity scenarios",
    "Brent/WTI spread",
    "Options Greeks",
    "ML monitoring",
    "SQL & export",
    "Interview pitch",
])

with tabs[0]:
    left, right = st.columns([1.25, 1])
    with left:
        show_chart(line_chart(history, "date", "price", f"{commodity} historical front-month proxy"))
    with right:
        st.subheader("Market drivers to discuss")
        for driver in config["typical_drivers"]:
            st.markdown(f"- {driver}")
        st.metric("Curve tightness score", f"{curve_score['tightness_score']:.2f}", curve_score["tightness_label"])
        st.metric("Annualized M1-M12 carry", pct(curve_score["annualized_carry"]))
    st.dataframe(history.tail(12), use_container_width=True)

with tabs[1]:
    st.subheader("Futures curve, roll yield and implied convenience yield")
    left, right = st.columns([1.15, 1])
    with left:
        show_chart(curve_chart(curve, f"{commodity} futures curve"))
    with right:
        clean_curve = curve.copy()
        clean_curve["curve_slope_vs_M1"] = clean_curve["curve_slope_vs_M1"].map(lambda x: f"{x:.2%}")
        clean_curve["roll_yield_to_next"] = clean_curve["roll_yield_to_next"].map(lambda x: "" if pd.isna(x) else f"{x:.2%}")
        clean_curve["implied_convenience_yield"] = clean_curve["implied_convenience_yield"].map(lambda x: f"{x:.2%}")
        st.dataframe(clean_curve, use_container_width=True)
    st.latex(r"F = S \times e^{(r + u - y)T}")
    st.latex(r"y = r + u - \frac{\ln(F/S)}{T}")
    st.markdown("The convenience yield converts the curve into a commodity-specific scarcity indicator. High implied convenience yield often points to value in holding physical inventory or having prompt access to supply.")

with tabs[2]:
    st.subheader("Physical exposure hedge simulator")
    h1, h2, h3 = st.columns(3)
    h1.metric("Physical exposure", f"{exposure:,.0f} {config['unit']}")
    h2.metric("Contracts needed", f"{h_summary['contracts_needed']:,.2f}")
    h3.metric("Rounded futures", f"{h_summary['rounded_contracts']:,.0f}")
    st.dataframe(pd.DataFrame([h_summary]), use_container_width=True)
    st.dataframe(h_scenarios, use_container_width=True)
    show_chart(bar_chart(h_scenarios, "price_shock", "hedged_cost_change_usd", "Hedged cost change by price shock"))
    st.markdown("A long futures hedge is useful for a future buyer of the commodity; it offsets rising physical purchase costs. For a producer/seller, the hedge direction would be reversed.")

with tabs[3]:
    st.subheader("Risk analytics and desk-style P&L attribution")
    r1, r2 = st.columns([1, 1.2])
    with r1:
        st.metric("Position notional", money(position_notional))
        st.metric("Historical VaR 95%", money(var95))
        st.metric("Annualized realized volatility", f"{vol:.1%}")
        st.dataframe(stress, use_container_width=True)
    with r2:
        show_chart(bar_chart(pnl_attr, "component", "pnl_usd", "Stylized one-day P&L attribution"))
        st.dataframe(pnl_attr, use_container_width=True)
    st.markdown("VaR gives a statistical loss threshold; stress tests and attribution explain the economic source of risk. This is closer to how desk tools are discussed in trading environments.")

with tabs[4]:
    st.subheader("Commodity-specific scenario library")
    st.dataframe(scenarios, use_container_width=True)
    show_chart(bar_chart(scenarios, "scenario", "pnl_usd", f"{commodity} scenario P&L impact"))
    st.markdown("These scenarios make the project more commodities-oriented because they connect price shocks to physical-market narratives: inventory, weather, OPEC, logistics, mining disruption, rates or safe-haven demand.")

with tabs[5]:
    st.subheader("Brent/WTI spread monitoring")
    brent, _ = load_history("BZ=F", 82.0, period)
    wti, _ = load_history("CL=F", 78.0, period)
    spread = spread_analysis(brent, wti)
    if spread.empty:
        st.warning("Not enough observations for spread z-score.")
    else:
        latest = spread.iloc[-1]
        s1, s2, s3 = st.columns(3)
        s1.metric("Latest Brent-WTI", f"{latest['spread']:.2f}")
        s2.metric("Z-score", f"{latest['z_score']:.2f}")
        s3.metric("Signal", "Extreme" if abs(float(latest["z_score"])) > 2 else "Normal")
        if PLOTLY_AVAILABLE:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=spread["date"], y=spread["spread"], mode="lines", name="Brent - WTI"))
            fig.add_trace(go.Scatter(x=spread["date"], y=spread["spread_mean"], mode="lines", name="Rolling mean"))
            fig.update_layout(title="Brent/WTI spread", height=430, margin=dict(l=20, r=20, t=55, b=20), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            show_chart(line_chart(spread, "date", "spread", "Brent/WTI spread"))
        st.info(zscore_signal(float(latest["z_score"])))
        st.markdown("Brent/WTI is a classic relative-value monitor. It captures regional logistics, crude quality, Cushing constraints, export economics and seaborne-versus-inland market dynamics.")

with tabs[6]:
    st.subheader("Black-76 commodity options pricer and Greeks")
    col1, col2, col3 = st.columns(3)
    F = col1.number_input("Futures price F", min_value=0.01, value=float(hedge_price), step=0.10)
    K = col2.number_input("Strike K", min_value=0.01, value=float(hedge_price), step=0.10)
    sigma = col3.number_input("Implied volatility", min_value=0.01, max_value=2.0, value=max(vol, 0.20), step=0.01)
    col4, col5, col6 = st.columns(3)
    T = col4.number_input("Maturity T in years", min_value=0.01, max_value=5.0, value=0.25, step=0.01)
    option_type = col5.selectbox("Option type", ["call", "put"])
    r = col6.number_input("Rate r", min_value=0.0, max_value=0.20, value=float(risk_free_rate), step=0.005)
    greeks = black76_greeks(F, K, r, sigma, T, option_type)
    st.dataframe(pd.DataFrame([greeks]), use_container_width=True)
    st.markdown("Black-76 is used for options on futures. Delta, gamma, vega and theta let a desk monitor direction, convexity, volatility sensitivity and time decay.")

with tabs[7]:
    st.subheader("Machine-learning monitoring layer")
    if ml_result.get("available"):
        m1, m2, m3 = st.columns(3)
        m1.metric("Out-of-sample accuracy", f"{ml_result['accuracy']:.1%}")
        m2.metric("Next-day up probability", f"{ml_result['latest_proba_up']:.1%}")
        bias = "Bullish monitoring bias" if ml_result["latest_proba_up"] > 0.55 else "Bearish monitoring bias" if ml_result["latest_proba_up"] < 0.45 else "Neutral"
        m3.metric("ML regime", bias)
    else:
        st.warning(ml_result.get("message", "ML unavailable"))
    st.dataframe(anomalies.tail(25), use_container_width=True)
    st.markdown("This is deliberately framed as monitoring, not autonomous trading. In an interview, that is more credible and risk-aware.")

with tabs[8]:
    st.subheader("SQL storage and Excel report")
    if st.button("Save latest desk outputs to SQLite"):
        save_dataframe(history, "price_history")
        save_dataframe(curve, "futures_curve")
        save_dataframe(h_scenarios, "hedge_scenarios")
        save_dataframe(stress, "stress_tests")
        save_dataframe(scenarios, "commodity_scenarios")
        save_dataframe(pnl_attr, "pnl_attribution")
        st.success(f"Saved to SQLite database: {DB_PATH}")
    export = excel_bytes({
        "price_history": history,
        "futures_curve": curve,
        "hedge_summary": pd.DataFrame([h_summary]),
        "hedge_scenarios": h_scenarios,
        "stress_tests": stress,
        "commodity_scenarios": scenarios,
        "pnl_attribution": pnl_attr,
        "ml_anomalies": anomalies.tail(250),
    })
    st.download_button("Download Excel desk report", export, "commodity_trading_desk_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tabs[9]:
    st.subheader("How to pitch it in an Assistant Trader Commodities interview")
    st.markdown(
        """
        **One-liner**  
        I built a Python-based commodity trading desk dashboard focused on market monitoring, futures curve analytics, physical hedging and risk management.

        **What I would explain technically**  
        - I use public continuous futures data for historical monitoring and a configurable curve input for term-structure marks.  
        - I classify contango/backwardation, compute roll yield and infer convenience yield using the cost-of-carry framework.  
        - I simulate physical exposure hedging with futures and show the residual P&L under price shocks.  
        - I monitor VaR, stress tests, desk-style P&L attribution, Brent/WTI spread z-scores and Black-76 option Greeks.  
        - I added a machine-learning layer only as a monitoring tool, not as an automatic trading system.  

        **Professional limitation to state**  
        The current version uses public data for demonstration. In a trading desk environment, I would replace the data layer with Bloomberg, Refinitiv, ICE/CME or internal marks, then add controls for data quality and official end-of-day reporting.
        """
    )

from __future__ import annotations

from datetime import datetime
import numpy as np
import pandas as pd

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


def fetch_yfinance_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    if not YFINANCE_AVAILABLE:
        raise ImportError("yfinance is not installed")
    data = yf.download(ticker, period=period, auto_adjust=False, progress=False)
    if data.empty:
        raise ValueError(f"No yfinance data returned for {ticker}")
    history = data.reset_index()
    if isinstance(history.columns, pd.MultiIndex):
        history.columns = [c[0] for c in history.columns]
    history = history.rename(columns={"Date": "date", "Close": "price"})
    history = history[["date", "price"]].dropna()
    history["daily_return"] = history["price"].pct_change()
    return history


def synthetic_history(initial_price: float, annual_vol: float = 0.35, trading_days: int = 252, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    daily_vol = annual_vol / np.sqrt(252)
    returns = rng.normal(0, daily_vol, trading_days)
    prices = [initial_price]
    for r in returns:
        prices.append(prices[-1] * (1 + r))
    dates = pd.bdate_range(end=datetime.today(), periods=trading_days + 1)
    df = pd.DataFrame({"date": dates, "price": prices})
    df["daily_return"] = df["price"].pct_change()
    return df


def load_history(ticker: str, fallback_price: float, period: str = "1y") -> tuple[pd.DataFrame, str]:
    try:
        return fetch_yfinance_history(ticker, period), "Real yfinance data"
    except Exception as exc:
        return synthetic_history(fallback_price), f"Synthetic fallback data: {exc}"

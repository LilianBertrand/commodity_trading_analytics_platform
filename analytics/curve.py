from __future__ import annotations

from datetime import datetime, timedelta
import numpy as np
import pandas as pd


def build_futures_curve(labels: list[str], prices: list[float], valuation_date: datetime) -> pd.DataFrame:
    offsets = [30, 60, 90, 180, 365][: len(labels)]
    df = pd.DataFrame({
        "contract": labels,
        "maturity_date": [valuation_date + timedelta(days=d) for d in offsets],
        "futures_price": prices,
    })
    df["days_to_maturity"] = (df["maturity_date"] - valuation_date).dt.days
    df["T"] = df["days_to_maturity"] / 365
    return df


def classify_curve(curve: pd.DataFrame) -> str:
    prices = curve["futures_price"].to_numpy()
    if np.all(np.diff(prices) > 0):
        return "Contango"
    if np.all(np.diff(prices) < 0):
        return "Backwardation"
    return "Mixed curve"


def add_curve_metrics(curve: pd.DataFrame) -> pd.DataFrame:
    out = curve.copy()
    out["curve_slope_vs_M1"] = out["futures_price"] / out["futures_price"].iloc[0] - 1
    out["roll_yield_to_next"] = out["futures_price"].shift(-1) / out["futures_price"] - 1
    return out


def add_convenience_yield(curve: pd.DataFrame, spot_price: float, risk_free_rate: float, storage_cost: float) -> pd.DataFrame:
    out = curve.copy()
    out["implied_convenience_yield"] = risk_free_rate + storage_cost - np.log(out["futures_price"] / spot_price) / out["T"]
    return out

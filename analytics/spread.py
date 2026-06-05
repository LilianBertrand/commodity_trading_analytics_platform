from __future__ import annotations

import pandas as pd


def spread_analysis(brent_history: pd.DataFrame, wti_history: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    brent = brent_history[["date", "price"]].rename(columns={"price": "brent_price"})
    wti = wti_history[["date", "price"]].rename(columns={"price": "wti_price"})
    df = pd.merge(brent, wti, on="date", how="inner")
    df["spread"] = df["brent_price"] - df["wti_price"]
    df["spread_mean"] = df["spread"].rolling(window).mean()
    df["spread_std"] = df["spread"].rolling(window).std()
    df["z_score"] = (df["spread"] - df["spread_mean"]) / df["spread_std"]
    return df.dropna()


def zscore_signal(z: float) -> str:
    if z > 2:
        return "Spread unusually high: investigate relative-value mean reversion or fundamental dislocation."
    if z < -2:
        return "Spread unusually low: investigate relative-value mean reversion or fundamental dislocation."
    return "Spread within normal range."

from __future__ import annotations

import numpy as np
import pandas as pd


def historical_var(returns: pd.Series, position_notional: float, confidence_level: float = 0.95) -> float:
    clean = returns.dropna()
    if clean.empty:
        return 0.0
    var_return = np.percentile(clean, (1 - confidence_level) * 100)
    return float(-position_notional * var_return)


def stress_test(position_units: float, reference_price: float) -> pd.DataFrame:
    shocks = [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]
    return pd.DataFrame({
        "stress_scenario": [f"{s:.0%}" for s in shocks],
        "new_price": [reference_price * (1 + s) for s in shocks],
        "pnl_usd": [position_units * (reference_price * (1 + s) - reference_price) for s in shocks],
    })


def realized_volatility(returns: pd.Series) -> float:
    return float(returns.dropna().std() * np.sqrt(252))

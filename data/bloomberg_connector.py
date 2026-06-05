"""
Optional Bloomberg connector.
This module is intentionally safe: it does not break the project if Bloomberg is unavailable.
Real usage requires Bloomberg Terminal, active entitlements, and blpapi installed.
"""
from __future__ import annotations

import pandas as pd


def fetch_bloomberg_history(ticker: str, field: str = "PX_LAST", start_date: str = "2025-01-01", end_date: str | None = None) -> pd.DataFrame:
    try:
        import blpapi  # noqa: F401
    except ImportError as exc:
        raise ImportError("Bloomberg blpapi is not installed. Install it only on a Bloomberg-enabled machine.") from exc
    raise NotImplementedError(
        "Bloomberg connection template prepared. Implement session/service request according to your Bloomberg setup."
    )

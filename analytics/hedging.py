from __future__ import annotations

import pandas as pd


def hedge_summary(exposure_units: float, hedge_price: float, contract_size: int, hedge_ratio: float) -> dict:
    contracts_needed = exposure_units * hedge_ratio / contract_size
    return {
        "exposure_units": exposure_units,
        "hedge_price": hedge_price,
        "notional_exposure_usd": exposure_units * hedge_price,
        "contract_size": contract_size,
        "hedge_ratio": hedge_ratio,
        "contracts_needed": contracts_needed,
        "rounded_contracts": round(contracts_needed),
    }


def hedge_scenarios(exposure_units: float, futures_entry_price: float, contract_size: int, contracts: int) -> pd.DataFrame:
    shocks = [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]
    rows = []
    for shock in shocks:
        new_price = futures_entry_price * (1 + shock)
        unhedged_cost_change = exposure_units * (new_price - futures_entry_price)
        futures_pnl = contracts * contract_size * (new_price - futures_entry_price)
        rows.append({
            "price_shock": shock,
            "new_price": new_price,
            "unhedged_cost_change_usd": unhedged_cost_change,
            "futures_pnl_usd": futures_pnl,
            "hedged_cost_change_usd": unhedged_cost_change - futures_pnl,
        })
    return pd.DataFrame(rows)

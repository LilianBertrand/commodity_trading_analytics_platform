COMMODITY_CONFIG = {
    "Brent Crude Oil": {
        "ticker": "BZ=F",
        "benchmark": "Global seaborne crude benchmark",
        "exchange": "ICE Brent / public continuous proxy",
        "contract_size": 1000,
        "unit": "barrels",
        "currency": "USD/bbl",
        "fallback_curve": [82.10, 81.70, 81.20, 79.90, 77.50],
        "typical_drivers": [
            "OPEC+ supply policy",
            "global refining demand",
            "geopolitical risk premium",
            "freight and seaborne flows",
            "inventory tightness"
        ],
        "curve_read": "Backwardation often signals prompt-market tightness; contango can reflect weaker prompt demand, storage economics, or oversupply."
    },
    "WTI Crude Oil": {
        "ticker": "CL=F",
        "benchmark": "US crude benchmark linked to Cushing logistics",
        "exchange": "NYMEX WTI / public continuous proxy",
        "contract_size": 1000,
        "unit": "barrels",
        "currency": "USD/bbl",
        "fallback_curve": [78.40, 78.05, 77.60, 76.20, 74.10],
        "typical_drivers": [
            "US crude inventories",
            "Cushing storage constraints",
            "shale production",
            "US refinery runs",
            "pipeline and export capacity"
        ],
        "curve_read": "WTI curve shape is highly sensitive to Cushing inventory, US logistics and refinery maintenance seasons."
    },
    "Natural Gas": {
        "ticker": "NG=F",
        "benchmark": "US Henry Hub natural gas benchmark",
        "exchange": "NYMEX Henry Hub / public continuous proxy",
        "contract_size": 10000,
        "unit": "MMBtu",
        "currency": "USD/MMBtu",
        "fallback_curve": [3.10, 3.22, 3.35, 3.85, 4.20],
        "typical_drivers": [
            "weather and heating/cooling demand",
            "storage injections/withdrawals",
            "LNG exports",
            "associated gas production",
            "seasonality"
        ],
        "curve_read": "Gas curves are strongly seasonal; winter contracts can command premiums due to weather and storage risk."
    },
    "Copper": {
        "ticker": "HG=F",
        "benchmark": "Industrial metal linked to global activity",
        "exchange": "COMEX Copper / public continuous proxy",
        "contract_size": 25000,
        "unit": "pounds",
        "currency": "USD/lb",
        "fallback_curve": [4.35, 4.38, 4.41, 4.50, 4.62],
        "typical_drivers": [
            "China industrial demand",
            "manufacturing cycle",
            "mine disruptions",
            "USD strength",
            "energy transition demand"
        ],
        "curve_read": "Copper curve moves often reflect macro growth expectations, inventory availability and mine/refining bottlenecks."
    },
    "Gold": {
        "ticker": "GC=F",
        "benchmark": "Precious metal and macro safe-haven asset",
        "exchange": "COMEX Gold / public continuous proxy",
        "contract_size": 100,
        "unit": "troy ounces",
        "currency": "USD/oz",
        "fallback_curve": [2350, 2358, 2365, 2388, 2430],
        "typical_drivers": [
            "real interest rates",
            "USD strength",
            "central bank buying",
            "safe-haven demand",
            "inflation expectations"
        ],
        "curve_read": "Gold is less about physical scarcity than rates, carry, USD and macro risk premia."
    }
}

CONTRACT_LABELS = ["M1", "M2", "M3", "M6", "M12"]

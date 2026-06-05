# Commodity Trading Desk Dashboard

Professional Python/Streamlit project designed for Assistant Trader Commodities, Trading Analyst, Market Risk or Commodity Structuring interviews.

## What this project demonstrates

This project is not positioned as an automatic trading bot. It is a desk-style analytics platform used to monitor commodity markets, understand futures curve structure, simulate physical hedges and quantify risk.

## Core features

- Real market data through `yfinance` with synthetic fallback
- Commodity-specific configuration for Brent, WTI, Natural Gas, Copper and Gold
- Futures curve analytics:
  - contango / backwardation classification
  - M1-M3 prompt spread
  - M1-M12 annualized carry
  - roll yield
  - implied convenience yield through cost-of-carry
- Commodity-market driver panel:
  - OPEC+, inventories, weather, LNG, Cushing, China demand, real rates, etc.
- Physical exposure hedge simulator:
  - notional exposure
  - contract sizing
  - hedged vs unhedged scenario P&L
- Risk module:
  - historical VaR
  - realized volatility
  - stress tests
  - desk-style P&L attribution
- Commodity-specific scenario library:
  - supply disruption
  - inventory build/draw
  - cold snap / warm winter
  - OPEC+ surprise cut
  - China stimulus
  - real-rate shock
- Brent/WTI spread monitor with rolling z-score
- Black-76 options pricer and Greeks
- Machine-learning monitoring layer:
  - next-day direction probability
  - anomaly detection
- SQLite storage
- Excel report export
- Optional Bloomberg connector template

## Installation

Mac/Linux:

```bash
cd commodity_trading_analytics_platform
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bash
cd commodity_trading_analytics_platform
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Live Demo

https://commoditytradinganalyticsplatform-gy5qqdasyqdp5ekyfiauhd.streamlit.app/


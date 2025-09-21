Vega Native Chart — Lightweight Charts
=====================================

Files
-----
- src/services/datafeed.py — gets OHLCV via yfinance if available; otherwise reads CSV at data/ohlc/<SYMBOL>_<INTERVAL>.csv and computes indicators (Heikin-Ashi, EMA 9/21/50/200, Bollinger(20,2), Ichimoku(9/26/52), MACD, RSI, OBV, ATR).
- src/components/native_chart.py — renders multi-pane Lightweight Charts via `streamlit-lightweight-charts`.
- src/pages/06_Vega_Native_Chart.py — Streamlit page to drive the chart.
- data/ohlc/NASDAQ_QQQ_D.csv — sample so the page renders even without internet.
- requirements.txt — add to your project if needed.

Quick Install
-------------
1) Copy `src/` and `data/` into your repo root (merge folders).
2) Ensure `requirements.txt` includes the new deps (streamlit-lightweight-charts, yfinance).
3) Commit & push — your Render deploy should pick it up.
4) In the sidebar, open **Vega Native Chart — Lightweight Charts** and choose a symbol like `NASDAQ:QQQ`.

"""
Macro/Micro Dashboard Module
---------------------------

Displays real‑time macroeconomic and microeconomic metrics using data from
`yfinance`.  The dashboard includes major indices, commodities, bond yields and
a small set of watchlist stocks to illustrate individual stock performance.
"""

import yfinance as yf
import pandas as pd
import streamlit as st


MACRO_TICKERS = {
    "S&P 500": "^GSPC",
    "VIX": "^VIX",
    "Crude Oil": "CL=F",
    "Gold": "GC=F",
    "10Y Yield": "^TNX",
    "30Y Yield": "^TYX"
}

MICRO_TICKERS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Tesla": "TSLA",
    "Amazon": "AMZN"
}


def fetch_prices(tickers: dict) -> pd.DataFrame:
    rows = []
    for name, ticker in tickers.items():
        try:
            data = yf.download(ticker, period="5d", interval="1d")
            if data.empty:
                continue
            close_yesterday = data["Close"].iloc[-2]
            close_last = data["Close"].iloc[-1]
            change = close_last - close_yesterday
            pct_change = (change / close_yesterday) * 100
            rows.append({
                "Name": name,
                "Ticker": ticker,
                "Last": round(close_last, 2),
                "Change": round(change, 2),
                "%Change": round(pct_change, 2)
            })
        except Exception:
            rows.append({
                "Name": name,
                "Ticker": ticker,
                "Last": None,
                "Change": None,
                "%Change": None
            })
    return pd.DataFrame(rows)


def render() -> None:
    st.subheader("📈 Macro/Micro Dashboard")
    st.write("Real‑time macroeconomic and microeconomic market data.")
    macro_df = fetch_prices(MACRO_TICKERS)
    micro_df = fetch_prices(MICRO_TICKERS)
    st.markdown("### Macro Indicators")
    st.table(macro_df)
    st.markdown("### Micro Watchlist")
    st.table(micro_df)
    st.table(micro_df)

# 🧠
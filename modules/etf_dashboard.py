"""
ETF Dashboard Module
-------------------

Track swing‑to‑investing ETFs across the Asia‑Pacific region.  The module
displays the latest prices and percentage changes for ETFs representing Japan,
Korea, Australia and Hong Kong.  Users can select an ETF to view a line
chart of its recent performance.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


REGIONS = {
    "Japan": ["EWJ", "DXJ", "JOF"],
    "Korea": ["EWY", "FLKR"],
    "Australia": ["EWA", "KROO"],
    "Hong Kong": ["EWH", "FLHK"],
}


def fetch_etf_data(tickers: list) -> pd.DataFrame:
    rows = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="5d", interval="1d")
            if data.empty:
                continue
            close_yesterday = data["Close"].iloc[-2]
            close_last = data["Close"].iloc[-1]
            change = close_last - close_yesterday
            pct_change = (change / close_yesterday) * 100
            rows.append({
                "Ticker": ticker,
                "Last": round(close_last, 2),
                "Change": round(change, 2),
                "%Change": round(pct_change, 2)
            })
        except Exception:
            rows.append({
                "Ticker": ticker,
                "Last": None,
                "Change": None,
                "%Change": None
            })
    return pd.DataFrame(rows)


def render() -> None:
    st.subheader("🌏 ETF Dashboard (APAC)")
    st.write("Monitor regional ETFs across Japan, Korea, Australia and Hong Kong.")
    for region, tickers in REGIONS.items():
        df = fetch_etf_data(tickers)
        st.markdown(f"### {region}")
        st.table(df)
    # Chart selection
    all_tickers = [t for tickers in REGIONS.values() for t in tickers]
    selected = st.selectbox("Select an ETF to chart", all_tickers)
    if selected:
        data = yf.download(selected, period="1y", interval="1d")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode='lines', name=selected))
        fig.update_layout(title=f"{selected} – 1 Year Price", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(fig, use_container_width=True)
# force

# 🧠
"""
BoJ Rate Hike Playbook Module
-----------------------------

Track Japanese FX pairs and sector ETFs to prepare for potential Bank of Japan
rate hikes.  The module highlights large moves in USD/JPY, EUR/JPY and GBP/JPY
and provides a simple overview of Japanese equity ETFs.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


FX_PAIRS = {
    "USD/JPY": "JPY=X",  # Yahoo Finance uses JPY=X for USD/JPY cross rate
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
}

JP_ETFS = ["EWJ", "DXJ", "JOF"]


def fetch_fx_data() -> pd.DataFrame:
    rows = []
    for name, ticker in FX_PAIRS.items():
        try:
            data = yf.download(ticker, period="5d", interval="1d")
            if data.empty:
                continue
            close_yesterday = data["Close"].iloc[-2]
            close_last = data["Close"].iloc[-1]
            change = close_last - close_yesterday
            pct_change = (change / close_yesterday) * 100
            rows.append({
                "Pair": name,
                "Last": round(close_last, 4),
                "Change": round(change, 4),
                "%Change": round(pct_change, 2)
            })
        except Exception:
            rows.append({
                "Pair": name,
                "Last": None,
                "Change": None,
                "%Change": None
            })
    return pd.DataFrame(rows)


def render() -> None:
    st.subheader("🇯🇵 BoJ Rate Hike Playbook")
    st.write("Monitor JPY FX pairs and Japanese ETFs for potential BoJ rate hikes.")
    fx_df = fetch_fx_data()
    st.markdown("### FX Pairs")
    st.table(fx_df)
    st.markdown("### Japanese Sector ETFs")
    etf_df = pd.DataFrame({"Ticker": JP_ETFS})
    st.table(etf_df)
    # Chart selection for FX
    selected_pair = st.selectbox("Select FX pair to chart", list(FX_PAIRS.keys()))
    if selected_pair:
        ticker = FX_PAIRS[selected_pair]
        data = yf.download(ticker, period="1y", interval="1d")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode='lines', name=selected_pair))
        fig.update_layout(title=f"{selected_pair} – 1 Year Performance", xaxis_title="Date", yaxis_title="Exchange Rate")
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(fig, use_container_width=True)
# force

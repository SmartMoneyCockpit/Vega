"""
SPY and Contra ETF Tracker Module
---------------------------------

Monitor the performance of SPY and select inverse ETFs (SPXU, SQQQ, RWM).  The
module displays the latest prices and percentage changes and provides a 1‑year
chart for the selected instrument.  It also computes relative performance
versus SPY over the past year.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


ETFS = {
    "SPY": "SPY",
    "SPXU (3x Short S&P 500)": "SPXU",
    "SQQQ (3x Short NASDAQ 100)": "SQQQ",
    "RWM (Short Russell 2000)": "RWM"
}


def fetch_prices() -> pd.DataFrame:
    rows = []
    for name, ticker in ETFS.items():
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


def relative_performance(etf: str) -> float:
    """Compute relative performance of an ETF against SPY over the past year."""
    try:
        spy = yf.download("SPY", period="1y", interval="1d")["Adj Close"]
        other = yf.download(etf, period="1y", interval="1d")["Adj Close"]
        if spy.empty or other.empty:
            return 0.0
        spy_return = spy.iloc[-1] / spy.iloc[0] - 1
        other_return = other.iloc[-1] / other.iloc[0] - 1
        return round(other_return - spy_return, 4)
    except Exception:
        return 0.0


def render() -> None:
    st.subheader("📊 SPY & Contra ETF Tracker")
    st.write("Track SPY and inverse ETFs.")
    price_df = fetch_prices()
    st.table(price_df)
    selected = st.selectbox("Select ETF to view chart", list(ETFS.keys()))
    if selected:
        ticker = ETFS[selected]
        data = yf.download(ticker, period="1y", interval="1d")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode='lines', name=ticker))
        fig.update_layout(title=f"{selected} – 1 Year Price", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)
        if selected != "SPY":
            rp = relative_performance(ticker)
            st.info(f"Relative performance vs SPY over past year: {rp*100:.2f}%")
            st.info(f"Relative performance vs SPY over past year: {rp*100:.2f}%")

# 🧠
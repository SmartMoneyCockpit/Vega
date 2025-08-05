"""
Bear Mode / Tail‑Risk Watchlist Module
-------------------------------------

Monitor risk‑off assets and notify the user when thresholds are breached.  The
module tracks instruments such as VIX, Gold (GLD), Long‑term Treasuries (TLT)
and High Yield Corporate Bonds (HYG).  Users can set custom alert thresholds
for each asset's percentage change.
"""

import yfinance as yf
import streamlit as st


WATCHLIST = {
    "VIX": "^VIX",
    "Gold ETF (GLD)": "GLD",
    "US 20+Y Treasury (TLT)": "TLT",
    "High Yield Bond (HYG)": "HYG"
}


def fetch_last_change(ticker: str) -> float:
    try:
        data = yf.download(ticker, period="5d", interval="1d")
        if data.empty:
            return 0.0
        close_yesterday = data["Close"].iloc[-2]
        close_last = data["Close"].iloc[-1]
        change = (close_last - close_yesterday) / close_yesterday * 100
        return round(change, 2)
    except Exception:
        return 0.0


def render() -> None:
    st.subheader("🐻 Bear Mode & Tail‑Risk Watchlist")
    st.write("Monitor risk‑off assets and set alerts on large moves.")
    thresholds = {}
    cols = st.columns(len(WATCHLIST))
    for i, (name, ticker) in enumerate(WATCHLIST.items()):
        with cols[i]:
            thresholds[name] = st.number_input(f"Alert threshold (%) for {name}", value=5.0, step=0.5)
    st.markdown("### Watchlist Status")
    for name, ticker in WATCHLIST.items():
        change_pct = fetch_last_change(ticker)
        alert_triggered = abs(change_pct) >= thresholds[name]
        if alert_triggered:
            st.error(f"{name}: {change_pct}% change – Alert! 📢")
        else:
<<<<<<< HEAD
            st.info(f"{name}: {change_pct}% change – Normal")
=======
            st.info(f"{name}: {change_pct}% change – Normal")
>>>>>>> 1d7947d895ee627f5b66a78bde632d8d795e9410

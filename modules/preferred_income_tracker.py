"""
Preferred Income Basket Tracker Module
------------------------------------

Track preferred share ETFs (ZPR, HPR, CPD) and apply a yield stop logic.  The
module fetches the latest price and dividend yield from `yfinance` and alerts
the user when the yield falls below a user‑defined threshold.
"""

import streamlit as st
import yfinance as yf


PREFERRED_ETFS = {
    "BMO Laddered Preferred Share ETF (ZPR)": "ZPR.TO",
    "Horizons Active Preferred Share ETF (HPR)": "HPR.TO",
    "iShares Canadian Preferred Share ETF (CPD)": "CPD.TO",
}


def fetch_etf_info(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        return {
            "price": info.get("regularMarketPrice"),
            "dividendYield": info.get("dividendYield") * 100 if info.get("dividendYield") else None,
        }
    except Exception:
        return {"price": None, "dividendYield": None}


def render() -> None:
    st.subheader("🏦 Preferred Income Basket Tracker")
    st.write("Monitor preferred share ETFs and apply yield stop logic.")
    threshold = st.number_input("Yield stop threshold (%)", min_value=0.0, max_value=20.0, value=4.0, step=0.1)
    for name, ticker in PREFERRED_ETFS.items():
        info = fetch_etf_info(ticker)
        price = info.get("price")
        yield_pct = info.get("dividendYield")
        if price is None:
            st.warning(f"{name} ({ticker}): Data unavailable")
            continue
        if yield_pct is None:
            st.warning(f"{name} ({ticker}): Dividend yield unavailable")
            continue
        if yield_pct < threshold:
            st.error(f"{name} ({ticker}): Price ${price:.2f}, Yield {yield_pct:.2f}% – Below threshold! ⚠️")
        else:
            st.success(f"{name} ({ticker}): Price ${price:.2f}, Yield {yield_pct:.2f}% – Above threshold")
            st.success(f"{name} ({ticker}): Price ${price:.2f}, Yield {yield_pct:.2f}% – Above threshold")

# 🧠
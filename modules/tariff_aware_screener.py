"""
Tariff‑Aware Canada Stock Screener Module
---------------------------------------

Screen Canadian stocks with tariff grades, USMCA involvement and smart money
scores.  This example uses a small universe of TSX‑listed equities and
generates placeholder grades for demonstration purposes.
"""

import random
import yfinance as yf
import pandas as pd
import streamlit as st


STOCKS = [
    {"Ticker": "RY.TO", "Name": "Royal Bank of Canada", "USMCA": True},
    {"Ticker": "TD.TO", "Name": "Toronto‑Dominion Bank", "USMCA": True},
    {"Ticker": "BNS.TO", "Name": "Bank of Nova Scotia", "USMCA": True},
    {"Ticker": "ENB.TO", "Name": "Enbridge Inc.", "USMCA": False},
    {"Ticker": "CNQ.TO", "Name": "Canadian Natural Resources", "USMCA": False},
    {"Ticker": "SHOP.TO", "Name": "Shopify Inc.", "USMCA": True},
    {"Ticker": "AC.TO", "Name": "Air Canada", "USMCA": True},
]

TARIFF_GRADES = ["A", "B", "C"]
SMART_GRADES = ["Strong", "Neutral", "Weak"]


def fetch_stock_data() -> pd.DataFrame:
    rows = []
    for stock in STOCKS:
        ticker = stock["Ticker"]
        try:
            data = yf.download(ticker, period="5d", interval="1d")
            if not data.empty:
                close_last = data["Close"].iloc[-1]
            else:
                close_last = None
        except Exception:
            close_last = None
        rows.append({
            "Ticker": ticker,
            "Name": stock["Name"],
            "Price": round(close_last, 2) if close_last is not None else None,
            "Tariff Grade": random.choice(TARIFF_GRADES),
            "USMCA": "Yes" if stock["USMCA"] else "No",
            "Smart Money Grade": random.choice(SMART_GRADES),
            "Action Plan": "Watchlist" if random.random() < 0.5 else "Consider Buying"
        })
    return pd.DataFrame(rows)


def render() -> None:
    st.subheader("🇨🇦 Tariff‑Aware Canada Stock Screener")
    st.write("Screen TSX stocks using tariff grades, USMCA involvement and smart money scores.")
    df = fetch_stock_data()
    grade_filter = st.multiselect("Select Tariff Grades", options=TARIFF_GRADES, default=TARIFF_GRADES)
    usmca_filter = st.selectbox("USMCA involvement", options=["All", "Yes", "No"], index=0)
    filtered_df = df[df["Tariff Grade"].isin(grade_filter)]
    if usmca_filter != "All":
        filtered_df = filtered_df[filtered_df["USMCA"] == usmca_filter]
    st.dataframe(filtered_df.reset_index(drop=True))
    st.dataframe(filtered_df.reset_index(drop=True))

# 🧠
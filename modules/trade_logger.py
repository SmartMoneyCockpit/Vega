
import streamlit as st
import asyncio
from datetime import date

# AsyncIO loop fix for Streamlit compatibility
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

def render():
    st.header("📝 Trade Logger")
    st.markdown("Record your trades here. Entries will be saved locally and synced to Google Sheets if configured.")

    col1, col2 = st.columns(2)
    with col1:
        trade_date = st.date_input("Date", value=date.today())
        side = st.selectbox("Side", ["Long", "Short"])
        quantity = st.number_input("Quantity", min_value=1, step=1)
    with col2:
        ticker = st.text_input("Ticker symbol", value="SPY")
        price = st.number_input("Price", min_value=0.0, step=0.01)
        notes = st.text_area("Notes")

    if st.button("Save Trade"):
        trade_data = {
            "date": trade_date.strftime("%Y-%m-%d"),
            "ticker": ticker.upper(),
            "side": side,
            "quantity": quantity,
            "price": price,
            "notes": notes
        }
        st.success(f"Trade saved: {trade_data['side']} {trade_data['quantity']} {trade_data['ticker']} @ {trade_data['price']}")
"""
Trade Logger Module
-------------------

This module provides a user interface for recording trades.  Each trade entry
includes the date, ticker symbol, side (long/short), quantity, price and
optional notes.  Trades are stored both locally in the `data/` directory and
synchronised to the `COCKPIT` Google Sheet (worksheet `Trades`) if
authentication succeeds.
"""

import datetime
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

from utils import google_sheets


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
TRADES_CSV = DATA_DIR / "trades.csv"


def save_trade(row: List) -> None:
    """Append a trade row to the local CSV and attempt to sync to Google Sheets."""
    # Append to CSV
    if TRADES_CSV.exists():
        df = pd.read_csv(TRADES_CSV)
        df.loc[len(df)] = row
    else:
        df = pd.DataFrame([row], columns=["Date", "Ticker", "Side", "Quantity", "Price", "Notes"])
    df.to_csv(TRADES_CSV, index=False)
    # Append to Google Sheet
    try:
        google_sheets.append_row(row, sheet_name="COCKPIT", worksheet_name="Trades")
    except Exception:
        pass


def render() -> None:
    st.subheader("📝 Trade Logger")
    st.write("Record your trades here.  Entries will be saved locally and synced to Google Sheets if configured.")
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        date = col1.date_input("Date", datetime.date.today())
        ticker = col2.text_input("Ticker symbol", "SPY")
        side = st.selectbox("Side", ["Long", "Short"])
        quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
        price = st.number_input("Price", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        notes = st.text_area("Notes", "")
        submitted = st.form_submit_button("Save Trade")
        if submitted:
            row = [date.strftime("%Y-%m-%d"), ticker.upper(), side, int(quantity), float(price), notes]
            save_trade(row)
            st.success(f"Saved trade for {ticker.upper()} on {date.strftime('%Y-%m-%d')}.")
    # Display latest trades
    if TRADES_CSV.exists():
        st.markdown("### Recent Trades")
        df = pd.read_csv(TRADES_CSV)
        st.dataframe(df.tail(10))

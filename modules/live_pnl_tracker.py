"""
Live PnL Tracker Module
----------------------

Displays real‑time profit and loss for open positions.  The module uses the
Interactive Brokers (IBKR) API via `ib_insync` to retrieve positions and
calculates PnL using current prices from `yfinance` as a fallback.  If the
connection to IBKR fails, the module will show an informative message.
"""

import streamlit as st
import pandas as pd

<<<<<<< HEAD
from utils import ibkr
=======
from utils import google_sheets
>>>>>>> 1d7947d895ee627f5b66a78bde632d8d795e9410


def render() -> None:
    st.subheader("💰 Live PnL Tracker")
    st.write("Monitor real‑time profit and loss for your open positions.")
    if st.button("Refresh Positions"):
        st.experimental_rerun()
    ib_instance = ibkr.connect()
    if ib_instance is None:
        st.warning("Unable to connect to IBKR.  Running in offline mode.")
        positions_df = pd.DataFrame()
    else:
        positions_df = ibkr.get_positions(ib_instance)
    if positions_df.empty:
        st.info("No open positions to display.")
        return
    # Fetch current prices for tickers
    tickers = positions_df["symbol"].tolist()
    price_df = ibkr.get_live_prices(tickers)
    merged = positions_df.merge(price_df, left_on="symbol", right_index=True, how="left")
    merged["PnL"] = (merged["price"] - merged["avgCost"]) * merged["position"]
    st.dataframe(merged[["symbol", "position", "avgCost", "price", "PnL"]])

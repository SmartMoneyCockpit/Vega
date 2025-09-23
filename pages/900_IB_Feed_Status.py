# pages/900_IB_Feed_Status.py
import os
import time
import streamlit as st
from pathlib import Path
from ruamel.yaml import YAML

st.set_page_config(page_title="IB Feed Status", layout="wide")
st.title("IBKR Feed Status")

yaml = YAML()
cfg = yaml.load(Path("config.yaml").read_text())

from src.ibkr_bridge import connect_ib, fetch_prices

col1, col2, col3 = st.columns(3)
with col1:
    host = os.getenv("IB_HOST", cfg["ibkr"]["host"])
    st.metric("IB Host", host)
with col2:
    st.metric("IB Port", os.getenv("IB_PORT", str(cfg["ibkr"]["port"])))
with col3:
    st.metric("Client ID", os.getenv("IB_CLIENT_ID", str(cfg["ibkr"]["client_id"])))

st.write("**Market Data Type**: 3 = delayed (free), 1 = live (if subscribed).")
tickers_default = ["AAPL", "SPY", "RY.TO", "ZPR.TO", "HPR.TO", "CPD.TO"]
tickers = st.text_input("Tickers (comma separated)", ", ".join(tickers_default))

if st.button("Test Feed Now"):
    try:
        ib = connect_ib(cfg)
        st.success("Connected to IBKR ✅")
        prices = fetch_prices(ib, [t.strip() for t in tickers.split(",") if t.strip()])
        ib.disconnect()
        st.subheader("Prices (delayed)")
        st.table([{ "Ticker": k, "Price": v } for k, v in prices.items()])
    except Exception as e:
        st.error(f"Feed test failed: {e}")

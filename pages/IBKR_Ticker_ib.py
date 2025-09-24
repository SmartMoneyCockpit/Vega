# pages/IBKR_Ticker_ib.py
import requests, streamlit as st
from config.ib_bridge_client import get_bridge_url, get_bridge_api_key

BRIDGE_URL = get_bridge_url()
API_KEY = get_bridge_api_key()

st.title("IBKR Ticker (ib_insync via Bridge)")

c1, c2 = st.columns([2,1])
with c1:
    symbol = st.text_input("Symbol", "AAPL").strip().upper()
with c2:
    asset = st.selectbox("Asset", ["stock", "fx"], index=0)

snapshot = st.checkbox("Snapshot (fast; 1s wait)", value=True)

if st.button("Get Quote"):
    try:
        r = requests.get(
            f"{BRIDGE_URL}/price/{symbol}",
            params={"asset": asset, "snapshot": str(snapshot).lower()},
            headers={"x-api-key": API_KEY},
            timeout=8,
        )
        if r.ok:
            st.json(r.json())
        else:
            st.error(f"{r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"Error fetching price: {e}")
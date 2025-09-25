import os, streamlit as st
from cockpit_client.ib_bridge_client import IBKRBridgeClient

st.set_page_config(page_title="IBKR Ticker (Bridge)", layout="wide")
st.title("IBKR Ticker (via Bridge)")

base = os.getenv("IBKR_BRIDGE_URL")
key  = os.getenv("BRIDGE_API_KEY") or os.getenv("IB_BRIDGE_API_KEY", "")
client = IBKRBridgeClient(base_url=base, api_key=key)

col1, col2 = st.columns([1,3])
with col1:
    sym = st.text_input("Symbol", "SPY").strip().upper()
with col2:
    if st.button("Fetch last price"):
        try:
            st.json(client.price(sym))
        except Exception as e:
            st.error(str(e))
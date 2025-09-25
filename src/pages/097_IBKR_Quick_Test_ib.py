import os, streamlit as st
from cockpit_client.ib_bridge_client import IBKRBridgeClient

st.set_page_config(page_title="IBKR Quick Test (Bridge)", layout="wide")
st.title("IBKR Quick Test (Bridge)")

base = os.getenv("IBKR_BRIDGE_URL")
key  = os.getenv("BRIDGE_API_KEY") or os.getenv("IB_BRIDGE_API_KEY", "")
client = IBKRBridgeClient(base_url=base, api_key=key)

col1, col2 = st.columns(2)
with col1:
    if st.button("Health"):
        try:
            st.json(client.health())
        except Exception as e:
            st.error(str(e))
with col2:
    sym = st.text_input("Symbol", "SPY")
    if st.button("Price"):
        try:
            st.json(client.price(sym))
        except Exception as e:
            st.error(str(e))
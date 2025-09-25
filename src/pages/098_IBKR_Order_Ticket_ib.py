import os, streamlit as st
from cockpit_client.ib_bridge_client import IBKRBridgeClient

st.set_page_config(page_title="IBKR Order Ticket (Bridge)", layout="wide")
st.title("IBKR Order Ticket (Bridge) — USE CAREFULLY (LIVE)")

base = os.getenv("IBKR_BRIDGE_URL")
key  = os.getenv("BRIDGE_API_KEY") or os.getenv("IB_BRIDGE_API_KEY", "")
client = IBKRBridgeClient(base_url=base, api_key=key)

sym = st.text_input("Symbol", "SPY").strip().upper()
action = st.selectbox("Action", ["BUY","SELL"], index=0)
qty = st.number_input("Quantity", min_value=1, value=1, step=1)

if st.button("Place Market Order"):
    try:
        res = client.market_order(sym, action, qty)
        st.success("Order sent")
        st.json(res)
    except Exception as e:
        st.error(str(e))
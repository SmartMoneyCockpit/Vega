
import os, streamlit as st
from cockpit_client.ib_bridge_client import IBKRBridgeClient

st.set_page_config(page_title="IBKR Bridge Test", layout="centered")
st.title("IBKR Bridge Test")

base = os.getenv("IBKR_BRIDGE_URL", "http://<DROPLET_IP>:8088")
key  = os.getenv("BRIDGE_API_KEY", "VegaTrading2025X")

st.write("**Bridge URL:**", base)
st.write("**API Key:**", "(set)" if key else "(empty)")

client = IBKRBridgeClient(base_url=base, api_key=key)

col1, col2 = st.columns(2)
with col1:
    if st.button("Health"):
        try:
            st.json(client.health())
        except Exception as e:
            st.error(str(e))
with col2:
    symbol = st.text_input("Symbol", "SPY")
    if st.button("Get Price"):
        try:
            st.json(client.price(symbol))
        except Exception as e:
            st.error(str(e))

st.divider()
st.subheader("Market Order (demo)")
sym = st.text_input("Order Symbol", "SPY", key="o_sym")
action = st.selectbox("Action", ["BUY", "SELL"], key="o_action")
qty = st.number_input("Quantity", min_value=1, value=1, step=1, key="o_qty")
if st.button("Place Market Order"):
    try:
        st.json(client.market_order(sym, action, qty))
    except Exception as e:
        st.error(str(e))

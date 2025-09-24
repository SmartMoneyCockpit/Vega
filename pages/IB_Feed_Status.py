# pages/IB_Feed_Status.py
import requests, streamlit as st
from config.ib_bridge_client import get_bridge_url, get_bridge_api_key

BRIDGE_URL = get_bridge_url()
API_KEY = get_bridge_api_key()

st.title("IB Feed Status")

colA, colB = st.columns(2)

with colA:
    st.caption("Public /health (no auth)")
    try:
        r = requests.get(f"{BRIDGE_URL}/health", timeout=4)
        st.success(r.json())
    except Exception as e:
        st.error(f"Could not reach {BRIDGE_URL}/health\n{e}")

with colB:
    st.caption("Authenticated /status (requires x-api-key)")
    try:
        r2 = requests.get(f"{BRIDGE_URL}/status", headers={"x-api-key": API_KEY}, timeout=6)
        st.info(r2.json())
    except Exception as e:
        st.error(f"Could not reach {BRIDGE_URL}/status\n{e}")

st.caption(f"Bridge URL: {BRIDGE_URL} (set IBKR_BRIDGE_URL or IB_BRIDGE_URL).")
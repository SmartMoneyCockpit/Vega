
import streamlit as st, httpx
from config.ib_bridge_client import get_bridge_url, default_headers

st.header("IB Feed Status")
base = get_bridge_url().rstrip("/")

try:
    r = httpx.get(f"{base}/health", headers=default_headers(), timeout=8.0)
    r.raise_for_status()
    data = r.json()
    st.success("Bridge reachable ✅")
    st.json(data)
except httpx.RequestError as e:
    st.error(f"Could not reach IBKR Bridge at {base}/health: {e}")

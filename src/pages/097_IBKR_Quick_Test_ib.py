
import streamlit as st, httpx
from config.ib_bridge_client import get_bridge_url, default_headers

st.header("IBKR Quick Test (Bridge)")

base = get_bridge_url().rstrip("/")
symbol = st.text_input("Symbol", value="SPY")

col1, col2 = st.columns(2)
with col1:
    if st.button("Health"):
        try:
            r = httpx.get(f"{base}/health", headers=default_headers(), timeout=8.0)
            r.raise_for_status()
            st.success("OK")
            st.json(r.json())
        except Exception as e:
            st.error(f"Health failed: {e}")
with col2:
    if st.button("Price"):
        try:
            r = httpx.get(f"{base}/price/{symbol}", headers=default_headers(), timeout=8.0)
            r.raise_for_status()
            st.json(r.json())
        except Exception as e:
            st.error(f"Price failed: {e}")

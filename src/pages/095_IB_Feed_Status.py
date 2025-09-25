import os
import streamlit as st
import httpx
from config.ib_bridge_client import get_bridge_url, get_bridge_api_key

st.set_page_config(page_title="IB Feed Status", layout="wide")
st.title("📡 IB Feed Status")

base = get_bridge_url()
health_url = f"{base}/health"
api_key = get_bridge_api_key()

with st.spinner(f"Checking bridge at {health_url} ..."):
    try:
        r = httpx.get(health_url, timeout=5.0)
        r.raise_for_status()
        data = r.json()
        st.success("Bridge is reachable")
        st.json(data)
    except Exception as e:
        st.error(f"Could not reach IBKR Bridge at {health_url}\n\n{e}")

st.divider()
st.subheader("Quick live test")
col1, col2 = st.columns([1,3])
with col1:
    sym = st.text_input("Symbol", "SPY")
with col2:
    if st.button("Get Price"):
        try:
            headers = {"x-api-key": api_key} if api_key else {}
            r = httpx.get(f"{base}/price/{sym}", headers=headers, timeout=8.0)
            r.raise_for_status()
            st.success("OK")
            st.json(r.json())
        except Exception as e:
            st.error(str(e))
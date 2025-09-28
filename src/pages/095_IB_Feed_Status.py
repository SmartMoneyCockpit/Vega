import streamlit as st
import httpx
from config.ib_bridge_client import get_bridge_url, get_bridge_api_key

st.set_page_config(page_title="IB Feed Status", layout="wide")
st.title("📡 IB Feed Status")

base = get_bridge_url()
health_url = f"{base}/health"
headers = {"x-api-key": get_bridge_api_key()} if get_bridge_api_key() else {}

with st.spinner(f"Checking bridge at {health_url} ..."):
    try:
        r = httpx.get(health_url, headers=headers, timeout=5.0)
        r.raise_for_status()
        st.success(f"✅ Bridge OK: {r.text}")
    except Exception as e:
        st.error(f"❌ Could not reach IBKR Bridge at {health_url}\n{e}")

st.subheader("Quick live test")
sym = st.text_input("Symbol", "SPY").strip().upper()
if st.button("Get Price"):
    try:
        r = httpx.get(f"{base}/price/{sym}", headers=headers, timeout=6.0)
        r.raise_for_status()
        st.json(r.json())
    except Exception as e:
        st.error(str(e))

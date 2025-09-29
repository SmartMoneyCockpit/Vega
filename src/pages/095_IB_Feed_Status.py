import streamlit as st, httpx
import os, pathlib, sys
try:
    from config.ib_bridge_client import get_bridge_url, get_bridge_api_key  # type: ignore
except Exception:
    def get_bridge_url() -> str:
        return (os.getenv("IBKR_BRIDGE_URL") or os.getenv("IB_BRIDGE_URL") or "").rstrip("/")
    def get_bridge_api_key() -> str:
        return os.getenv("IB_BRIDGE_API_KEY") or os.getenv("BRIDGE_API_KEY") or os.getenv("IBKR_BRIDGE_API_KEY") or ""


st.set_page_config(page_title="IB Feed Status", layout="wide")
st.title("📡 IB Feed Status")

base = get_bridge_url()
headers = {"x-api-key": get_bridge_api_key()} if get_bridge_api_key() else {}
health_url = f"{base}/health" if base else ""

if not base:
    st.error("IBKR_BRIDGE_URL is not set in environment.")
else:
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

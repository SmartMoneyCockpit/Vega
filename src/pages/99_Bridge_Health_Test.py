import httpx, streamlit as st
import os, pathlib, sys
try:
    from config.ib_bridge_client import get_bridge_url, get_bridge_api_key  # type: ignore
except Exception:
    def get_bridge_url() -> str:
        return (os.getenv("IBKR_BRIDGE_URL") or os.getenv("IB_BRIDGE_URL") or "").rstrip("/")
    def get_bridge_api_key() -> str:
        return os.getenv("IB_BRIDGE_API_KEY") or os.getenv("BRIDGE_API_KEY") or os.getenv("IBKR_BRIDGE_API_KEY") or ""


st.header("Bridge Health Check")

base = get_bridge_url()
key  = get_bridge_api_key()
headers = {"x-api-key": key} if key else {}
url = f"{base}/health" if base else ""

if not base:
    st.error("IBKR_BRIDGE_URL is not set. Set it in Render env to your VPS bridge, e.g. http://<IP>:8888")
else:
    st.write(f"Testing {url}")
    try:
        r = httpx.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        st.success(f"✅ Bridge reachable: {r.text}")
    except Exception as e:
        st.error(f"❌ Bridge not reachable: {e}")

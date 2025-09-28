import httpx, streamlit as st
from config.ib_bridge_client import get_bridge_url, get_bridge_api_key

st.header("Bridge Health Check")

base    = get_bridge_url()
headers = {"x-api-key": get_bridge_api_key()} if get_bridge_api_key() else {}
url     = f"{base}/health"
st.write(f"Testing {url}")

try:
    r = httpx.get(url, headers=headers, timeout=5)
    r.raise_for_status()
    st.success(f"✅ Bridge reachable: {r.text}")
except Exception as e:
    st.error(f"❌ Bridge not reachable: {e}")

import httpx, streamlit as st
from components.bridge import get_bridge_base, get_bridge_headers

st.header("Bridge Health Check")

base    = get_bridge_base()
headers = get_bridge_headers()
url     = f"{base}/health"
st.write(f"Testing {url}")

try:
    r = httpx.get(url, headers=headers, timeout=5)
    r.raise_for_status()
    st.success(f"✅ Bridge reachable: {r.text}")
except Exception as e:
    st.error(f"❌ Bridge not reachable: {e}")

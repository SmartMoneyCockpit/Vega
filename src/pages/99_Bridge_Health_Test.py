import os, httpx, streamlit as st

scheme = os.getenv("BRIDGE_SCHEME", "http")
host   = os.getenv("BRIDGE_HOST", "127.0.0.1")
port   = os.getenv("BRIDGE_PORT", "8088")

url = f"{scheme}://{host}:{port}/health"
st.header("Bridge Health Check")
st.write(f"Testing {url}")

try:
    r = httpx.get(url, timeout=5)
    r.raise_for_status()
    st.success(f"✅ Bridge reachable: {r.text}")
except Exception as e:
    st.error(f"❌ Bridge not reachable: {e}")

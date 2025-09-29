
import streamlit as st, httpx, json
from config.ib_bridge_client import get_bridge_url, default_headers

st.header("Bridge Health Check")

base = get_bridge_url().rstrip("/")
st.info(f"Testing: {base}/health")

try:
    r = httpx.get(f"{base}/health", headers=default_headers(), timeout=8.0)
    r.raise_for_status()
    st.success(f"Bridge OK ✅: {r.json()}")
except httpx.HTTPStatusError as e:
    st.error(f"Bridge returned {e.response.status_code}: {e.response.text[:500]}")
except httpx.RequestError as e:
    st.error(f"Network error: {e}")

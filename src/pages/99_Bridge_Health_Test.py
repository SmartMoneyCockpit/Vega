
import os, sys, pathlib
HERE = pathlib.Path(__file__).resolve()
CANDIDATES = [
    HERE.parents[2],
    HERE.parents[1],
    pathlib.Path("/opt/render/project/src"),
]
for p in CANDIDATES:
    if str(p) not in sys.path and p.exists():
        sys.path.insert(0, str(p))

from config.ib_bridge_client import get_bridge_url, default_headers

import streamlit as st, httpx
st.header("Bridge Health Check")
base = get_bridge_url().rstrip("/")
st.info(f"Testing: {base}/health")
try:
    r = httpx.get(f"{base}/health", headers=default_headers(), timeout=8.0)
    r.raise_for_status()
    st.success("Bridge OK ✅")
    st.json(r.json())
except httpx.HTTPStatusError as e:
    st.error(f"Bridge returned {e.response.status_code}: {e.response.text[:500]}")
except httpx.RequestError as e:
    st.error(f"Network error: {e}")

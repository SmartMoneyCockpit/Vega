import os
import streamlit as st
import httpx

st.set_page_config(page_title="IB Feed Status", layout="wide")
st.title("📡 IB Feed Status")

host = os.environ.get("BRIDGE_HOST", "127.0.0.1")
port = int(os.environ.get("BRIDGE_PORT", "8088"))
url = f"http://{host}:{port}/health"

with st.spinner(f"Checking bridge at {url} ..."):
    try:
        r = httpx.get(url, timeout=2.0)
        ok = r.status_code == 200 and isinstance(r.json(), dict) and r.json().get("ok") is True
        if ok:
            st.success("IBKR Bridge is running ✅")
        else:
            st.warning(f"Bridge responded but not OK: {r.text}")
    except Exception as e:
        st.error(f"Could not reach IBKR Bridge at {url}\n\n{e}")

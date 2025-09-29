import streamlit as st, httpx
import os
import httpx
def _get_base(): return (os.getenv("IBKR_BRIDGE_URL") or os.getenv("IB_BRIDGE_URL") or "").rstrip("/")
def _get_key():  return os.getenv("IB_BRIDGE_API_KEY") or os.getenv("BRIDGE_API_KEY") or os.getenv("IBKR_BRIDGE_API_KEY") or ""


st.set_page_config(page_title="IBKR Quick Test (Bridge)", layout="wide")
st.title("IBKR Quick Test (Bridge)")

base = _get_base()
headers = {"x-api-key": _get_key()} if _get_key() else {}

col1, col2 = st.columns(2)
with col1:
    if st.button("Health"):
        try:
            r = httpx.get(f"{base}/health", headers=headers, timeout=5.0)
            r.raise_for_status()
            st.success(r.text)
        except Exception as e:
            st.error(str(e))

with col2:
    sym = st.text_input("Symbol", "SPY").strip().upper()
    if st.button("Price"):
        try:
            r = httpx.get(f"{base}/price/{sym}", headers=headers, timeout=6.0)
            r.raise_for_status()
            st.json(r.json())
        except Exception as e:
            st.error(str(e))

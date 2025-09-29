import streamlit as st
import os
import httpx
def _get_base(): return (os.getenv("IBKR_BRIDGE_URL") or os.getenv("IB_BRIDGE_URL") or "").rstrip("/")
def _get_key():  return os.getenv("IB_BRIDGE_API_KEY") or os.getenv("BRIDGE_API_KEY") or os.getenv("IBKR_BRIDGE_API_KEY") or ""


st.set_page_config(page_title="IBKR Ticker (via Bridge)", layout="wide")
st.title("IBKR Ticker (Bridge)")

base = _get_base()
headers = {"x-api-key": _get_key()} if _get_key() else {}
st.caption(f"Bridge: {base}")

col1, col2 = st.columns([1,3])
with col1:
    sym = st.text_input("Symbol", "SPY").strip().upper()
with col2:
    if st.button("Fetch last price"):
        if not base:
            st.error("IBKR_BRIDGE_URL not set")
        else:
            try:
                r = httpx.get(f"{base}/price/{sym}", headers=headers, timeout=6.0)
                r.raise_for_status()
                st.json(r.json())
            except Exception as e:
                st.error(str(e))

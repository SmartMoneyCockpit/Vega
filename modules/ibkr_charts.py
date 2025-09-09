import os, json
import streamlit as st

def render():
    st.header("IBKR Charts (Live if configured, else cached)")
    host = os.getenv("IBKR_HOST","")
    port = os.getenv("IBKR_PORT","")
    client_id = os.getenv("IBKR_CLIENT_ID","")
    if not (host and port and client_id):
        st.warning("IBKR not configured. Set IBKR_HOST / IBKR_PORT / IBKR_CLIENT_ID in Render. Showing placeholder.")
        st.code("Fallback: cached chart images or basic placeholders here.")
    else:
        st.success("IBKR env vars detected — this panel will request live charts in server workflows.")
        st.code("Server-side workflow pulls data from IBKR; UI displays generated snapshots.")

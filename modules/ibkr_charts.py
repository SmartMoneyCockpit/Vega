# modules/ibkr_charts.py
import streamlit as st
from tools.ibkr_client import get_ib, status

def render():
    st.header("IBKR Charts")
    st.caption(f"IBKR status: {status()}")
    ib = get_ib()
    if not ib:
        st.info("IBKR not connected (safe fallback). Start TWS/Gateway and set IB_HOST/IB_PORT/IB_CLIENT_ID if needed.")
        return
    try:
        server_time = ib.reqCurrentTime()
        st.success(f"Connected. IB Server time: {server_time}")
    except Exception as e:
        st.warning(f"Connected but request failed: {e}")
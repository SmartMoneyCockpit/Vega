# pages/93_IBKR_Bridge_Log.py
import streamlit as st

st.set_page_config(page_title="IBKR Bridge Log", layout="wide")
st.title("IBKR Bridge Log Viewer")

levels = st.multiselect("Filter levels", ["INFO","WARNING","ERROR"], default=["INFO","WARNING","ERROR"])

try:
    with open("ibkr_bridge.log","r") as f:
        lines = f.readlines()[-500:]
    for line in lines:
        if any(lvl in line for lvl in levels):
            st.text(line.strip())
except FileNotFoundError:
    st.warning("No log file yet.")

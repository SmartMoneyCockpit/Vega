
# pages/Logs_IBKR.py
import os, re
import streamlit as st

st.set_page_config(page_title="IBKR Logs", layout="wide")
st.title("IBKR Logs (Filtered)")

path = os.path.join(os.getcwd(), "logs", "ibkr.log")
os.makedirs(os.path.dirname(path), exist_ok=True)

st.caption(f"Showing: {path}")
filters = st.multiselect("Filter terms",
                         ["Connecting IB", "Connected to IBKR", "ECONNREFUSED", "Timed out", "clientId in use", "Not allowed"],
                         default=["Connecting IB", "Connected to IBKR"])

if os.path.exists(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()[-1000:]
    if filters:
        rx = re.compile("|".join(re.escape(f) for f in filters))
        lines = [ln for ln in lines if rx.search(ln)]
    st.code("".join(lines) if lines else "(no matching lines)")
else:
    st.info("No log file yet. Ensure your app writes IB messages to logs/ibkr.log")

import os
import streamlit as st
import pandas as pd
from services.ibkr_scanner.ibkr_client_stub import IBKRClient

st.set_page_config(page_title="IBKR Scanner", layout="wide")
st.title("🔎 IBKR Stock Scanner (Stub)")

host = os.getenv("IBKR_HOST", "127.0.0.1")
port = int(os.getenv("IBKR_PORT", "7497"))
client_id = int(os.getenv("IBKR_CLIENT_ID", "111"))

with st.sidebar:
    st.subheader("Connection")
    st.write(f"Host: {host}  •  Port: {port}  •  ClientId: {client_id}")
    if st.button("Test Connect (safe)"):
        ok, msg = IBKRClient(host, port, client_id).connect()
        st.info(f"Result → ok={ok}, msg={msg}")

client = IBKRClient(host, port, client_id)
results = pd.DataFrame(client.scan_example(["AAPL", "MSFT", "SPY"]))
st.subheader("Sample Scan Results")
st.dataframe(results, use_container_width=True)
st.caption("Safe stub: won’t crash without ib_insync or an IB Gateway. Live wiring comes in the next upgrade.")

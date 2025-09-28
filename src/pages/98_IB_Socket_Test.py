import os, socket, streamlit as st
host = os.getenv("IB_HOST", "127.0.0.1")
port = int(os.getenv("IB_PORT", "7496"))
st.header("IBKR Socket Test")
try:
    with socket.create_connection((host, port), timeout=5):
        st.success(f"✅ Connected to IBKR at {host}:{port}")
except Exception as e:
    st.error(f"❌ Could not connect: {e}")

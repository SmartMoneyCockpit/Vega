# pages/090_IB_Feed_Status.py
import os, streamlit as st
from src.ibkr_bridge import connect_ib, fetch_prices

st.set_page_config(page_title="IB Feed Status", layout="wide")
st.title("IBKR Feed Status")

col1, col2, col3 = st.columns(3)
with col1: st.metric("Host", os.getenv("IBKR_HOST") or os.getenv("IB_HOST") or "127.0.0.1")
with col2: st.metric("Port", os.getenv("IBKR_PORT") or os.getenv("IB_PORT") or "4002")
with col3: st.metric("Client ID", os.getenv("IBKR_CLIENT_ID") or os.getenv("IB_CLIENT_ID") or "7")

tickers = st.text_input("Tickers (comma separated)", "AAPL, SPY, RY.TO, ZPR.TO, HPR.TO, CPD.TO")

if st.button("Test Feed Now"):
    try:
        ib = connect_ib()
        st.success("Connected ✅")
        symbols = [t.strip() for t in tickers.split(",") if t.strip()]
        data = fetch_prices(ib, symbols)
        ib.disconnect()
        st.table([{ "Ticker": k, "Price": v } for k,v in data.items()])
    except Exception as e:
        st.error(f"Feed test failed: {e}")

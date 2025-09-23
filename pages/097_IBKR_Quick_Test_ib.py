# pages/097_IBKR_Quick_Test_ib.py
import streamlit as st
from src.ibkr_bridge import connect_ib, get_delayed_last

st.title("IBKR Quick Test (ib_insync)")
symbol = st.text_input("Symbol", "SPY")
if st.button("Get Quote"):
    try:
        ib = connect_ib()
        px = get_delayed_last(ib, symbol.strip())
        ib.disconnect()
        st.success(f"{symbol} = {px}" if px is not None else "No price returned.")
    except Exception as e:
        st.error(f"Error: {e}")

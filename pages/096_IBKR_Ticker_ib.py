# pages/096_IBKR_Ticker_ib.py
import time, streamlit as st
from src.ibkr_bridge import connect_ib, fetch_prices

st.title("IBKR Live Ticker (ib_insync)")
symbols = st.text_input("Symbols (comma separated)", "SPY,AAPL,MSFT")
period = st.slider("Refresh every (seconds)", 2, 30, 5)

placeholder = st.empty()

if st.button("Start"):
    ib = connect_ib()
    try:
        while True:
            data = fetch_prices(ib, [s.strip() for s in symbols.split(",") if s.strip()])
            placeholder.table([{ "Ticker": k, "Price": v } for k,v in data.items()])
            time.sleep(period)
    except Exception as e:
        st.error(f"Ticker stopped: {e}")
    finally:
        ib.disconnect()


# pages/IB_Command_Panel.py
import streamlit as st
from ib_insync import Stock
from components.ib_status import render_ib_panel
from utils.ib_client import connect_with_retry

st.set_page_config(page_title="IB Command Panel", layout="wide")

st.title("IB Command Panel")
render_ib_panel()

if st.toggle("Enable Controls (are you sure?)", value=False):
    ib, cid = connect_with_retry()
    st.caption(f"Connected with clientId={cid}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Get Account Summary"):
            rows = ib.accountSummary()
            st.table([{ "tag": r.tag, "value": r.value, "currency": r.currency } for r in rows])
    with col2:
        sym = st.text_input("Snapshot symbol", "AAPL")
        if st.button("Get Snapshot"):
            c = Stock(sym, "SMART", "USD")
            t = ib.reqMktData(c, snapshot=True)
            ib.sleep(2)
            st.write({ "bid": t.bid, "ask": t.ask, "last": t.last })
    if st.button("Cancel ALL Orders"):
        ib.cancelAllOrders()
        st.success("Cancel all sent.")
    ib.disconnect()

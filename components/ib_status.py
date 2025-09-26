
# components/ib_status.py
import os
import time
import streamlit as st
from ib_insync import IB, Stock

IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", "7496"))
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "1"))

def _connect(timeout_sec: int = 5):
    ib = IB()
    ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID, timeout=timeout_sec)
    return ib

def status_badge(pad: str = "0.25rem 0.6rem", fs: str = "0.9rem"):
    try:
        ib = _connect(3)
        ok = ib.isConnected()
        ib.disconnect()
    except Exception:
        ok = False
    color = "#16a34a" if ok else "#dc2626"
    text  = "IBKR: CONNECTED" if ok else "IBKR: DISCONNECTED"
    st.markdown(f"""
        <span style='background:{color};color:white;border-radius:0.5rem;padding:{pad};font-size:{fs};'>
        {text}
        </span>
    """, unsafe_allow_html=True)

def check_ib_status(timeout_sec: int = 5) -> dict:
    ib = IB()
    try:
        ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID, timeout=timeout_sec)
        status = {"status": "connected" if ib.isConnected() else "disconnected",
                  "host": IB_HOST, "port": IB_PORT, "clientId": IB_CLIENT_ID}
        return status
    except Exception as e:
        return {"status": "error", "message": str(e), "host": IB_HOST, "port": IB_PORT, "clientId": IB_CLIENT_ID}
    finally:
        if ib.isConnected():
            ib.disconnect()

def quick_snapshot(symbol="AAPL", exchange="SMART", currency="USD", wait_sec=2):
    ib = IB()
    try:
        ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID, timeout=5)
        contract = Stock(symbol, exchange, currency)
        ticker = ib.reqMktData(contract, snapshot=True)
        ib.sleep(wait_sec)
        return {"symbol": symbol, "bid": ticker.bid, "ask": ticker.ask, "last": ticker.last}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if ib.isConnected():
            ib.disconnect()

def render_ib_panel():
    st.subheader("IBKR Connection")
    cols = st.columns([1,1,1])
    cols[0].metric("Host", IB_HOST)
    cols[1].metric("Port", IB_PORT)
    cols[2].metric("Client ID", IB_CLIENT_ID)

    refresh = st.button("Check IB Connection", use_container_width=True)
    if refresh:
        with st.spinner("Connecting to IBKR…"):
            status = check_ib_status()
            time.sleep(0.2)

        if status.get("status") == "connected":
            st.success(f"Connected to IBKR ({status['host']}:{status['port']}, clientId={status['clientId']})")
            if st.toggle("Quick snapshot: AAPL", value=False):
                snap = quick_snapshot("AAPL")
                if "error" in snap:
                    st.warning(f"Snapshot error: {snap['error']}")
                else:
                    st.info(f"AAPL → bid: {snap['bid']}  ask: {snap['ask']}  last: {snap['last']}")
        elif status.get("status") == "disconnected":
            st.error("Disconnected from IBKR.")
        else:
            st.error(f"Error: {status.get('message','unknown')}")
    else:
        st.caption("Press the button to test connectivity.")

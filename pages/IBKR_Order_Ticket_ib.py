# pages/IBKR_Order_Ticket_ib.py
import requests, streamlit as st
from config.ib_bridge_client import get_bridge_url, get_bridge_api_key

BRIDGE_URL = get_bridge_url()
API_KEY = get_bridge_api_key()

st.title("IBKR Order Ticket (ib_insync)")

c1, c2, c3 = st.columns([2,1,1])
with c1: symbol = st.text_input("Symbol", "AAPL").strip().upper()
with c2: side   = st.radio("Side", ["buy", "sell"], horizontal=True)
with c3: qty    = st.number_input("Quantity", min_value=1.0, value=1.0, step=1.0)

otype = st.selectbox("Order Type", ["MKT", "LMT", "STP", "STP LMT", "BRACKET"], index=0)
lc, sc, tc = st.columns(3)
with lc: lmt = st.number_input("Limit Price (LMT / STP LMT)", min_value=0.0, step=0.01, value=0.0)
with sc: stp = st.number_input("Stop Price (STP / STP LMT / BRACKET)",  min_value=0.0, step=0.01, value=0.0)
with tc: tgt = st.number_input("Target Price (BRACKET)", min_value=0.0, step=0.01, value=0.0)

if st.button("Place Order"):
    payload = {
        "symbol": symbol,
        "side": side,            # bridge expects 'buy'/'sell'
        "quantity": float(qty),
        "type": otype,           # MKT, LMT, STP, STP LMT, BRACKET
        "limit_price": (float(lmt) if otype in ("LMT", "STP LMT") else None),
        "stop_price":  (float(stp) if otype in ("STP", "STP LMT", "BRACKET") else None),
        "target_price":(float(tgt) if otype == "BRACKET" else None),
        "exchange": "SMART",
        "currency": "USD",
        "asset": "stock",
    }
    try:
        r = requests.post(f"{BRIDGE_URL}/order", json=payload,
                          headers={"x-api-key": API_KEY}, timeout=15)
        if r.ok:
            st.success(r.json())
        else:
            st.error(f"{r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"Order failed: {e}")
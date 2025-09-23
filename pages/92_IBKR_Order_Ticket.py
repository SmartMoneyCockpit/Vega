# pages/92_IBKR_Order_Ticket.py
import os, requests, streamlit as st

st.set_page_config(page_title="IBKR Order Ticket", layout="wide")
st.title("IBKR Order Ticket")

BRIDGE_URL = os.getenv("IBKR_BRIDGE_URL", "http://127.0.0.1:8088")
API_KEY    = os.getenv("IBKR_API_KEY", os.getenv("BRIDGE_API_KEY", ""))

def place_order(symbol, side, qty, order_type="MKT", limit_price=None):
    try:
        payload = {
            "symbol": symbol,
            "side": side.lower(),
            "quantity": qty,
            "type": order_type.upper()
        }
        if order_type.upper() == "LMT" and limit_price:
            payload["limit_price"] = limit_price
        r = requests.post(f"{BRIDGE_URL}/order",
                          headers={"x-api-key": API_KEY},
                          json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

symbol = st.text_input("Symbol", "SPY").upper().strip()
side = st.selectbox("Side", ["buy", "sell"])
qty = st.number_input("Quantity", min_value=1, value=1)
otype = st.selectbox("Order Type", ["MKT", "LMT"])
limit_price = None
if otype == "LMT":
    limit_price = st.number_input("Limit Price", min_value=0.0, value=0.0)

if st.button("Place Order", type="primary"):
    res = place_order(symbol, side, qty, otype, limit_price)
    st.write("Response:", res)


# --- Extended Order Types & Recent Orders ---
import json

def place_order_ext(payload):
    try:
        r = requests.post(f"{BRIDGE_URL}/order",
                          headers={"x-api-key": API_KEY},
                          json=payload, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

st.markdown("### Advanced Options")
otype_adv = st.selectbox("Advanced Order Type", ["None","STP","STP LMT","Bracket"])

stop_price, target_price = None, None
if otype_adv in ["STP","STP LMT"]:
    stop_price = st.number_input("Stop Price", min_value=0.0, value=0.0)
if otype_adv == "STP LMT":
    limit_price = st.number_input("Stop-Limit Price", min_value=0.0, value=0.0)
if otype_adv == "Bracket":
    stop_price = st.number_input("Bracket Stop Price", min_value=0.0, value=0.0)
    target_price = st.number_input("Bracket Target Price", min_value=0.0, value=0.0)

if st.button("Confirm & Place Advanced Order", type="primary"):
    payload = {
        "symbol": symbol,
        "side": side,
        "quantity": qty,
        "type": otype
    }
    if otype == "LMT" and limit_price:
        payload["limit_price"] = limit_price
    if otype_adv == "STP":
        payload["type"] = "STP"
        payload["stop_price"] = stop_price
    if otype_adv == "STP LMT":
        payload["type"] = "STP LMT"
        payload["stop_price"] = stop_price
        payload["limit_price"] = limit_price
    if otype_adv == "Bracket":
        payload["type"] = "BRACKET"
        payload["stop_price"] = stop_price
        payload["target_price"] = target_price

    res = place_order_ext(payload)
    st.write("Response:", res)

st.markdown("### Recent Orders")
try:
    r = requests.get(f"{BRIDGE_URL}/orders", headers={"x-api-key": API_KEY}, timeout=6)
    if r.status_code == 200:
        st.table(r.json()[-10:])
except Exception as e:
    st.error(f"Error fetching orders: {e}")

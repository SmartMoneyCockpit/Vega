# pages/098_IBKR_Order_Ticket_ib.py
import streamlit as st
from ib_insync import MarketOrder, LimitOrder
from src.ibkr_bridge import connect_ib, to_ib_contract, get_delayed_last

st.title("IBKR Order Ticket (ib_insync)")
col1, col2, col3 = st.columns(3)
with col1: symbol = st.text_input("Symbol", "SPY")
with col2: side = st.selectbox("Side", ["buy","sell"])
with col3: qty = st.number_input("Quantity", min_value=1, value=1, step=1)

otype = st.selectbox("Order Type", ["MKT","LMT"])
limit_price = None
if otype == "LMT":
    limit_price = st.number_input("Limit Price", min_value=0.0, value=0.0, step=0.01, format="%.2f")

confirm = st.checkbox("I understand and want to place this order now.", value=False)
if st.button("Place Order"):
    try:
        ib = connect_ib()
        contract = to_ib_contract(symbol.strip())
        action = "BUY" if side=="buy" else "SELL"
        if otype == "MKT":
            order = MarketOrder(action, qty)
        else:
            if not limit_price or limit_price <= 0:
                px = get_delayed_last(ib, symbol.strip()) or 0
                if px <= 0: raise RuntimeError("No price to infer a limit; enter a price.")
                limit_price = round(px * (1.01 if action=="BUY" else 0.99), 2)
            order = LimitOrder(action, qty, limit_price)
        if not confirm:
            st.warning("Safety is OFF: no order sent. Tick the checkbox to transmit.")
        else:
            trade = ib.placeOrder(contract, order)
            st.success(f"Order sent: {action} {qty} {symbol} ({otype}{' @ '+str(limit_price) if otype=='LMT' else ''})")
            st.write("Status:", trade.orderStatus.status)
        ib.disconnect()
    except Exception as e:
        st.error(f"Order error: {e}")

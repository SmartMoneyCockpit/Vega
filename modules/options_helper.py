import streamlit as st

def decide_trade(options_iv_overpriced: bool, options_iv_underpriced: bool, days_to_expiry: int, earnings_in_days: int, rr_ratio: float):
    if earnings_in_days is not None and earnings_in_days <= 30:
        return "WAIT (Earnings within 30 days)"
    if options_iv_underpriced and 21 <= days_to_expiry <= 90 and rr_ratio >= 3.0:
        return "OPTIONS: Calls / Call Spreads (~60% POP)"
    if options_iv_overpriced and 21 <= days_to_expiry <= 90 and rr_ratio >= 3.0:
        return "OPTIONS: Puts / Put Spreads (~60% POP)"
    if rr_ratio >= 3.0:
        return "STOCK (Default)"
    return "REJECT (R:R < 1:3)"

def render():
    st.header("Options Helper")
    st.caption("Auto-selects Stock vs Options: ~60% POP, 21–90 DTE, ≥1:3 R:R, no buys within 30 days of earnings.")
    c1,c2,c3 = st.columns(3)
    with c1:
        overpriced = st.toggle("Options IV Overpriced?", value=False)
    with c2:
        underpriced = st.toggle("Options IV Underpriced?", value=False)
    with c3:
        dte = st.number_input("Days to Expiry (DTE)", min_value=0, value=45)
    e_days = st.number_input("Earnings in (days)", min_value=0, value=45)
    rr = st.number_input("Risk:Reward (e.g., 3 = 1:3)", min_value=0.0, value=3.0, step=0.1)
    st.success(decide_trade(overpriced, underpriced, dte, e_days, rr))

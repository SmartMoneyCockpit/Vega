import streamlit as st
from modules.risk.risk_scoring import full_report
from data.eodhd_adapter import get_eod_prices_csv

def render(symbol: str = "SPY", benchmark: str = "SPY", period: str = "1y"):
    st.markdown("### 📊 Risk Score (EODHD)")
    c1, c2, c3 = st.columns([2,2,1])
    with c1:
        sym = st.text_input("Symbol", value=symbol, key="risk_tile_symbol")
    with c2:
        bm = st.text_input("Benchmark", value=benchmark, key="risk_tile_bench")
    with c3:
        per = st.selectbox("Lookback", ["6m","1y","2y","3y","5y"], index=1, key="risk_tile_period")

    if st.button("Update Risk Score", key="risk_tile_btn"):
        df = get_eod_prices_csv(sym, period=per)
        col = "adjusted_close" if "adjusted_close" in df.columns else "close"
        prices = df.set_index("date")[col]
        bench = None
        if bm.strip():
            bf = get_eod_prices_csv(bm.strip(), period=per)
            bcol = "adjusted_close" if "adjusted_close" in bf.columns else "close"
            bench = bf.set_index("date")[bcol]
        rep = full_report(prices, bench)
        st.json(rep)

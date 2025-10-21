import os, sys, pathlib
# Ensure 'src' imports resolve when running from repo root
_here = pathlib.Path(__file__).resolve()
src_root = _here.parents[1]
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

try:
    from modules.risk.risk_scoring import full_report
except Exception as _ex:
    import importlib
    full_report = importlib.import_module('modules.risk.risk_scoring').full_report
from data.eodhd_adapter import get_eod_prices_csv

st.set_page_config(page_title="Risk & Return Scoring", page_icon="📊", layout="wide")

st.title("📊 Vega Risk & Return Scoring Engine")

col1, col2, col3 = st.columns([2,1,1])
with col1:
    symbol = st.text_input("Symbol (required)", value="SPY")
with col2:
    benchmark = st.text_input("Benchmark (optional)", value="SPY")
with col3:
    period = st.selectbox("Lookback", ["6m","1y","2y","3y","5y"], index=1)

run = st.button("Compute Score", type="primary")

if run:
    with st.spinner("Fetching prices & computing metrics..."):
        df = get_eod_prices_csv(symbol, period=period)
        col = "adjusted_close" if "adjusted_close" in df.columns else "close"
        prices = df.set_index("date")[col]

        bench_prices = None
        if benchmark.strip():
            bf = get_eod_prices_csv(benchmark.strip(), period=period)
            bcol = "adjusted_close" if "adjusted_close" in bf.columns else "close"
            bench_prices = bf.set_index("date")[bcol]

        report = full_report(prices, bench_prices)

    st.subheader("Metrics")
    st.json(report)

    st.subheader("Price Series")
    fig = plt.figure()
    prices.plot()
    st.pyplot(fig)

import os, sys, pathlib
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

_here = pathlib.Path(__file__).resolve()
sys.path.append(str(_here.parents[1]))  # add src

from data.eodhd_adapter import get_eod_prices_csv
from modules.exports.snapshot import export_dataframe_png, export_dataframe_csv

st.set_page_config(page_title="Relative Strength Dashboard", page_icon="📈", layout="wide")
st.title("📈 Relative Strength Momentum Dashboard")

with st.expander("Settings"):
    symbols = st.text_input("Symbols (comma separated)", value="SPY, QQQ, IWM")
    benchmark = st.text_input("Benchmark", value="SPY")
    period = st.selectbox("Lookback", ["6m","1y","2y"], index=0)

def compute_rs(sym, bench, period):
    df = get_eod_prices_csv(sym, period=period)
    bf = get_eod_prices_csv(bench, period=period)
    col = "adjusted_close" if "adjusted_close" in df.columns else "close"
    bcol = "adjusted_close" if "adjusted_close" in bf.columns else "close"
    s = df.set_index("date")[col]
    b = bf.set_index("date")[bcol]
    aligned = pd.concat([s, b], axis=1).dropna()
    rs = aligned.iloc[:,0] / aligned.iloc[:,1]
    rs = rs / rs.iloc[0]  # normalize
    rs_ma4  = rs.rolling(20).mean()
    rs_ma12 = rs.rolling(60).mean()
    return pd.DataFrame({"RS": rs, "RS_MA4": rs_ma4, "RS_MA12": rs_ma12})

if st.button("Run RS"):
    syms = [x.strip() for x in symbols.split(",") if x.strip()]
    tabs = st.tabs(syms)
    for i, sym in enumerate(syms):
        with tabs[i]:
            df = compute_rs(sym, benchmark, period)
            st.line_chart(df)

    # Export panel (simple combined export of last computed df)
    st.markdown("---")
    st.subheader("Export")
    try:
        img = export_dataframe_png(df, title="RS_Dashboard")
        csv = export_dataframe_csv(df.reset_index().rename(columns={"index":"date"}), title="RS_Dashboard")
        st.success(f"Saved: {img}")
        st.success(f"Saved: {csv}")
    except Exception as ex:
        st.warning(f"Export failed: {ex}")

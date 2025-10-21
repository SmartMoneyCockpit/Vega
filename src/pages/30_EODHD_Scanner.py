import os, sys, pathlib
import streamlit as st
import pandas as pd

_here = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[1]))

from data.eodhd_adapter import get_eod_prices_csv, latest_close
from data.regions import REGIONS

st.set_page_config(page_title="EODHD Stock Scanner", page_icon="📡", layout="wide")
st.title("📡 EODHD Stock Scanner")

col1, col2 = st.columns([2,1])
with col1:
    region = st.selectbox("Region", list(REGIONS.keys()), index=0)
with col2:
    lookback = st.selectbox("Lookback", ["3m","6m","1y"], index=1)

if st.button("Fetch Snapshot", type="primary"):
    syms = REGIONS[region]
    rows = []
    for s in syms:
        try:
            df = get_eod_prices_csv(s, period=lookback)
            col = "adjusted_close" if "adjusted_close" in df.columns else "close"
            last = float(df[col].iloc[-1])
            chg1d = float((df[col].iloc[-1]/df[col].iloc[-2]-1)*100) if len(df)>1 else 0.0
            rows.append({"Symbol": s, "Last": round(last,2), "Change 1D %": round(chg1d,2)})
        except Exception as ex:
            rows.append({"Symbol": s, "Error": str(ex)[:120]})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

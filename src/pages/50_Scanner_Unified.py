import os, sys, pathlib
import streamlit as st
import pandas as pd

_here = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[1]))

from data.eodhd_adapter import get_eod_prices_csv
from data.regions import REGIONS
from modules.scanner.patterns import rising_wedge, falling_wedge, bearish_setup_score
from modules.exports.snapshot import export_df_csv

st.set_page_config(page_title="Scanner – Unified", page_icon="🧭", layout="wide")
st.title("🧭 Unified Scanner")

colA, colB, colC = st.columns([1.2,1,1])
with colA:
    region = st.selectbox("Region", list(REGIONS.keys()), index=0)
with colB:
    scan = st.selectbox("Scan Type", ["Rising Wedge","Falling Wedge","Best Downside Setups"])
with colC:
    lookback = st.selectbox("Lookback", ["3m","6m","1y"], index=1)

run = st.button("Run Scan", type="primary")
if run:
    syms = REGIONS[region]
    rows = []
    for sym in syms:
        try:
            df = get_eod_prices_csv(sym, period=lookback)
            col = "adjusted_close" if "adjusted_close" in df.columns else "close"
            s = df.set_index("date")[col]
            if scan == "Rising Wedge":
                flag = rising_wedge(s, lookback=60)
                rows.append({"Symbol": sym, "Match": bool(flag)})
            elif scan == "Falling Wedge":
                flag = falling_wedge(s, lookback=60)
                rows.append({"Symbol": sym, "Match": bool(flag)})
            else:
                score = bearish_setup_score(s, window=20)
                rows.append({"Symbol": sym, "BearishScore": score})
        except Exception as ex:
            rows.append({"Symbol": sym, "Error": str(ex)[:120]})
    out = pd.DataFrame(rows)
    if scan != "Best Downside Setups":
        out = out[out["Match"]==True]
    else:
        out = out.sort_values("BearishScore", ascending=False)
    st.subheader("Results")
    st.dataframe(out, use_container_width=True)
    path = export_df_csv(out, f"{region.replace('/','-')}_{scan.replace(' ','_')}")
    st.success(f"Saved: {path}")

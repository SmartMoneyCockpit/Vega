import os, sys, pathlib
import streamlit as st
import pandas as pd

_here = pathlib.Path(__file__).resolve()
sys.path.append(str(_here.parents[1]))  # add src

from data.eodhd_adapter import get_eod_prices_csv
from modules.exports.snapshot import export_dataframe_png, export_dataframe_csv

st.set_page_config(page_title="Sector Momentum Tiles", page_icon="🧩", layout="wide")
st.title("🧩 Sector Momentum Tiles (Daily EOD)")

sectors = {
    "XLK":"Tech", "XLI":"Industrials", "XLB":"Materials",
    "XLF":"Financials", "XLP":"Staples", "XLY":"Discretionary",
    "XLV":"Health Care", "XLU":"Utilities", "XLRE":"Real Estate", "XLC":"Comm Services"
}

with st.expander("Settings"):
    lookback = st.selectbox("Lookback", ["6m","1y"], index=0)
    benchmark = st.text_input("Benchmark", value="SPY")

def momentum_score(sym, bm, period):
    df = get_eod_prices_csv(sym, period=period)
    bf = get_eod_prices_csv(bm, period=period)
    col = "adjusted_close" if "adjusted_close" in df.columns else "close"
    bcol = "adjusted_close" if "adjusted_close" in bf.columns else "close"
    s = df.set_index("date")[col]
    b = bf.set_index("date")[bcol]
    aligned = pd.concat([s,b], axis=1).dropna()
    ret = aligned.iloc[-1,0]/aligned.iloc[0,0]-1
    rrel= (aligned.iloc[-1,0]/aligned.iloc[0,0])/(aligned.iloc[-1,1]/aligned.iloc[0,1]) - 1
    return ret, rrel

if st.button("Compute Tiles"):
    rows=[]
    for sym, name in sectors.items():
        r, rr = momentum_score(sym, benchmark, lookback)
        status = "🟢 Buy Today" if rr>0 and r>0 else ("🟡 Wait" if rr> -0.02 else "🔴 Avoid")
        rows.append({"ETF": sym, "Sector": name, "AbsRet": round(r,4), "RelRet": round(rr,4), "Status": status})
    df = pd.DataFrame(rows).sort_values("RelRet", ascending=False)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    img = export_dataframe_png(df.set_index("ETF")[["AbsRet","RelRet"]], title="Sector_Momentum")
    csv = export_dataframe_csv(df, title="Sector_Momentum")
    st.success(f"Saved: {img}")
    st.success(f"Saved: {csv}")

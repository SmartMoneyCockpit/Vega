# pages/01_RealTime_Scanner.py
import os, time
import pandas as pd
import streamlit as st

from integration.scanner_client import load_snapshot

st.set_page_config(page_title="Real‑Time Scanner", layout="wide")

st.title("Real‑Time Scanner (VectorVest/TradingView style)")

colA, colB = st.columns(2)
with colA:
    st.caption("Source")
    st.code(f"SCANNER_URL={os.environ.get('SCANNER_URL','http://127.0.0.1:8080/snapshot')}", language="shell")
with colB:
    st.caption("Fallback path")
    st.code(f"SCANNER_PATH={os.environ.get('SCANNER_PATH','outputs/snapshot.json')}", language="shell")

data = load_snapshot()
if not data or "rows" not in data:
    st.warning("No snapshot available yet. Make sure the scanner is running (and the API if using HTTP).")
    st.stop()

rows = data["rows"]
df = pd.DataFrame(rows)

# Basic columns in a friendly order
cols = ["ticker","last","changePct","rsi14","ema9","ema21","ema50","ema200","ha_trend","trade_now"]
for c in cols:
    if c not in df.columns: cols.remove(c)
df = df[cols + [c for c in df.columns if c not in cols]]

# Colorize 'trade_now'
def color_trade(val):
    if val == "🟢": return "background-color: #eaffea"
    if val == "🟡": return "background-color: #fffbea"
    if val == "🔴": return "background-color: #ffefef"
    return ""
st.dataframe(df.style.applymap(color_trade, subset=["trade_now"]), use_container_width=True)

with st.expander("Raw JSON"):
    st.json(data)

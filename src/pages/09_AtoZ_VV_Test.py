
import os, sys, json, streamlit as st

# Ensure /opt/render/project/src (this file's parent) is importable as top-level
THIS_DIR = os.path.dirname(__file__)
SRC_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from components.az_vv import render_vv_block

st.set_page_config(page_title="A-to-Z + VectorVest (Demo)", layout="wide")
st.title("A-to-Z + VectorVest — Demo")

syms = []
p = os.path.join("vault","cache","vectorvest_signals.json")
if os.path.exists(p):
    try:
        data = json.load(open(p,"r",encoding="utf-8"))
        syms = sorted({str(i.get("symbol","")).upper() for i in data.get("signals",[]) if i.get("symbol")})
    except Exception:
        pass

symbol = st.selectbox("Symbol", syms, index=0 if syms else None)
window = st.select_slider("Window", options=["26w","52w"], value="26w")

if symbol:
    render_vv_block(symbol, window=window)
else:
    st.info("Add symbols to vault/cache/vectorvest_signals.json to test.")


# src/pages/05_TradingView_Charts.py
import os, json
import streamlit as st
from components.tv_bridge import render_chart, render_heatmap, render_login_helper
from components.tv_bus import push_symbol

st.set_page_config(page_title="TradingView Bridge", layout="wide")
st.title("TradingView — Bridge")

with st.expander("Login Help", expanded=False):
    render_login_helper()
    st.caption("Allow third-party cookies for tradingview.com / s.tradingview.com")

DATA_DIR = os.getenv("DATA_DIR", "data")
APPROVED_JSON = os.path.join(DATA_DIR, "approved_tickers.json")
approved = []
if os.path.exists(APPROVED_JSON):
    try:
        approved = json.load(open(APPROVED_JSON, "r", encoding="utf-8")).get("approved", [])
    except Exception:
        approved = []

st.subheader("Chart")
c1, c2, c3, c4 = st.columns([2,1,1,1])
with c1:
    symbol = st.text_input("Symbol", value=st.session_state.get("symbol","NYSE:RBC"), key="symbol")
with c2:
    interval = st.selectbox("Interval", ["1","5","15","30","60","D","W","M"],
                            index=["1","5","15","30","60","D","W","M"].index(st.session_state.get("interval","D")),
                            key="interval")
with c3:
    theme = st.selectbox("Theme", ["dark","light"],
                         index=["dark","light"].index(st.session_state.get("theme","dark")),
                         key="theme")
with c4:
    mode = st.selectbox("Mode", ["auto","iframe"], index=0, key="mode",
                        help="auto = tv.js with built-ins; iframe = your TradingView layout/session")

if st.button("Reset to Vega Defaults (HA + EMAs + Built-ins)"):
    st.session_state.update({"symbol":"NYSE:RBC","interval":"D","theme":"dark","mode":"auto","region":"USA"})
    st.experimental_rerun()

render_chart(symbol, interval=interval, theme=theme, height=600, overlays=None, mode=mode)

ar1, ar2 = st.columns([1,3])
with ar1:
    autorotate = st.toggle("Auto-rotate", value=False)
with ar2:
    rotate_sec = st.number_input("Every (sec)", value=20, min_value=5, step=5)

if autorotate and mode != "iframe" and approved:
    idx_key = "_tv_autorotate_idx"
    i = st.session_state.get(idx_key, 0) % len(approved)
    next_sym = approved[i]
    push_symbol(next_sym, interval)
    st.session_state[idx_key] = (i + 1) % len(approved)
    st.markdown(f"<script>setTimeout(() => window.location.reload(), {int(rotate_sec*1000)});</script>", unsafe_allow_html=True)

st.subheader("Sector Heatmap")
region = st.selectbox("Region", ["USA","Canada","Mexico"],
                      index=["USA","Canada","Mexico"].index(st.session_state.get("region","USA")),
                      key="region")
height = st.slider("Heatmap height", 600, 1400, 900, 10)
render_heatmap(region, height=height)

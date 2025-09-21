import streamlit as st
from components.tv_bridge import render_chart, render_heatmap, render_login_helper

st.set_page_config(page_title="TradingView Bridge", layout="wide")
st.title("TradingView — Bridge")

with st.expander("Login Help", expanded=True):
    render_login_helper()

st.subheader("Chart")
c1, c2, c3, c4 = st.columns([2,1,1,1])
with c1:
    symbol = st.text_input("Symbol", value="NASDAQ:QQQ")
with c2:
    interval = st.selectbox("Interval", ["1","5","15","30","60","D","W","M"], index=6)
with c3:
    theme = st.selectbox("Theme", ["dark","light"], index=0)
with c4:
    mode = st.selectbox("Mode", ["auto","iframe","tvjs"], index=0)

st.caption("Overlays (codes: e9,e21,e50,e200,bb,ichi) — used in tvjs mode.")
ov = st.multiselect("Overlays", ["e9","e21","e50","e200","bb","ichi"], default=["e9","e21","e50","e200"] if mode!='iframe' else [])

if mode == "iframe":
    st.info("If you still see public data, allow third‑party cookies for tradingview.com / s.tradingview.com, sign in in a new tab, then press ↻ Refresh below the chart.")

render_chart(symbol, interval=interval, theme=theme, height=600, overlays=(ov if mode!='iframe' else None), mode=mode)

st.subheader("Sector Heatmap")
region = st.selectbox("Region", ["USA","Canada","Mexico"], index=0)
render_heatmap(region, height=520)

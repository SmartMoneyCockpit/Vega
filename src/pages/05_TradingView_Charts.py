import streamlit as st
from components.tv_bridge import render_chart, render_heatmap, render_login_helper

st.set_page_config(page_title="TradingView Charts", layout="wide")
st.title("TradingView — Charts & Heatmap (Bridge)")

with st.expander("Login Help", expanded=False):
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
    mode = st.selectbox("Mode", ["auto","iframe","tvjs"], index=0, help="iframe uses your TradingView login; tvjs uses built-in studies.")

st.caption("Overlays (built-ins):")
ov = st.multiselect("Select studies", ["EMA 9","EMA 21","EMA 50","EMA 200","Bollinger (20,2)","Ichimoku (9/26/52)"],
                    default=["EMA 9","EMA 21","EMA 50","EMA 200"] if mode != "iframe" else [])
_name_to_code = {"EMA 9":"e9","EMA 21":"e21","EMA 50":"e50","EMA 200":"e200","Bollinger (20,2)":"bb","Ichimoku (9/26/52)":"ichi"}
codes = [_name_to_code[i] for i in ov]

if mode == "iframe":
    st.info("If the chart looks 'logged-out', enable third‑party cookies for tradingview.com / s.tradingview.com, sign in to TradingView in a new tab, then click ↻ Refresh after sign‑in below the chart.")

render_chart(symbol, interval=interval, theme=theme, height=600, overlays=(codes if mode!='iframe' else None), mode=mode)

st.subheader("Sector Heatmap")
region = st.selectbox("Region", ["USA","Canada","Mexico"], index=0)
render_heatmap(region, height=520)

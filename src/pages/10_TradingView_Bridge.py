
"""
src/pages/10_TradingView_Bridge.py — adds height slider and uses tv_bridge APIs
"""
import streamlit as st
from components.tv_bridge import render_chart, render_heatmap, render_login_helper

st.set_page_config(page_title="TradingView — Bridge", layout="wide")
st.title("TradingView — Bridge")

with st.expander("Login Help", expanded=False):
    st.write("This page uses public widgets for now. Authenticated embeds will be wired later.")

with st.expander("About TradingView Embeds / Auth vs Public", expanded=False):
    st.write("Public widgets (no login) vs Authenticated (private layouts). Public mode is active.")

with st.container():
    st.subheader("Chart")
    c1, c2, c3, c4 = st.columns([2,1,1,1])
    with c1:
        symbol = st.text_input("Symbol", "NASDAQ:QQQ")
    with c2:
        interval = st.selectbox("Interval", ["1","5","15","60","D","W","M"], index=4)
    with c3:
        theme = st.selectbox("Theme", ["dark","light"], index=0)
    with c4:
        height = st.slider("Height", 500, 1400, 860, 20)

    # overlays UI kept for compatibility but not passed (public widget cannot set overlays)
    overlays = st.multiselect("Overlays (UI only, public widget ignores)", ["e9","e21","e50","e200","bb","ich"], ["e9","e21","e50","e200"])

    render_chart(symbol=symbol, interval=interval, theme=theme, height=height)

st.divider()
st.subheader("Heatmap")
hm_col1, hm_col2 = st.columns([1,3])
with hm_col1:
    market = st.selectbox("Market", ["US","WORLD","EU","JP","CN"], index=0)
with hm_col2:
    hm_height = st.slider("Heatmap height", 400, 1200, 560, 20)

render_heatmap(market=market, theme=theme, height=hm_height)
render_login_helper("Public mode active. Height controls enabled.")

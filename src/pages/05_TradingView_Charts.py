import streamlit as st
from components.tv_bridge import render_chart, render_heatmap, render_login_helper

st.set_page_config(page_title="TradingView Charts", layout="wide")
st.title("TradingView — Charts & Heatmap (Bridge)")

with st.expander("Login Help", expanded=False):
    render_login_helper()

st.subheader("Chart")
c1, c2, c3 = st.columns([2,1,1])
with c1:
    symbol = st.text_input("Symbol", value="NASDAQ:QQQ")
with c2:
    interval = st.selectbox("Interval", ["1","5","15","30","60","D","W","M"], index=6)
with c3:
    theme = st.selectbox("Theme", ["dark","light"], index=0)

render_chart(symbol, interval=interval, theme=theme, height=600)

st.subheader("Sector Heatmap")
region = st.selectbox("Region", ["USA","Canada","Mexico"], index=0)
render_heatmap(region, height=520)

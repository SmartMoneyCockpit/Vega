
"""
src/pages/05_TradingView_Charts.py
Safe public-version page that depends on components.tv_bridge.
If/when you wire authenticated TV, you can swap implementations inside tv_bridge.py
without touching this page again.
"""
import streamlit as st
from components.tv_bridge import render_chart, render_heatmap, render_login_helper

st.set_page_config(page_title="TradingView Charts & Heatmap", layout="wide")
st.title("TradingView — Public Widgets")

with st.sidebar:
    st.subheader("Chart controls")
    symbol = st.text_input("Symbol", "NASDAQ:QQQ")
    interval = st.selectbox("Interval", ["1","5","15","60","D","W","M"], index=4)
    theme = st.radio("Theme", ["dark","light"], index=0, horizontal=True)
    st.subheader("Heatmap")
    market = st.selectbox("Market", ["US","WORLD","EU","JP","CN"], index=0)

col1, col2 = st.columns([2,1])
with col1:
    render_chart(symbol=symbol, interval=interval, theme=theme, height=560)
with col2:
    render_heatmap(market=market, theme=theme, height=560)

render_login_helper("Running in Public widget mode. Your private layouts will appear once auth cookies are connected.")

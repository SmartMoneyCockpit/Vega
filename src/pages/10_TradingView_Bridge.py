
# src/pages/10_TradingView_Bridge.py
import streamlit as st, os, json
from components.tv_bridge import render_chart, render_heatmap, render_login_helper

st.set_page_config(page_title="TradingView Bridge", layout="wide")
st.title("TradingView — Bridge")

st.caption("Uses your browser login for authenticated iframes. Env URLs override behavior when set.")

with st.expander("Login Help", expanded=False):
    render_login_helper()

st.subheader("Chart")
col1, col2, col3 = st.columns([2,1,1])
with col1:
    symbol = st.text_input("Symbol", value="NASDAQ:QQQ", help="Use TV syntax, e.g., NASDAQ:QQQ, NYSEARCA:SPY")
with col2:
    interval = st.selectbox("Interval", ["1", "5", "15", "30", "60", "D", "W", "M"], index=6)
with col3:
    theme = st.selectbox("Theme", ["dark", "light"], index=0)

render_chart(symbol, interval=interval, theme=theme, height=600)

st.subheader("Sector Heatmap")
region = st.selectbox("Region", ["USA", "Canada", "Mexico"], index=0)
render_heatmap(region, height=520)

st.caption("Tip: set TV_EMBED_TEMPLATE, TV_HEATMAP_{REGION}_AUTH_URL, TV_HEATMAP_{REGION}_PUBLIC_URL in environment to override defaults.")

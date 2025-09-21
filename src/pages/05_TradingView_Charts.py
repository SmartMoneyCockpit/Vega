
"""
src/pages/05_TradingView_Charts.py — NA-style big chart with height slider + compact layout
"""
import streamlit as st
from urllib.parse import urlencode
from components.tv_bridge import render_chart, render_heatmap, render_login_helper

st.set_page_config(page_title="TradingView — Public Widgets", layout="wide")

# --- Global compact CSS (reduce top/bottom padding, tighten gaps)
st.markdown("""
<style>
/* tighten the page chrome */
.block-container {padding-top: 0.6rem; padding-bottom: 0.6rem;}
/* remove extra gaps that Streamlit adds around components */
section.main > div {gap: 0.6rem;}
/* Make our widget rows denser */
.stButton > button {width: 100%;}
</style>
""", unsafe_allow_html=True)

# Fullscreen route (no sidebar chrome)
qp = st.query_params
if qp.get("fullscreen", ["0"])[0] == "1":
    symbol = qp.get("symbol", ["NASDAQ:QQQ"])[0]
    interval = qp.get("interval", ["D"])[0]
    theme = qp.get("theme", ["dark"])[0]
    height = int(qp.get("height", ["1100"])[0])
    render_chart(symbol=symbol, interval=interval, theme=theme, height=height)
    st.stop()

st.title("TradingView — Public Widgets")

with st.sidebar:
    st.subheader("Chart controls")
    symbol = st.text_input("Symbol", "NASDAQ:QQQ")
    interval = st.selectbox("Interval", ["1","5","15","60","D","W","M"], index=4)
    theme = st.radio("Theme", ["dark","light"], index=0, horizontal=True)
    height = st.slider("Chart height", 500, 1600, 980, 20)  # NA‑style default
    layout = st.radio("Layout", ["Chart only", "Chart + Heatmap"], index=0)  # default to Chart only
    compact = st.toggle("Compact mode (less padding)", value=True)

def _open_fullscreen_link(symbol, interval, theme, height):
    params = {"fullscreen":"1","symbol":symbol,"interval":interval,"theme":theme,"height":height}
    st.link_button("Open full-page chart (in-app)", f"?{urlencode(params)}", use_container_width=True)

def _open_on_tradingview(symbol):
    st.link_button("Open on TradingView", f"https://www.tradingview.com/chart/?symbol={symbol}", use_container_width=True)

# Top action buttons
_open_fullscreen_link(symbol, interval, theme, height)
_open_on_tradingview(symbol)

# Layout
if layout == "Chart only":
    # Full width big chart
    render_chart(symbol=symbol, interval=interval, theme=theme, height=height)
else:
    # 3:1 chart + heatmap
    col1, col2 = st.columns([3, 1])
    with col1:
        render_chart(symbol=symbol, interval=interval, theme=theme, height=height)
    with col2:
        render_heatmap(market="US", theme=theme, height=max(420, height-80))

# Info (collapsed by default to avoid taking space)
with st.expander("About TradingView Embeds / Auth vs Public", expanded=False):
    render_login_helper("Public widget mode active. Height slider + full-page view enabled.")

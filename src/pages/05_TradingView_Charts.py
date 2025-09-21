
"""
src/pages/05_TradingView_Charts.py — Big / full‑page chart upgrade
- Height slider (500–1400)
- Layout: Chart+Heatmap or Chart only
- Full‑page mode via query param ?fullscreen=1
- Quick links: Open full‑page (in‑app), Open on TradingView
"""
import streamlit as st
from urllib.parse import urlencode
from components.tv_bridge import render_chart, render_heatmap, render_login_helper

st.set_page_config(page_title="TradingView — Public Widgets", layout="wide")

# --- Fullscreen route (no sidebar chrome) ---
qp = st.query_params
if qp.get("fullscreen", ["0"])[0] == "1":
    symbol = qp.get("symbol", ["NASDAQ:QQQ"])[0]
    interval = qp.get("interval", ["D"])[0]
    theme = qp.get("theme", ["dark"])[0]
    height = int(qp.get("height", ["980"])[0])
    render_chart(symbol=symbol, interval=interval, theme=theme, height=height)
    st.stop()

st.title("TradingView — Public Widgets")

with st.sidebar:
    st.subheader("Chart controls")
    symbol = st.text_input("Symbol", "NASDAQ:QQQ")
    interval = st.selectbox("Interval", ["1","5","15","60","D","W","M"], index=4)
    theme = st.radio("Theme", ["dark","light"], index=0, horizontal=True)
    height = st.slider("Chart height", 500, 1400, 820, 20)
    layout = st.radio("Layout", ["Chart + Heatmap", "Chart only"], index=0)

def _open_fullscreen_link(symbol, interval, theme, height):
    params = {"fullscreen":"1","symbol":symbol,"interval":interval,"theme":theme,"height":height}
    query = urlencode(params)
    url = f"?{query}"
    st.link_button("Open full‑page chart (in‑app)", url, use_container_width=True)

def _open_on_tradingview(symbol):
    # Basic symbol URL (public)
    base = "https://www.tradingview.com/chart/?symbol="
    st.link_button("Open on TradingView", f"{base}{symbol}", use_container_width=True)

if layout == "Chart only":
    _open_fullscreen_link(symbol, interval, theme, height)
    _open_on_tradingview(symbol)
    render_chart(symbol=symbol, interval=interval, theme=theme, height=height)
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        _open_fullscreen_link(symbol, interval, theme, height)
        _open_on_tradingview(symbol)
        render_chart(symbol=symbol, interval=interval, theme=theme, height=height)
    with col2:
        render_heatmap(market="US", theme=theme, height=height-60)

render_login_helper("Running in Public widget mode. Your private layouts will appear once auth cookies are connected.")

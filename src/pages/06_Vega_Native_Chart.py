
import streamlit as st
from urllib.parse import urlencode

# Robust import shim (works whether app root includes 'src' on sys.path or not)
try:
    from src.services.datafeed import fetch_ohlcv
    from src.components.native_chart import render
except ModuleNotFoundError:
    import sys, pathlib
    root = pathlib.Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.append(str(root))
    try:
        from src.services.datafeed import fetch_ohlcv
        from src.components.native_chart import render
    except Exception:
        # Last resort: direct import without package prefix
        from services.datafeed import fetch_ohlcv
        from components.native_chart import render

st.set_page_config(page_title="Vega Native Chart — Lightweight Charts", layout="wide")

# --- Fullscreen route for big chart
qp = st.query_params
if qp.get("fullscreen", ["0"])[0] == "1":
    import pandas as pd
    symbol = qp.get("symbol", ["NASDAQ:QQQ"])[0]
    interval = qp.get("interval", ["D"])[0]
    theme = qp.get("theme", ["dark"])[0]
    height = int(qp.get("height", ["980"])[0])
    df = fetch_ohlcv(symbol, interval, 2000)
    render(df, theme=theme, main_height=height)
    st.stop()

st.sidebar.header("Vega Native Chart — Lightweight Charts")
symbol = st.sidebar.text_input("Symbol (e.g., NASDAQ:QQQ)", "NASDAQ:QQQ")
interval = st.sidebar.selectbox("Interval", ["D","W","M"], index=0)
theme = st.sidebar.radio("Theme", ["dark","light"], index=0, horizontal=True)
max_points = st.sidebar.slider("Max bars", 200, 5000, 1500, 100)
main_height = st.sidebar.slider("Main pane height", 500, 1600, 900, 20)

st.caption("Heikin-Ashi + EMA 9/21/50/200, Bollinger(20,2), Ichimoku(9/26/52), panes: MACD/RSI/OBV/ATR.")

@st.cache_data(show_spinner=False)
def _load(symbol, interval, max_points):
    return fetch_ohlcv(symbol, interval, max_points)

def _open_fullscreen_link(symbol, interval, theme, height):
    params = {"fullscreen":"1","symbol":symbol,"interval":interval,"theme":theme,"height":height}
    st.link_button("Open full-page native chart (in-app)", f"?{urlencode(params)}", use_container_width=True)

try:
    df = _load(symbol, interval, max_points)
    st.success(f"Loaded {len(df)} bars for {symbol} ({interval})")
    _open_fullscreen_link(symbol, interval, theme, main_height)
    render(df, theme=theme, main_height=main_height)
    with st.expander("Data (tail)", expanded=False):
        st.dataframe(df.tail(200), use_container_width=True)
except FileNotFoundError as e:
    st.error(str(e))
    st.info("You can drop a CSV at data/ohlc/<SYMBOL>_<INTERVAL>.csv with columns: time,open,high,low,close,volume")
except Exception as e:
    st.error(f"Error: {e}")

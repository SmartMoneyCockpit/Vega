
import json
import streamlit as st
import pandas as pd

from src.services.datafeed import fetch_ohlcv
from src.components.native_chart import render

st.set_page_config(page_title="Vega Native Chart — Lightweight Charts", layout="wide")

st.sidebar.header("Vega Native Chart — Lightweight Charts")
symbol = st.sidebar.text_input("Symbol (e.g., NASDAQ:QQQ)", "NASDAQ:QQQ")
interval = st.sidebar.selectbox("Interval", ["D","W","M"], index=0)
theme = st.sidebar.radio("Theme", ["dark","light"], index=0, horizontal=True)
max_points = st.sidebar.slider("Max bars", 200, 5000, 1500, 100)

st.caption("Heikin-Ashi candles + EMA 9/21/50/200, Bollinger(20,2), Ichimoku(9/26/52), and panes for MACD, RSI, OBV, ATR.")

@st.cache_data(show_spinner=False)
def _load(symbol, interval, max_points):
    return fetch_ohlcv(symbol, interval, max_points)

try:
    df = _load(symbol, interval, max_points)
    st.success(f"Loaded {len(df)} bars for {symbol} ({interval})")
    render(df, theme=theme)
    with st.expander("Data (tail)", expanded=False):
        st.dataframe(df.tail(200), use_container_width=True)
except FileNotFoundError as e:
    st.error(str(e))
    st.info("You can drop a CSV at data/ohlc/<SYMBOL>_<INTERVAL>.csv with columns: time,open,high,low,close,volume")
except Exception as e:
    st.error(f"Error: {e}")

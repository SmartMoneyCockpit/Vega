import streamlit as st
from vega.components.lightweight_charts import renderLightweightCharts

st.set_page_config(page_title="Vega Native Chart", layout="wide")
st.title("Vega Native Chart — Lightweight Charts")

# Simple inputs
sym = st.text_input("Symbol (e.g., NASDAQ:QQQ)", "NASDAQ:QQQ")
interval = st.selectbox("Interval", ["1","5","15","60","D","W","M"], index=4)
theme_choice = st.radio("Theme", ["dark","light"], index=0, horizontal=True)
height = 600

# Build a minimal series config (TradingView-like)
series = [{
    "type": "line",
    "symbol": sym,
    "interval": interval,
}]

st.caption("If you see an error, the chart component may be updating. Try a different symbol/interval.")
# IMPORTANT: renderLightweightCharts() in your build does not accept 'theme'. Remove kwarg.
renderLightweightCharts(series, height=height, key="native_lwc_v2")

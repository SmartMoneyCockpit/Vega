import streamlit as st
import pandas as pd
import yfinance as yf
try:
    from streamlit_lightweight_charts import render as lwc_render
except Exception:
    from streamlit_lightweight_charts import renderLightweightCharts as lwc_render

st.set_page_config(page_title="Vega Native Chart — Lightweight Charts", layout="wide")
st.title("Vega Native Chart — Lightweight Charts")

symbol = st.sidebar.text_input("Symbol (e.g., NASDAQ:QQQ)", value="NASDAQ:QQQ")
interval = st.sidebar.selectbox("Interval", ["D","W","M"], index=0)
theme = st.sidebar.radio("Theme", ["dark","light"], index=0)
height = 600

# Fetch data (last ~260 bars)
tkr = symbol.split(":")[-1]
df = yf.Ticker(tkr).history(period="2y")
if df.empty:
    st.warning(f"No data for {symbol}")
    st.stop()

st.success(f"Loaded {len(df)} bars for {symbol} ({interval})")

df = df.reset_index()
df["time"] = df["Date"].dt.strftime("%Y-%m-%d")
series = [{
    "type": "Candlestick",
    "data": [
        {
            "time": row["time"],
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
        }
        for _, row in df.tail(260).iterrows()
    ]
}]

options = {"layout": {"background": {"type": "solid"}}}
# Use 'height', not 'main_height' for older versions
lwc_render(series, options, theme=theme, height=height, key="native_lwc")

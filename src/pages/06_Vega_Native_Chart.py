import streamlit as st
import pandas as pd
import traceback

st.set_page_config(page_title="Vega Native Chart — Lightweight Charts", layout="wide")
st.title("Vega Native Chart — Lightweight Charts")

# UI
raw = st.sidebar.text_input("Symbol (e.g., NASDAQ:QQQ)", value="NASDAQ:QQQ")
interval = st.sidebar.selectbox("Interval", ["D","W","M"], index=0)
theme = st.sidebar.radio("Theme", ["dark","light"], index=0)
height = 600

# Parse ticker
ticker = (raw or "").strip().split(":")[-1].upper()

# Fetch data with robust fallbacks
df = pd.DataFrame()
last_err = None
try:
    import yfinance as yf
    try:
        df = yf.Ticker(ticker).history(period="2y", interval="1d", auto_adjust=False)
    except Exception as e:
        last_err = e
        df = pd.DataFrame()
    if df.empty:
        try:
            df = yf.download(ticker, period="2y", interval="1d", auto_adjust=False, progress=False)
        except Exception as e:
            last_err = e
            df = pd.DataFrame()
except Exception as e:
    last_err = e

# Fallback: try local CSV (data/ohlc/<EXCHANGE_SYMBOL>_D.csv or SYMBOL_D.csv)
if df.empty:
    try:
        import os
        candidates = []
        if ":" in raw:
            candidates.append(f"data/ohlc/{raw.replace(':','_')}_D.csv")
        candidates.append(f"data/ohlc/{ticker}_D.csv")
        for path in candidates:
            if os.path.exists(path):
                _df = pd.read_csv(path)
                if not _df.empty:
                    df = _df
                    break
    except Exception as _e:
        last_err = _e

if df.empty:
    st.warning(f"No data for {ticker}")
    if last_err:
        with st.expander("See error details"):
            st.code("".join(traceback.format_exception_only(type(last_err), last_err)))
    st.stop()

# Prepare candlestick series
df = df.reset_index()
# Standardize column names from yfinance (sometimes lowercase in newer builds)
cols = {c.lower(): c for c in df.columns}
def col(name): return cols.get(name, name.capitalize())
if "date" in cols:
    df["time"] = pd.to_datetime(df[col("date")]).dt.strftime("%Y-%m-%d")
elif "datetime" in cols:
    df["time"] = pd.to_datetime(df[col("datetime")]).dt.strftime("%Y-%m-%d")
else:
    # last resort
    if "Date" in df.columns:
        df["time"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    else:
        df["time"] = pd.to_datetime(df.index).strftime("%Y-%m-%d")

try:
    from streamlit_lightweight_charts import render as lwc_render
except Exception:
    from streamlit_lightweight_charts import renderLightweightCharts as lwc_render

series = [{
    "type": "Candlestick",
    "data": [
        {
            "time": str(row["time"]),
            "open": float(row.get(col("open"), row.get("Open"))),
            "high": float(row.get(col("high"), row.get("High"))),
            "low": float(row.get(col("low"), row.get("Low"))),
            "close": float(row.get(col("close"), row.get("Close"))),
        }
        for _, row in df.tail(260).iterrows()
    ],
}]

options = {"layout": {"background": {"type": "solid"}}}
lwc_render(series, options, theme=theme, height=height, key="native_lwc_v2")

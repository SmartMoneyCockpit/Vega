# app.py (drop-in replacement with fast rendering + indicator toggles)

from utils.prefs_bootstrap import prefs  # noqa: F401  (keeps any side-effects)
import streamlit as st
import pandas as pd
import numpy as np

from src.config_schema import load_config
from src.providers import MarketDataProvider
# (we keep these imports so nothing else breaks, but we won't rely on them for plotting)
# from src.indicators import apply_pack
# from src.charts import price_with_ma

import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Vega Cockpit", layout="wide")

# -------------------------
# Caching + data access
# -------------------------

@st.cache_data(show_spinner=False)
def get_config():
    return load_config("vega_config.yaml")

@st.cache_data(show_spinner=False, ttl=900)
def fetch(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    cfg = get_config()
    provider = MarketDataProvider(cfg.providers.order + ["public"])
    return provider._fetch(symbol, period, interval)

# -------------------------
# Indicator engines (cached)
# -------------------------

@st.cache_data(ttl=600, show_spinner=False)
def _prep_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize incoming OHLCV DataFrame:
    - tolerant to yfinance columns (Open/High/Low/Close/Volume),
      polygon-like (o/h/l/c/v), or already normalized.
    - ensure DateTimeIndex
    """
    if df is None or df.empty:
        return pd.DataFrame()

    d = df.copy()

    # Lowercase all columns to simplify mapping
    d.columns = [str(c).lower() for c in d.columns]

    # Common renames
    rename = {
        "time": "dt",
        "timestamp": "dt",
        "date": "dt",
        "ts": "dt",
        "o": "open", "h": "high", "l": "low", "c": "close",
        "v": "volume", "vol": "volume",
    }
    d = d.rename(columns=rename)

    # If typical yfinance keeps the index as DatetimeIndex and columns as lowercase already,
    # we should have open/high/low/close/volume.
    if "dt" in d.columns:
        d["dt"] = pd.to_datetime(d["dt"], utc=True, errors="coerce")
        d = d.dropna(subset=["dt"]).set_index("dt")
    elif not isinstance(d.index, pd.DatetimeIndex):
        # try to coerce index to datetime
        d.index = pd.to_datetime(d.index, utc=True, errors="coerce")

    # Ensure required columns exist
    for col in ("open", "high", "low", "close"):
        if col not in d.columns:
            raise ValueError(f"Missing column: {col}")
    if "volume" not in d.columns:
        d["volume"] = np.nan

    # Sort by time
    d = d.sort_index()
    return d

@st.cache_data(ttl=600, show_spinner=False)
def _ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False, min_periods=n).mean()

@st.cache_data(ttl=600, show_spinner=False)
def _sma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n).mean()

@st.cache_data(ttl=600, show_spinner=False)
def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(n).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(n).mean()
    rs = gain / loss.replace({0: np.nan})
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(method="bfill")

@st.cache_data(ttl=600, show_spinner=False)
def _macd(close: pd.Series, fast: int = 12, slow: int = 26, sig: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=sig, adjust=False).mean()
    return macd, signal

@st.cache_data(ttl=600, show_spinner=False)
def _bbands(close: pd.Series, n: int = 20, k: float = 2.0):
    ma = close.rolling(n).mean()
    std = close.rolling(n).std()
    upper = ma + k * std
    lower = ma - k * std
    return upper, ma, lower

@st.cache_data(ttl=600, show_spinner=False)
def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            (df["high"] - df["low"]).abs(),
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(n).mean()

# -------------------------
# UI controls + plotting
# -------------------------

def indicator_controls(prefix: str = "ind"):
    with st.expander("📈 Indicators & Performance", expanded=False):
        c1, c2 = st.columns(2)
        use_ema = c1.checkbox("EMA 10/20/50/200", True, key=f"{prefix}_ema")
        use_sma = c2.checkbox("SMA 50/200", False, key=f"{prefix}_sma")
        use_rsi = c1.checkbox("RSI (14)", True, key=f"{prefix}_rsi")
        use_macd = c2.checkbox("MACD (12,26,9)", False, key=f"{prefix}_macd")
        use_bb = c1.checkbox("Bollinger Bands (20,2)", False, key=f"{prefix}_bb")
        use_atr = c2.checkbox("ATR (14)", False, key=f"{prefix}_atr")

        st.divider()
        c3, c4 = st.columns(2)
        fast_mode = c3.toggle("⚡ Fast mode (downsample)", value=True, key=f"{prefix}_fast")
        max_bars = c4.slider("Bars to plot", 200, 4000, 1200, step=100, key=f"{prefix}_bars")

    return dict(
        ema=use_ema, sma=use_sma, rsi=use_rsi, macd=use_macd, bb=use_bb, atr=use_atr,
        fast=fast_mode, max_bars=max_bars
    )

def plot_chart(ticker: str, raw_df: pd.DataFrame, s):
    df = _prep_df(raw_df)
    if df.empty:
        st.error(f"No data for {ticker}")
        return

    # Downsample for speed
    if s["fast"]:
        df = df.tail(s["max_bars"])

    rows = 1
    row_heights = [0.62]
    if s["rsi"]:
        rows += 1; row_heights.append(0.19)
    if s["macd"] or s["atr"]:
        rows += 1; row_heights.append(0.19)

    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.02,
        row_heights=row_heights,
        specs=[[{"secondary_y": False}]] + [[{"secondary_y": False}] for _ in range(rows-1)]
    )

    # Price panel
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            name=ticker, showlegend=False
        ), row=1, col=1
    )

    # Overlays
    if s["ema"]:
        for n in (10, 20, 50, 200):
            fig.add_trace(go.Scatter(x=df.index, y=_ema(df["close"], n), mode="lines", name=f"EMA {n}"), row=1, col=1)
    if s["sma"]:
        for n in (50, 200):
            fig.add_trace(go.Scatter(x=df.index, y=_sma(df["close"], n), mode="lines", name=f"SMA {n}"), row=1, col=1)
    if s["bb"]:
        up, mid, lo = _bbands(df["close"], 20, 2.0)
        fig.add_trace(go.Scatter(x=df.index, y=up, mode="lines", name="BB Upper"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=mid, mode="lines", name="BB Mid"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=lo, mode="lines", name="BB Lower"), row=1, col=1)

    # RSI panel
    next_row = 2
    if s["rsi"]:
        r = _rsi(df["close"], 14)
        fig.add_trace(go.Scatter(x=df.index, y=r, mode="lines", name="RSI 14"), row=next_row, col=1)
        fig.add_hline(y=70, line=dict(dash="dot"), row=next_row, col=1)
        fig.add_hline(y=30, line=dict(dash="dot"), row=next_row, col=1)
        next_row += 1

    # MACD / ATR panel
    if s["macd"] or s["atr"]:
        if s["macd"]:
            m, sig = _macd(df["close"])
            fig.add_trace(go.Scatter(x=df.index, y=m, mode="lines", name="MACD"), row=next_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=sig, mode="lines", name="Signal"), row=next_row, col=1)
        if s["atr"]:
            a = _atr(df, 14)
            fig.add_trace(go.Bar(x=df.index, y=a, name="ATR 14"), row=next_row, col=1)

    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=720 if rows == 3 else (580 if rows == 2 else 440),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# App UI
# -------------------------

cfg = get_config()
st.title("Vega Cockpit — Core Fix Pack")

regions = []
if getattr(cfg.ui, "enable_us", False): regions.append("USA")
if getattr(cfg.ui, "enable_canada", False): regions.append("Canada")
if getattr(cfg.ui, "enable_mexico", False): regions.append("Mexico")
if getattr(cfg.ui, "enable_europe", False): regions.append("Europe")
if getattr(cfg.ui, "enable_apac", False): regions.append("APAC")

if not regions:
    st.warning("No regions enabled in config.")
    st.stop()

tabs = st.tabs(regions)

# --- Europe demo with fast-mode + indicator toggles ---
if "Europe" in regions:
    with tabs[regions.index("Europe")]:
        st.subheader("Europe Indices & ETFs")

        # One set of toggles for all charts rendered in this tab
        settings = indicator_controls(prefix="eu")

        # Build the symbol list from config (indices + ETFs)
        symbols = []
        for ex in cfg.exchanges:
            symbols += (ex.indices or []) + (ex.etfs or [])

        picked = st.multiselect("Symbols", symbols, default=symbols[:6])

        col1, col2 = st.columns(2)
        for i, s in enumerate(picked):
            try:
                df = fetch(s)  # cached
                target_col = col1 if i % 2 == 0 else col2
                if df is None or df.empty:
                    target_col.error(f"No data for {s}")
                    continue
                with target_col:
                    plot_chart(s, df, settings)
            except Exception as e:
                (col1 if i % 2 == 0 else col2).error(f"{s}: {e}")

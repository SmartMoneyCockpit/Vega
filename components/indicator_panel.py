# components/indicator_panel.py
from __future__ import annotations
import math
from dataclasses import dataclass
import streamlit as st
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# ---------- perf helpers ----------

@st.cache_data(ttl=600, show_spinner=False)
def _prep_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize incoming OHLCV DataFrame columns and set a DateTime index."""
    d = df.copy()
    # try common column names
    rename = {
        "time": "dt", "timestamp": "dt", "date": "dt", "ts": "dt",
        "o": "open", "h": "high", "l": "low", "c": "close",
        "v": "volume", "vol": "volume",
    }
    d = d.rename(columns=rename)
    if "dt" in d.columns:
        d["dt"] = pd.to_datetime(d["dt"], utc=True, errors="coerce")
        d = d.dropna(subset=["dt"]).set_index("dt")
    elif not isinstance(d.index, pd.DatetimeIndex):
        # last-ditch: try to datetime the index
        d.index = pd.to_datetime(d.index, utc=True, errors="coerce")

    # make sure required cols exist
    for col in ["open", "high", "low", "close"]:
        if col not in d.columns:
            raise ValueError(f"Missing column: {col}")
    if "volume" not in d.columns:
        d["volume"] = np.nan
    d = d.sort_index()
    return d

@st.cache_data(ttl=600, show_spinner=False)
def _rsi14(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(n).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(n).mean()
    rs = gain / loss.replace({0: np.nan})
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(method="bfill")

@st.cache_data(ttl=600, show_spinner=False)
def _ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False, min_periods=n).mean()

@st.cache_data(ttl=600, show_spinner=False)
def _sma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n).mean()

@st.cache_data(ttl=600, show_spinner=False)
def _macd(close: pd.Series, fast: int = 12, slow: int = 26, sig: int = 9) -> tuple[pd.Series, pd.Series]:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=sig, adjust=False).mean()
    return macd, signal

@st.cache_data(ttl=600, show_spinner=False)
def _bbands(close: pd.Series, n: int = 20, k: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
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

# ---------- UI + plotting ----------

@dataclass(frozen=True)
class IndicatorSettings:
    ema: bool = True
    sma: bool = False
    rsi: bool = True
    macd: bool = False
    bbands: bool = False
    atr: bool = False
    # perf
    fast_mode: bool = True        # downsample to last N bars
    max_bars: int = 1200          # only used if fast_mode

def indicator_controls(prefix: str = "ind") -> IndicatorSettings:
    with st.expander("📈 Indicators & Performance", expanded=False):
        c1, c2 = st.columns(2)
        ema = c1.checkbox("EMA 10/20/50/200", True, key=f"{prefix}_ema")
        sma = c2.checkbox("SMA 50/200", False, key=f"{prefix}_sma")
        rsi = c1.checkbox("RSI (14)", True, key=f"{prefix}_rsi")
        macd = c2.checkbox("MACD (12,26,9)", False, key=f"{prefix}_macd")
        bbands = c1.checkbox("Bollinger Bands (20,2)", False, key=f"{prefix}_bb")
        atr = c2.checkbox("ATR (14)", False, key=f"{prefix}_atr")

        st.divider()
        c3, c4 = st.columns(2)
        fast = c3.toggle("⚡ Fast mode (downsample)", value=True, key=f"{prefix}_fast")
        max_bars = c4.slider("Bars to plot", 200, 4000, 1200, step=100, key=f"{prefix}_bars")

    return IndicatorSettings(
        ema=ema, sma=sma, rsi=rsi, macd=macd, bbands=bbands, atr=atr,
        fast_mode=fast, max_bars=max_bars
    )

def plot_chart(ticker: str, raw_df: pd.DataFrame, settings: IndicatorSettings) -> None:
    df = _prep_df(raw_df)

    # downsample for speed
    if settings.fast_mode:
        df = df.tail(settings.max_bars)

    rows = 1
    row_heights = [0.62]
    if settings.rsi:
        rows += 1; row_heights.append(0.19)
    if settings.macd or settings.atr:
        rows += 1; row_heights.append(0.19)

    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.02,
        row_heights=row_heights,
        specs=[[{"secondary_y": False}]] + [[{"secondary_y": False}] for _ in range(rows-1)]
    )

    # Price panel
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name=f"{ticker}", showlegend=False
    ), row=1, col=1)

    # Overlays on price
    if settings.ema:
        for n in (10, 20, 50, 200):
            fig.add_trace(go.Scatter(x=df.index, y=_ema(df["close"], n), mode="lines", name=f"EMA {n}"), row=1, col=1)
    if settings.sma:
        for n in (50, 200):
            fig.add_trace(go.Scatter(x=df.index, y=_sma(df["close"], n), mode="lines", name=f"SMA {n}"), row=1, col=1)
    if settings.bbands:
        up, mid, lo = _bbands(df["close"], 20, 2.0)
        fig.add_trace(go.Scatter(x=df.index, y=up, mode="lines", name="BB Upper"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=mid, mode="lines", name="BB Mid"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=lo, mode="lines", name="BB Lower"), row=1, col=1)

    # RSI panel
    next_row = 2
    if settings.rsi:
        r = _rsi14(df["close"], 14)
        fig.add_trace(go.Scatter(x=df.index, y=r, mode="lines", name="RSI 14"), row=next_row, col=1)
        fig.add_hline(y=70, line=dict(dash="dot"), row=next_row, col=1)
        fig.add_hline(y=30, line=dict(dash="dot"), row=next_row, col=1)
        next_row += 1

    # MACD / ATR panel
    if settings.macd or settings.atr:
        if settings.macd:
            m, s = _macd(df["close"])
            fig.add_trace(go.Scatter(x=df.index, y=m, mode="lines", name="MACD"), row=next_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=s, mode="lines", name="Signal"), row=next_row, col=1)
        if settings.atr:
            a = _atr(df, 14)
            fig.add_trace(go.Bar(x=df.index, y=a, name="ATR 14"), row=next_row, col=1)

    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=720 if rows == 3 else (580 if rows == 2 else 440),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

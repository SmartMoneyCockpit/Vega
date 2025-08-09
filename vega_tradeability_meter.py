
# vega_tradeability_meter.py
# Simple Tradeability Meter — USA uses Polygon when POLYGON_KEY is set; others use Yahoo.
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Dict

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Optional deps
try:
    import yfinance as yf
except Exception:
    yf = None
try:
    import requests
except Exception:
    requests = None

st.set_page_config(page_title="Vega — Tradeability Meter", page_icon="🟢", layout="wide")

POLYGON_KEY = os.environ.get("POLYGON_KEY", "").strip()
REFRESH_TTL = 60 * 60

ETF_BASKETS: Dict[str, List[str]] = {
    "USA": ["XLY","XLP","XLE","XLF","XLV","XLI","XLB","XLK","XLC","XLRE","XLU"],
    "Canada": ["XIC.TO","XFN.TO","XEG.TO","XMA.TO","XIT.TO","XRE.TO","XHC.TO","XGD.TO","XUT.TO"],
    "Mexico": ["EWW"],
}

TIERS: List[Tuple[float, float, str, str]] = [
    (0.00, 0.20, "Red x3", "#ef4444"),
    (0.20, 0.35, "Red x2", "#ef4444"),
    (0.35, 0.45, "Red x1", "#ef4444"),
    (0.45, 0.55, "Yellow x3", "#f59e0b"),
    (0.55, 0.65, "Yellow x2", "#f59e0b"),
    (0.65, 0.72, "Yellow x1", "#f59e0b"),
    (0.72, 0.82, "Green x3", "#16a34a"),
    (0.82, 0.92, "Green x2", "#16a34a"),
    (0.92, 1.01, "Green x1", "#16a34a"),
]

def _norm_0_2(x: pd.Series, lo: float, hi: float) -> pd.Series:
    return ((x - lo) / (hi - lo)).clip(0, 1) * 2.0

@st.cache_data(ttl=REFRESH_TTL)
def fetch_prices(tickers: List[str], country: str) -> pd.DataFrame:
    use_polygon = bool(POLYGON_KEY) and country == "USA" and requests is not None
    if use_polygon:
        try:
            return _fetch_polygon_daily(tickers)
        except Exception as e:
            st.warning(f"Polygon fetch failed, falling back to Yahoo. Reason: {e}")
    if yf is None:
        raise RuntimeError("yfinance not available. Install yfinance or set POLYGON_KEY.")
    df = yf.download(tickers, period="6mo", interval="1d", auto_adjust=True, progress=False)["Close"]
    if isinstance(df, pd.Series):
        df = df.to_frame()
    return df.ffill().dropna(how="all")

def _fetch_polygon_daily(tickers: List[str]) -> pd.DataFrame:
    end = datetime.utcnow().date()
    start = end - timedelta(days=185)
    frames = []
    for t in tickers:
        url = (f"https://api.polygon.io/v2/aggs/ticker/{t}/range/1/day/{start}/{end}"
               f"?adjusted=true&sort=asc&limit=50000&apiKey={POLYGON_KEY}")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            continue
        ts = [pd.to_datetime(row["t"], unit="ms") for row in results]
        close = [row["c"] for row in results]
        frames.append(pd.Series(close, index=ts, name=t))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, axis=1)
    df.index.name = "Date"
    return df.ffill().dropna(how="all")

def compute_components(prices: pd.DataFrame) -> pd.DataFrame:
    px = prices.copy()
    comp = px.mean(axis=1)
    ma20, ma50 = comp.rolling(20).mean(), comp.rolling(50).mean()
    roc5, roc10, roc20 = comp.pct_change(5), comp.pct_change(10), comp.pct_change(20)

    mti_raw = ((comp > ma50).astype(float) * 0.8 +
               (comp > ma20).astype(float) * 0.4 +
               _norm_0_2(roc20, -0.08, 0.08) * 0.8)
    mti_01 = (mti_raw / 2.0).clip(0, 1)

    breadth = (px.gt(px.rolling(20).mean())).sum(axis=1) / max(1, px.shape[1])

    rt_raw = (_norm_0_2(roc5, -0.05, 0.05) * 0.4 +
              _norm_0_2(roc10, -0.07, 0.07) * 0.3 +
              _norm_0_2(roc20, -0.10, 0.10) * 0.3)
    rt_01 = (rt_raw / 2.0).clip(0, 1)

    score = (mti_01 + breadth + rt_01) / 3.0
    out = pd.DataFrame({"Composite": comp, "MTI_01": mti_01, "Breadth": breadth, "RT_01": rt_01, "Score": score})
    return out.dropna()

def tier_for(score: float) -> Tuple[str, str]:
    for lo, hi, label, color in TIERS:
        if lo <= score < hi:
            return label, color
    return "Green x1", "#16a34a"

def render_meter(score: float, label: str, color: str):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[1.0], y=[1], orientation='h', marker=dict(color="#1f2937"), showlegend=False))
    fig.add_trace(go.Bar(x=[max(0.01, score)], y=[1], orientation='h', marker=dict(color=color), showlegend=False))
    fig.update_yaxes(visible=False)
    fig.update_xaxes(range=[0,1], showticklabels=False, showgrid=False, zeroline=False)
    fig.update_layout(height=90, margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"### {label}")
    st.caption("Tradeability score (0–1). Greens imply ‘go’, reds imply ‘stand down’.")
    
def render_timing(s: pd.Series):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines"))
    fig.add_hline(y=0.5, line_dash="dot")
    fig.update_layout(height=180, margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.title("Tradeability Meter — USA | Canada | Mexico")
tabs = st.tabs(["USA","Canada","Mexico"])
for tab, country in zip(tabs, ["USA","Canada","Mexico"]):
    with tab:
        try:
            px = fetch_prices(ETF_BASKETS[country], country)
            comp = compute_components(px)
            latest = comp.iloc[-1]
            label, color = tier_for(float(latest["Score"]))
            render_meter(float(latest["Score"]), label, color)
            render_timing(comp["Score"].tail(120))
            st.caption("Source: Polygon" if (country=="USA" and POLYGON_KEY) else "Source: Yahoo Finance")
        except Exception as e:
            st.error(f"Data error for {country}: {e}")

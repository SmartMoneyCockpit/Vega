
# components/metric_trends.py
from __future__ import annotations
import os, pandas as pd, numpy as np
import plotly.graph_objects as go
import streamlit as st

VST_BANDS = {"green": (1.2, 2.0), "yellow": (0.9, 1.19), "red": (0.0, 0.89)}

def _ma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n, min_periods=1).mean()

def _load_series(symbol: str, metric: str):
    """
    Expected CSV locations under vault/timeseries/vv/: 
      - VST:          {SYMBOL}.csv with columns: date,vst
      - EPS:          {SYMBOL}_eps.csv with columns: date,eps
      - growth:       {SYMBOL}_growth.csv with columns: date,growth
      - sales_growth: {SYMBOL}_sales_growth.csv with columns: date,sales_growth
    Will resample to weekly (Fri) when frequency > weekly.
    """
    base = os.path.join("vault","timeseries","vv")
    # map metric to file suffix
    fn = {
        "vst": f"{symbol.upper()}.csv",
        "eps": f"{symbol.upper()}_eps.csv",
        "growth": f"{symbol.upper()}_growth.csv",
        "sales_growth": f"{symbol.upper()}_sales_growth.csv",
    }.get(metric, None)
    if not fn:
        return None
    path = os.path.join(base, fn)
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        df.columns = [c.lower() for c in df.columns]
        if "date" not in df.columns or metric not in df.columns:
            return None
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        # Resample to weekly if high frequency
        if df["date"].diff().dt.days.median() < 5:
            df = (df.set_index("date")
                    .resample("W-FRI")
                    .last()
                    .reset_index())
        return df[["date", metric]].copy()
    except Exception:
        return None

def render_metric_trend(symbol: str, metric: str, lookback_weeks: int = 26):
    metric = metric.lower()
    assert metric in {"vst", "eps", "growth", "sales_growth"}
    df = _load_series(symbol, metric)
    if df is None or df.empty:
        pretty = {"vst":"VST","eps":"EPS","growth":"Earnings Growth","sales_growth":"Sales Growth"}[metric]
        st.info(f"No {pretty} timeseries found for **{symbol}**. Place CSV at `vault/timeseries/vv/{symbol}_{metric if metric!='vst' else ''}.csv`.")
        return
    df = df.tail(lookback_weeks).copy()
    df["ma4"] = _ma(df[metric], 4)
    df["ma12"] = _ma(df[metric], 12)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df[metric], mode="lines", name=metric.upper()))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ma4"], mode="lines", name="MA 4w"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ma12"], mode="lines", name="MA 12w"))

    if metric == "vst":
        for label, (lo, hi) in VST_BANDS.items():
            fig.add_shape(
                type="rect", xref="paper", yref="y",
                x0=0, x1=1, y0=lo, y1=hi,
                fillcolor={"green":"rgba(34,197,94,0.09)","yellow":"rgba(234,179,8,0.10)","red":"rgba(239,68,68,0.08)"}[label],
                line_width=0, layer="below"
            )
        cross = (np.sign(df["ma4"] - df["ma12"]) != np.sign((df["ma4"] - df["ma12"]).shift(1))).fillna(False)
        for _, row in df[cross].iterrows():
            fig.add_annotation(x=row["date"], y=row[metric], text="flip", showarrow=True, yshift=10)

    titles = {"vst":"VST (0–2)","eps":"Earnings Per Share","growth":"Earnings Growth (%)","sales_growth":"Sales Growth (%)"}
    fig.update_layout(
        title=f"{titles[metric]} — {symbol} (26w)",
        xaxis_title="Date",
        yaxis_title=titles[metric],
        height=280, margin=dict(l=10,r=10,t=40,b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

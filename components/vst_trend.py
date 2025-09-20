
# components/vst_trend.py
from __future__ import annotations
import os, pandas as pd, numpy as np
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

BANDS = {"green": (1.2, 2.0), "yellow": (0.9, 1.19), "red": (0.0, 0.89)}

def _ma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n, min_periods=1).mean()

def load_vst_series(symbol: str) -> pd.DataFrame | None:
    """Expect CSV at vault/timeseries/vv/{symbol}.csv with columns: date, vst"""
    path = os.path.join("vault","timeseries","vv", f"{symbol.upper()}.csv")
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        if "date" not in df.columns or "vst" not in df.columns:
            return None
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        # Weekly sampling assumed; otherwise resample to weekly on Friday
        if df["date"].diff().dt.days.median() < 5:
            df = (df.set_index("date")
                    .resample("W-FRI")
                    .last()
                    .reset_index())
        return df
    except Exception:
        return None

def render_vst_trend(symbol: str, lookback_weeks: int = 26):
    df = load_vst_series(symbol)
    if df is None or df.empty:
        st.info(f"No VST timeseries found for **{symbol}**. Place a CSV at `vault/timeseries/vv/{symbol}.csv` with columns `date,vst`.")
        return
    df = df.tail(lookback_weeks).copy()
    df["ma4"] = _ma(df["vst"], 4)
    df["ma12"] = _ma(df["vst"], 12)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["vst"], mode="lines", name="VST"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ma4"], mode="lines", name="MA 4w"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ma12"], mode="lines", name="MA 12w"))

    # Background bands
    for label, (lo, hi) in BANDS.items():
        fig.add_shape(
            type="rect",
            xref="paper", yref="y",
            x0=0, x1=1, y0=lo, y1=hi,
            fillcolor={"green":"rgba(34,197,94,0.09)","yellow":"rgba(234,179,8,0.10)","red":"rgba(239,68,68,0.08)"}[label],
            line_width=0,
            layer="below"
        )

    # Annotations for flips (crosses of ma4 vs ma12)
    cross = (np.sign(df["ma4"] - df["ma12"]) != np.sign((df["ma4"] - df["ma12"]).shift(1))).fillna(False)
    for i, row in df[cross].iterrows():
        fig.add_annotation(x=row["date"], y=row["vst"], text="flip", showarrow=True, yshift=10)

    fig.update_layout(
        title=f"VST Trend — {symbol} (26w)",
        xaxis_title="Date",
        yaxis_title="VST (0–2)",
        height=280,
        margin=dict(l=10,r=10,t=40,b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

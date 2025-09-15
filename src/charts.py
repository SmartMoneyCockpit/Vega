from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

def price_with_ma(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"], name="OHLC"))
    for col in [c for c in df.columns if c.startswith(("ema_","sma_","hma_","gma_"))]:
        fig.add_trace(go.Scatter(x=df["date"], y=df[col], name=col, mode="lines"))
    fig.update_layout(title=title, xaxis_rangeslider_visible=False, height=520)
    return fig

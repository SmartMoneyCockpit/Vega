import numpy as np
import pandas as pd

def ema(series, n):  # simple, stable EMA
    return series.ewm(span=n, adjust=False).mean()

def atr(df, n=14):
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([
        (h - l),
        (h - c.shift(1)).abs(),
        (l - c.shift(1)).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def rs_against(df_stock, df_bench, lookback=20):
    # ratio of cumulative returns over lookback
    s_ret = df_stock["close"].pct_change().tail(lookback).add(1).prod()
    b_ret = df_bench["close"].pct_change().tail(lookback).add(1).prod()
    return (s_ret / b_ret) if b_ret else 0.0

def rr_ok(entry, stop, target, rr_min=3.0):
    risk = entry - stop
    reward = target - entry
    return (risk > 0) and (reward / risk >= rr_min)

def build_df(bars):
    return pd.DataFrame([{
        "t": b["t"], "open": b["o"], "high": b["h"], "low": b["l"], "close": b["c"], "vol": b["v"]
    } for b in bars])

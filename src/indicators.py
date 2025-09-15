from __future__ import annotations
import pandas as pd
import numpy as np

def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/length, adjust=False).mean()
    roll_down = down.ewm(alpha=1/length, adjust=False).mean()
    rs = roll_up / roll_down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()

def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length).mean()

def hull(series: pd.Series, length: int = 55) -> pd.Series:
    half = int(length/2)
    sqrt_len = int(np.sqrt(length))
    wma = lambda s, l: s.rolling(l).apply(lambda x: np.dot(x, np.arange(1, l+1))/np.arange(1, l+1).sum(), raw=True)
    return wma(2*wma(series, half) - wma(series, length), sqrt_len)

def apply_pack(df: pd.DataFrame, pack: dict) -> pd.DataFrame:
    close = df["close"].astype(float)
    if (r := pack.get("rsi")):
        df[f"rsi_{r.get('length',14)}"] = rsi(close, r.get("length",14))
    for e in pack.get("ema", []) or []:
        df[f"ema_{e}"] = ema(close, e)
    for s in pack.get("sma", []) or []:
        df[f"sma_{s}"] = sma(close, s)
    if (h := pack.get("hull")):
        df[f"hma_{h.get('length',55)}"] = hull(close, h.get("length",55))
    g = pack.get("guppy") or {}
    for e in (g.get("fast") or []):
        df[f"gma_f_{e}"] = ema(close, e)
    for e in (g.get("slow") or []):
        df[f"gma_s_{e}"] = ema(close, e)
    return df

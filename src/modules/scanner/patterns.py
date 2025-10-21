import numpy as np, pandas as pd
from typing import Tuple

def pct_change_series(prices: pd.Series) -> pd.Series:
    return prices.pct_change().fillna(0.0)

def _linreg(x: np.ndarray, y: np.ndarray) -> Tuple[float,float]:
    x = np.asarray(x); y = np.asarray(y)
    A = np.vstack([x, np.ones(len(x))]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(slope), float(intercept)

def rising_wedge(prices: pd.Series, lookback: int = 60) -> bool:
    if len(prices) < lookback+5: return False
    s = prices.iloc[-lookback:]
    highs = s.rolling(5, center=True).max().dropna()
    lows  = s.rolling(5, center=True).min().dropna()
    common = highs.index.intersection(lows.index)
    highs = highs.loc[common]; lows = lows.loc[common]
    if len(highs)<10 or len(lows)<10: return False
    x = np.arange(len(common))
    us, _ = _linreg(x, highs.values)
    ls, _ = _linreg(x, lows.values)
    narrowing = (us > 0) and (ls > 0) and (us < ls)
    recent_loss = s.pct_change(10).iloc[-1] < 0
    return bool(narrowing and recent_loss)

def falling_wedge(prices: pd.Series, lookback: int = 60) -> bool:
    if len(prices) < lookback+5: return False
    s = prices.iloc[-lookback:]
    highs = s.rolling(5, center=True).max().dropna()
    lows  = s.rolling(5, center=True).min().dropna()
    common = highs.index.intersection(lows.index)
    highs = highs.loc[common]; lows = lows.loc[common]
    if len(highs)<10 or len(lows)<10: return False
    x = np.arange(len(common))
    us, _ = _linreg(x, highs.values)
    ls, _ = _linreg(x, lows.values)
    narrowing = (us < 0) and (ls < 0) and (us > ls)
    recent_gain = s.pct_change(10).iloc[-1] > 0
    return bool(narrowing and recent_gain)

def bearish_setup_score(prices: pd.Series, window: int = 20) -> float:
    if len(prices) < window+5: return 0.0
    s = prices.copy()
    ma = s.rolling(window).mean()
    below = float((s.iloc[-1] < ma.iloc[-1]))
    mom = float((s.iloc[-1] / s.iloc[-window]) - 1.0 < 0)
    bounce = float((s.iloc[-1] < s.rolling(3).max().iloc[-1]*0.98))
    score = 100.0 * (0.5*below + 0.35*mom + 0.15*bounce)
    return round(score,2)

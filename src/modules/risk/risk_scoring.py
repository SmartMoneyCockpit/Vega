"""
Vega Risk & Return Scoring Engine
Computes: Sharpe, Sortino, Volatility, Beta vs Benchmark, Max Drawdown, CVaR, CAGR,
Rolling metrics, and a composite 0–100 score with adjustable weights.
"""
from __future__ import annotations
import numpy as np, pandas as pd, typing as t

def _to_returns(prices: pd.Series, freq_per_year: int = 252) -> pd.Series:
    returns = prices.pct_change().dropna()
    return returns

def sharpe(returns: pd.Series, rf: float = 0.0, freq_per_year: int = 252) -> float:
    if returns.empty: return np.nan
    ex = returns - rf/freq_per_year
    mu, sig = ex.mean(), ex.std()
    return float(np.sqrt(freq_per_year) * (mu / sig)) if sig != 0 else np.nan

def sortino(returns: pd.Series, rf: float = 0.0, freq_per_year: int = 252) -> float:
    if returns.empty: return np.nan
    downside = returns.copy()
    downside[downside > 0] = 0
    dd = downside.std()
    ex = returns - rf/freq_per_year
    mu = ex.mean()
    return float(np.sqrt(freq_per_year) * (mu / dd)) if dd != 0 else np.nan

def volatility(returns: pd.Series, freq_per_year: int = 252) -> float:
    return float(returns.std() * np.sqrt(freq_per_year)) if not returns.empty else np.nan

def max_drawdown(prices: pd.Series) -> float:
    if prices.empty: return np.nan
    roll_max = prices.cummax()
    drawdown = prices/roll_max - 1.0
    return float(drawdown.min())

def beta_vs(prices: pd.Series, bench_prices: pd.Series) -> float:
    r = prices.pct_change().dropna()
    b = bench_prices.pct_change().dropna()
    # align
    df = pd.concat([r,b], axis=1).dropna()
    if df.shape[0] < 5: return np.nan
    cov = np.cov(df.iloc[:,0], df.iloc[:,1])[0,1]
    var_b = np.var(df.iloc[:,1])
    return float(cov/var_b) if var_b != 0 else np.nan

def cagr(prices: pd.Series, freq_per_year: int = 252) -> float:
    if prices.empty or prices.iloc[0] <= 0: return np.nan
    n = len(prices)
    years = n/freq_per_year
    return float((prices.iloc[-1]/prices.iloc[0])**(1/years) - 1) if years>0 else np.nan

def cvar(returns: pd.Series, alpha: float = 0.05) -> float:
    if returns.empty: return np.nan
    q = returns.quantile(alpha)
    tail = returns[returns <= q]
    return float(tail.mean()) if not tail.empty else np.nan

def composite_score(metrics: dict, weights: dict|None=None) -> float:
    # normalize a few key metrics to 0..100-ish
    w = weights or {
        "sharpe": 0.25, "sortino": 0.2, "volatility": 0.1,
        "max_drawdown": 0.15, "cvar": 0.1, "cagr": 0.2
    }
    s = metrics.get("sharpe", np.nan)
    so= metrics.get("sortino", np.nan)
    vol= metrics.get("volatility", np.nan)
    mdd= metrics.get("max_drawdown", np.nan) # negative
    cv = metrics.get("cvar", np.nan)         # negative
    cg = metrics.get("cagr", np.nan)

    # scale helpers
    def clamp(x, lo, hi):
        return max(lo, min(hi, x))

    # Sharpe scale: 0 at 0, 100 at 3+
    s100  = 100*clamp((s or 0)/3.0, 0, 1)
    so100 = 100*clamp((so or 0)/4.0, 0, 1)
    # Lower vol better up to a point: map 60% vol -> 0, 10% vol -> 100
    v = abs(vol or 0)
    vol100 = 100*clamp((0.60 - v)/(0.60-0.10), 0, 1)

    # MDD and CVaR are negative; less negative is better
    m = mdd or 0
    mdd100 = 100*clamp((m + 0.6)/(0.6), 0, 1)  # -60% -> 0, 0% -> 100
    c = cv or 0
    cvar100 = 100*clamp((c + 0.1)/0.1, 0, 1)   # -10% -> 0, 0% -> 100

    # CAGR: 0 -> 0, 25%+ -> 100
    cg100 = 100*clamp((cg or 0)/0.25, 0, 1)

    score = (
        w["sharpe"]*s100 + w["sortino"]*so100 + w["volatility"]*vol100 +
        w["max_drawdown"]*mdd100 + w["cvar"]*cvar100 + w["cagr"]*cg100
    )
    return float(round(score, 2))

def full_report(prices: pd.Series, bench_prices: pd.Series|None=None, rf: float=0.0, freq_per_year: int=252) -> dict:
    r = _to_returns(prices, freq_per_year=freq_per_year)
    metrics = {
        "sharpe": sharpe(r, rf, freq_per_year),
        "sortino": sortino(r, rf, freq_per_year),
        "volatility": volatility(r, freq_per_year),
        "max_drawdown": max_drawdown(prices),
        "cvar": cvar(r, alpha=0.05),
        "cagr": cagr(prices, freq_per_year),
    }
    if bench_prices is not None:
        metrics["beta"] = beta_vs(prices, bench_prices)
    metrics["score"] = composite_score(metrics)
    return metrics

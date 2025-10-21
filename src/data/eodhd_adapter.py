"""
EODHD adapter for Vega Cockpit
- Pulls end-of-day (or delayed) prices from EODHD REST API.
- Falls back to cached CSV if provided.
"""
from __future__ import annotations
import os, time, json, math, typing as t
from dataclasses import dataclass
import requests
import pandas as pd

EODHD_API_TOKEN = os.getenv("EODHD_API_TOKEN", "").strip()
EODHD_BASE_URL  = os.getenv("EODHD_BASE_URL", "https://eodhd.com/api").rstrip("/")

class EODHDError(RuntimeError):
    pass

def _check_token():
    if not EODHD_API_TOKEN:
        raise EODHDError("EODHD_API_TOKEN not set")

def _get(url: str, params: dict) -> dict:
    # simple GET with retries
    for i in range(3):
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                # EODHD returns JSON for fundamental endpoints, CSV for price endpoints
                ctype = r.headers.get("Content-Type","")
                if "application/json" in ctype:
                    return r.json()
                # if CSV, we'll parse where needed
                return {"_raw": r.text}
            err = f"HTTP {r.status_code} - {r.text[:180]}"
            time.sleep(0.8*(i+1))
        except Exception as ex:
            err = str(ex)
            time.sleep(0.8*(i+1))
    raise EODHDError(err)

def get_eod_prices_csv(symbol: str, period: str = "1y", exchange: str|None=None) -> pd.DataFrame:
    """Fetch daily bars as a DataFrame with columns: date, open, high, low, close, volume"""
    _check_token()
    sym = symbol if exchange is None else f"{symbol}.{exchange}"
    url = f"{EODHD_BASE_URL}/eod/{sym}"
    params = {"api_token": EODHD_API_TOKEN, "fmt": "csv", "period": "d"}
    # Note: 'period' like 1y is a convenience; we filter after download if needed.
    resp = _get(url, params)
    raw = resp.get("_raw","")
    if not raw:
        raise EODHDError("Empty CSV response")
    from io import StringIO
    df = pd.read_csv(StringIO(raw))
    # ensure columns
    cols = {c.lower(): c for c in df.columns}
    rename = {cols.get("date","date"): "date",
              cols.get("open","open"): "open",
              cols.get("high","high"): "high",
              cols.get("low","low"): "low",
              cols.get("close","close"): "close",
              cols.get("adjusted_close","adjusted_close"): "adjusted_close",
              cols.get("volume","volume"): "volume"}
    df = df.rename(columns=rename)
    # keep required
    keep = [c for c in ["date","open","high","low","close","adjusted_close","volume"] if c in df.columns]
    df = df[keep].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.sort_values("date").reset_index(drop=True)
    # optional trim by 'period'
    # crude parse like '1y','6m','3m','1m','5y'
    if isinstance(period, str) and period.endswith(("y","m")):
        n = int(period[:-1])
        unit = period[-1]
        if unit == "y":
            cutoff = df["date"].max() - pd.DateOffset(years=n)
        else:
            cutoff = df["date"].max() - pd.DateOffset(months=n)
        df = df[df["date"] >= cutoff].reset_index(drop=True)
    return df

def latest_close(symbol: str, exchange: str|None=None) -> float|None:
    df = get_eod_prices_csv(symbol, period="6m", exchange=exchange)
    if df.empty: return None
    col = "adjusted_close" if "adjusted_close" in df.columns else "close"
    return float(df[col].iloc[-1])



# --- CSV fallback cache -------------------------------------------------------
from pathlib import Path
CACHE_DIR = Path(__file__).resolve().parents[2] / "data_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _cache_path(symbol: str, exchange: str|None):
    sym = symbol if exchange is None else f"{symbol}.{exchange}"
    return CACHE_DIR / f"eod_{sym.replace(':','_').replace('/','_')}.csv"

def _get_prices_live(symbol: str, period: str = "1y", exchange: str|None=None) -> pd.DataFrame:
    # This function mirrors the original fetch logic.
    _check_token()
    sym = symbol if exchange is None else f"{symbol}.{exchange}"
    url = f"{EODHD_BASE_URL}/eod/{sym}"
    params = {"api_token": EODHD_API_TOKEN, "fmt": "csv", "period": "d"}
    resp = _get(url, params)
    raw = resp.get("_raw","")
    if not raw:
        raise EODHDError("Empty CSV response")
    from io import StringIO
    df = pd.read_csv(StringIO(raw))
    cols = {c.lower(): c for c in df.columns}
    rename = {cols.get("date","date"): "date",
              cols.get("open","open"): "open",
              cols.get("high","high"): "high",
              cols.get("low","low"): "low",
              cols.get("close","close"): "close",
              cols.get("adjusted_close","adjusted_close"): "adjusted_close",
              cols.get("volume","volume"): "volume"}
    df = df.rename(columns=rename)
    keep = [c for c in ["date","open","high","low","close","adjusted_close","volume"] if c in df.columns]
    df = df[keep].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.sort_values("date").reset_index(drop=True)
    # trim by period
    if isinstance(period, str) and period.endswith(("y","m")):
        n = int(period[:-1])
        unit = period[-1]
        cutoff = df["date"].max() - (pd.DateOffset(years=n) if unit=="y" else pd.DateOffset(months=n))
        df = df[df["date"] >= cutoff].reset_index(drop=True)
    return df

def get_eod_prices_csv(symbol: str, period: str = "1y", exchange: str|None=None) -> pd.DataFrame:
    try:
        df = _get_prices_live(symbol, period=period, exchange=exchange)
        # save cache
        try:
            df.to_csv(_cache_path(symbol, exchange), index=False)
        except Exception:
            pass
        return df
    except Exception:
        # fallback to cache
        cp = _cache_path(symbol, exchange)
        if cp.exists():
            df = pd.read_csv(cp)
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            df = df.sort_values("date").reset_index(drop=True)
            if isinstance(period, str) and period.endswith(("y","m")):
                n = int(period[:-1]); unit = period[-1]
                cutoff = df["date"].max() - (pd.DateOffset(years=n) if unit=="y" else pd.DateOffset(months=n))
                df = df[df["date"] >= cutoff].reset_index(drop=True)
            return df
        raise

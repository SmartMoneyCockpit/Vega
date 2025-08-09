# price_client.py — multi-provider quotes (polygon, yfinance) + throttling + cache
import os, time, requests
import streamlit as st

PROVIDERS   = [p.strip().lower() for p in os.getenv("PRICE_PROVIDERS","polygon,yfinance").split(",") if p.strip()]
POLYGON_KEY = os.getenv("POLYGON_KEY","")
_THROTTLE_SEC = float(os.getenv("PRICE_THROTTLE_SEC","0.6"))
_last_call = {}  # (provider,symbol)->timestamp

def _throttle(provider: str, sym: str):
    k = (provider, sym.upper())
    now = time.time()
    if k in _last_call:
        wait = _THROTTLE_SEC - (now - _last_call[k])
        if wait > 0: time.sleep(wait)
    _last_call[k] = time.time()

def _polygon(sym: str):
    if "." in sym or not POLYGON_KEY: return None
    _throttle("polygon", sym)
    try:
        r = requests.get(f"https://api.polygon.io/v2/last/trade/{sym.upper()}?apiKey={POLYGON_KEY}", timeout=6)
        if r.status_code != 200: return None
        p = (r.json() or {}).get("results",{}).get("p")
        return float(p) if p is not None else None
    except: return None

@st.cache_data(show_spinner=False, ttl=15)
def _yf_cached(sym_upper: str):
    try:
        import yfinance as yf
        t = yf.Ticker(sym_upper)
        fi = getattr(t, "fast_info", None)
        if fi:
            p = getattr(fi, "last_price", None) or getattr(fi, "last_trade", None) or (fi.get("last_price") if isinstance(fi, dict) else None)
            if p: return float(p)
        # fallback: info dict lastPrice
        info = getattr(t, "info", {}) or {}
        p = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("lastPrice")
        return float(p) if p else None
    except Exception:
        return None

def _yfinance(sym: str):
    _throttle("yfinance", sym)
    return _yf_cached(sym.upper())

_PROVIDER_FUN = {"polygon": _polygon, "yfinance": _yfinance}

def get_price(symbol: str):
    if not symbol: return None
    for p in PROVIDERS:
        f = _PROVIDER_FUN.get(p)
        if not f: continue
        price = f(symbol)
        if price is not None: return price
    return None

import os
import datetime as dt
import pytz
import requests
import yfinance as yf

# --- Robust timezone with fallback ---
tz_pref = os.getenv("TZ_PREF") or "America/Los_Angeles"
try:
    PT = pytz.timezone(tz_pref)
except pytz.UnknownTimeZoneError:
    PT = pytz.timezone("UTC")

def now_pt():
    return dt.datetime.now(PT)

def in_us_window(ts=None):
    """US trading window 06:00–14:00 PT Mon–Fri"""
    ts = ts or now_pt()
    return ts.weekday() <= 4 and 6 <= ts.hour < 14

def in_apac_window(ts=None):
    """APAC window 18:00–22:00 PT daily"""
    ts = ts or now_pt()
    return 18 <= ts.hour < 22

def last_price(ticker):
    df = yf.download(ticker, period="1d", interval="1m", progress=False, auto_adjust=False)
    if df.empty:
        return None
    return float(df["Close"].dropna().iloc[-1])

def prev_close(ticker):
    df = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
    if df.empty or len(df["Close"]) < 2:
        return None
    return float(df["Close"].iloc[-2])

def pct_from_prev_close(ticker):
    p0 = prev_close(ticker)
    p = last_price(ticker)
    if p0 is None or p is None:
        return None
    return (p / p0 - 1.0) * 100.0

def fmt_num(x, n=2):
    return "n/a" if x is None else f"{x:.{n}f}"

# --- Optional: Gist logging for alert history ---
def fetch_gist(gist_id, token):
    try:
        r = requests.get(

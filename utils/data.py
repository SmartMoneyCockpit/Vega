# utils/data.py
import datetime as dt
import yfinance as yf
import pandas as pd

def _hist(ticker, period="6mo", interval="1d"):
    return yf.download(ticker, period=period, interval=interval, progress=False)

def get_price(ticker: str) -> float:
    df = _hist(ticker, period="5d", interval="1m")
    if df.empty: raise RuntimeError(f"No data for {ticker}")
    return float(df["Close"].dropna().iloc[-1])

def get_close(ticker: str) -> float:
    df = _hist(ticker, period="3mo", interval="1d")
    if df.empty: raise RuntimeError(f"No data for {ticker}")
    return float(df["Close"].dropna().iloc[-1])

def get_breakout_close(ticker: str, lookback_days: int = 20, confirm_breadth: bool = False) -> bool:
    df = _hist(ticker, period="6mo", interval="1d").dropna()
    if len(df) < lookback_days + 2: return False
    last_close = df["Close"].iloc[-1]
    prior_max = df["High"].iloc[-(lookback_days+1):-1].max()
    cond = last_close > prior_max
    if confirm_breadth:
        # simple breadth proxy: SPY above 50DMA
        spy = _hist("SPY", period="6mo", interval="1d").dropna()
        ma50 = spy["Close"].rolling(50).mean().iloc[-1]
        cond = cond and (spy["Close"].iloc[-1] > ma50)
    return bool(cond)

def get_vix() -> float:
    return get_close("^VIX")

def news_since(lookback="1h", tickers=None, keywords=None):
    # Minimal stub; returns empty (you can wire a real feed later).
    return []

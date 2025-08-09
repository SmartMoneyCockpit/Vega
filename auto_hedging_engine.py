# auto_hedging_engine.py — SPY/QQQ/IWM risk scoring + SPXU/SQQQ/RWM triggers
import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import streamlit as st

POLY_KEY = os.getenv("POLYGON_API_KEY") or os.getenv("POLYGON_KEY")

def _poly_url(ticker, mult, span, start, end):
    return (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{mult}/{span}/"
        f"{start.date()}/{end.date()}?adjusted=true&sort=asc&limit=50000&apiKey={POLY_KEY}"
    )

@st.cache_data(show_spinner=False, ttl=60)
def fetch_polygon(ticker: str, tf: str):
    if not POLY_KEY:
        raise RuntimeError("Missing Polygon API key (set POLYGON_API_KEY or POLYGON_KEY in Render).")
    ticker = ticker.upper().strip()
    now = datetime.now(timezone.utc)

    if tf == "1h":
        mult, span = 1, "hour"
        start = now - timedelta(days=60)
    else:
        mult, span = 1, "day"
        start = now - relativedelta(months=9)

    url = _poly_url(ticker, mult, span, start, now)
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json().get("results", [])
    if not data:
        raise RuntimeError(f"No data for {ticker} ({tf}).")

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["t"], unit="ms", utc=True)
    df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"}, inplace=True)
    return df.set_index("date")[["open","high","low","close","volume"]].sort_index()

def atr(df, n=14):
    h,l,c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h-l), (h-pc).abs(), (l-pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def trend_liquidity_vol(df):
    sma20 = df["close"].rolling(20).mean()
    sma50 = df["close"].rolling(50).mean()
    slope = (sma50 - sma50.shift(10))/10
    trend_bear = (sma20.iloc[-1] < sma50.iloc[-1]) and (slope.iloc[-1] < 0)
    vol_pct = float(df["volume"].rank(pct=True).iloc[-1])
    atr14 = atr(df, 14)
    atr_pct = float((atr14 / df["close"]).iloc[-1])
    if atr_pct < 0.015: regime = "Calm"
    elif atr_pct < 0.03: regime = "Normal"
    elif atr_pct < 0.06: regime = "Elevated"
    else: regime = "Wild"
    return dict(
        trend_bear=bool(trend_bear),
        slope=float(slope.iloc[-1]),
        vol_pct=vol_pct,
        atr_pct=atr_pct,
        regime=regime,
        last=float(df['close'].iloc[-1]),
        last_ts=df.index[-1].isoformat(),
        sma20=float(sma20.iloc[-1]) if not np.isnan(sma20.iloc[-1]) else None,
        sma50=float(sma50.iloc[-1]) if not np.isnan(sma50.iloc[-1]) else None,
    )

def severity(scorebits):
    sev = 0
    if scorebits["trend_bear"]: sev += 1
    if scorebits["regime"] in ("Elevated","Wild"): sev += 1
    if scorebits["vol_pct"] >= 0.6: sev += 1
    return sev

def hedge_sizing(sev):
    return {0:0, 1:0.1, 2:0.25, 3:0.4}[sev]

def trigger_price(last, sma20, atr_pct, inverse_multiple):
    if sma20 is None or atr_pct is None: 
        return None
    drop = (0.5 * atr_pct) * last
    idx_trigger = max(last - drop, sma20)
    return round(idx_trigger, 2)

MAP = {
    "SPY": {"inverse":"SPXU", "multiple": -3},
    "QQQ": {"inverse":"SQQQ", "multiple": -3},
    "IWM": {"inverse":"RWM",  "multiple": -1},
}

def run():
    st.header("Auto-Hedging Engine")
    st.caption("Reads SPY/QQQ/IWM, scores risk, and suggests SPXU/SQQQ/RWM hedge entries and sizing.")
    tf = st.selectbox("Timeframe for regime scoring", ["Daily","1h"], index=0)
    cols = st.columns(3)
    indices = ["SPY","QQQ","IWM"]
    results = {}
    for i, sym in enumerate(indices):
        with cols[i]:
            try:
                df = fetch_polygon(sym, "1h" if tf=="1h" else "Daily")
                bits = trend_liquidity_vol(df)
                sev = severity(bits)
                size = hedge_sizing(sev)
                trig = trigger_price(bits["last"], bits["sma20"], bits["atr_pct"], MAP[sym]["multiple"])
                st.subheader(sym)
                st.metric("Last", f"{bits['last']:.2f}")
                st.metric("Regime", bits["regime"])
                st.metric("Trend bearish?", "Yes" if bits["trend_bear"] else "No")
                st.metric("ATR%", f"{bits['atr_pct']*100:.2f}%")
                st.metric("Liquidity pct", f"{bits['vol_pct']*100:.0f}%")
                st.metric("Severity (0-3)", sev)
                st.metric("Suggested hedge size", f"{int(size*100)}%")
                inv = MAP[sym]["inverse"]
                st.write(f"**Hedge vehicle**: {inv}")
                if trig:
                    st.info(f"Index alert: Enter hedge if **{sym}** closes < **{trig}** (≈ half ATR% below price/20SMA).")
                else:
                    st.info("Trigger pending (need more data for SMA/ATR).")
                results[sym] = dict(
                    index=sym,
                    inverse=inv,
                    last=bits["last"],
                    regime=bits["regime"],
                    trend_bear=bits["trend_bear"],
                    atr_pct=bits["atr_pct"],
                    vol_pct=bits["vol_pct"],
                    severity=sev,
                    hedge_size_pct=int(size*100),
                    index_trigger=trig,
                    ts=bits["last_ts"],
                    timeframe=tf,
                )
            except Exception as e:
                st.error(f"{sym}: {e}")
    st.divider()
    if results:
        df = pd.DataFrame(results).T.reset_index(drop=True)
        st.dataframe(df, use_container_width=True)

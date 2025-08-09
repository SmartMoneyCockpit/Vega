# vega_tradeability_meter.py — LIVE Polygon version (env-var tolerant)
import os
import math
import requests
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
import streamlit as st

# Accept either env var name so you don't have to change Render
POLY_KEY = os.getenv("POLYGON_API_KEY") or os.getenv("POLYGON_KEY")

@st.cache_data(show_spinner=False, ttl=60)
def fetch_polygon_daily(ticker: str, months_back: int = 6) -> pd.DataFrame:
    """Fetch last ~6 months of daily candles from Polygon."""
    if not POLY_KEY:
        raise RuntimeError("Missing Polygon API key (set POLYGON_API_KEY or POLYGON_KEY in Render).")

    end = pd.Timestamp.utcnow().tz_localize(None).normalize()
    start = end - relativedelta(months=months_back, days=3)

    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker.upper()}/range/1/day/"
        f"{start.date()}/{end.date()}?adjusted=true&sort=asc&limit=50000&apiKey={POLY_KEY}"
    )
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json().get("results", [])
    if not data:
        raise RuntimeError(f"No data returned for {ticker} (check the symbol or your API plan).")

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["t"], unit="ms")
    df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}, inplace=True)
    df = df[["date", "open", "high", "low", "close", "volume"]].set_index("date").sort_index()
    return df

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    prev_c = c.shift(1)
    tr = pd.concat([(h - l), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def score_tradeability(df: pd.DataFrame) -> dict:
    # Trend (0–10): slope of 50sma vs noise
    sma50 = df["close"].rolling(50).mean()
    slope = (sma50 - sma50.shift(10)) / 10
    noise = df["close"].pct_change().rolling(20).std()
    trend_raw = (slope / (noise * df["close"])).iloc[-1]
    trend_score = int(np.clip((trend_raw * 400) + 5, 0, 10)) if np.isfinite(trend_raw) else 0

    # Liquidity (0–10): where today’s volume ranks within window
    vol_pct = (df["volume"].rank(pct=True).iloc[-1])  # 0..1
    liq_score = int(np.clip(vol_pct * 10, 0, 10))

    # Volatility regime via ATR% of price
    atr14 = atr(df, 14)
    atr_pct = (atr14 / df["close"]).iloc[-1]
    if atr_pct < 0.015:
        regime = "Calm"
    elif atr_pct < 0.03:
        regime = "Normal"
    elif atr_pct < 0.06:
        regime = "Elevated"
    else:
        regime = "Wild"

    # Setup Quality (A..C) from blend + sweet spot volatility bump
    sweet = 0.015 <= atr_pct <= 0.04
    base = (0.6 * trend_score + 0.4 * liq_score) / 10  # 0..1
    bump = 0.1 if sweet else -0.05
    q = float(np.clip(base + bump, 0, 1))
    if q >= 0.85: quality = "A+"
    elif q >= 0.75: quality = "A"
    elif q >= 0.65: quality = "A-"
    elif q >= 0.55: quality = "B+"
    elif q >= 0.45: quality = "B"
    else: quality = "C"

    return {
        "trend_score": trend_score,
        "liquidity_score": liq_score,
        "vol_regime": regime,
        "atr_pct": float(atr_pct) if np.isfinite(atr_pct) else None,
        "quality": quality,
        "last_close": float(df["close"].iloc[-1]),
        "last_date": df.index[-1].date().isoformat(),
    }

def run():
    st.header("Vega – Tradeability Meter")
    st.caption("Assess instruments quickly with uniform inputs.")

    with st.container():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            ticker = st.text_input("Ticker", value="SPY", placeholder="e.g., SPY").strip().upper()
        with col2:
            timeframe = st.selectbox("Timeframe", ["Daily"], index=0)  # extend later
        with col3:
            as_of = st.date_input("As of", None)

    st.divider()

    if not ticker:
        st.info("Enter a ticker to evaluate.")
        return

    try:
        with st.spinner(f"Fetching {ticker} from Polygon…"):
            df = fetch_polygon_daily(ticker)
        metrics = score_tradeability(df)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Trend Score", f"{metrics['trend_score']}/10", help="Higher = clearer directional edge")
        m2.metric("Liquidity Score", f"{metrics['liquidity_score']}/10", help="Higher = easier fills / less slippage")
        m3.metric("Volatility Regime", metrics["vol_regime"], help="Based on ATR% of price")
        m4.metric("Setup Quality", metrics["quality"], help="Blend of trend/liquidity + ‘sweet spot’ vol")

        atr_pct_txt = f"{metrics['atr_pct']*100:.2f}%" if metrics["atr_pct"] is not None else "n/a"
        st.success(f"{ticker} @ {metrics['last_close']:.2f} • {metrics['last_date']} • ATR% ~ {atr_pct_txt}")

    except Exception as e:
        st.error(f"Error: {e}")
        if not POLY_KEY:
            st.info("Add POLYGON_API_KEY or POLYGON_KEY in Render → Environment and redeploy.")

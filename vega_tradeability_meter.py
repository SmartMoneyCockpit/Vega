# vega_tradeability_meter.py — Polygon LIVE (15m / 1h / Daily) + Journal + Sheets sync + Test button
import os
import io
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import streamlit as st

POLY_KEY = os.getenv("POLYGON_API_KEY") or os.getenv("POLYGON_KEY")
SHEETS_SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
SHEETS_WORKSHEET = os.getenv("SHEETS_WORKSHEET_NAME", "tradeability_log")

def _poly_range_url(ticker: str, mult: int, span: str, start_dt, end_dt) -> str:
    return (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{mult}/{span}/"
        f"{start_dt.date()}/{end_dt.date()}?adjusted=true&sort=asc&limit=50000&apiKey={POLY_KEY}"
    )

@st.cache_data(show_spinner=False, ttl=60)
def fetch_polygon(ticker: str, timeframe: str) -> pd.DataFrame:
    if not POLY_KEY:
        raise RuntimeError("Missing Polygon API key (set POLYGON_API_KEY or POLYGON_KEY in Render).")
    ticker = ticker.upper().strip()
    now = datetime.now(timezone.utc)
    if timeframe == "15m":
        mult, span = 15, "minute"; start = now - timedelta(days=10)
    elif timeframe == "1h":
        mult, span = 1, "hour"; start = now - timedelta(days=60)
    else:
        mult, span = 1, "day"; start = (now - relativedelta(months=6, days=3))
    url = _poly_range_url(ticker, mult, span, start, now)
    r = requests.get(url, timeout=20); r.raise_for_status()
    data = r.json().get("results", [])
    if not data:
        raise RuntimeError(f"No data returned for {ticker} ({timeframe}).")
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["t"], unit="ms", utc=True)
    df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"}, inplace=True)
    return df.set_index("date")[["open","high","low","close","volume"]].sort_index()

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    prev_c = c.shift(1)
    tr = pd.concat([(h - l), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def score_tradeability(df: pd.DataFrame) -> dict:
    if len(df) < 60:
        df = df.tail(60)
    sma50 = df["close"].rolling(50).mean()
    slope = (sma50 - sma50.shift(10)) / 10
    noise = df["close"].pct_change().rolling(20).std()
    trend_raw = (slope / (noise * df["close"])).iloc[-1]
    trend_score = int(np.clip((trend_raw * 400) + 5, 0, 10)) if np.isfinite(trend_raw) else 0
    vol_pct = (df["volume"].rank(pct=True).iloc[-1])
    liq_score = int(np.clip(vol_pct * 10, 0, 10))
    atr14 = atr(df, 14)
    atr_pct = (atr14 / df["close"]).iloc[-1]
    if atr_pct < 0.015: regime = "Calm"
    elif atr_pct < 0.03: regime = "Normal"
    elif atr_pct < 0.06: regime = "Elevated"
    else: regime = "Wild"
    sweet = 0.015 <= atr_pct <= 0.04
    base = (0.6 * trend_score + 0.4 * liq_score) / 10
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
        "last_date": df.index[-1].astimezone(timezone.utc).isoformat(),
    }

LOG_DIR = "data"
LOG_FILE = os.path.join(LOG_DIR, "tradeability_log.csv")

def append_journal(record: dict):
    os.makedirs(LOG_DIR, exist_ok=True)
    row = pd.DataFrame([record])
    if os.path.exists(LOG_FILE):
        row.to_csv(LOG_FILE, mode="a", header=False, index=False)
    else:
        row.to_csv(LOG_FILE, index=False)

def load_journal(n: int = 1000) -> pd.DataFrame:
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(LOG_FILE)
        return df.tail(n)
    except Exception:
        return pd.DataFrame()

def try_sheets_append(record: dict):
    if not SHEETS_SPREADSHEET_ID:
        return "sheets_not_configured"
    try:
        import sheets_sync
        sheets_sync.append_row(SHEETS_SPREADSHEET_ID, SHEETS_WORKSHEET, record)
        return "ok"
    except Exception as e:
        return f"error: {e}"

def run():
    st.header("Vega – Tradeability Meter")
    st.caption("Real-time scoring with Polygon data. 15m / 1h / Daily + auto journal logging + Sheets sync.")

    with st.container():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            ticker = st.text_input("Ticker", value="SPY", placeholder="e.g., SPY").strip().upper()
        with col2:
            timeframe = st.selectbox("Timeframe", ["15m", "1h", "Daily"], index=2)
        with col3:
            as_of = st.date_input("As of (optional)", None)

    # Sheets quick test
    with st.expander("Google Sheets • connection test"):
        if st.button("Send test row to Google Sheet"):
            test_rec = {
                "ts_utc": datetime.now(timezone.utc).isoformat(),
                "ticker": "TEST",
                "timeframe": "TEST",
                "last_close": 0.0,
                "trend_score": 0,
                "liquidity_score": 0,
                "vol_regime": "n/a",
                "atr_pct": 0.0,
                "quality": "n/a",
                "note": "Connectivity check from Vega",
            }
            status = try_sheets_append(test_rec)
            st.success("Test row sent ✅") if status == "ok" else st.error(status)

    st.divider()

    if not ticker:
        st.info("Enter a ticker to evaluate.")
        return

    try:
        with st.spinner(f"Fetching {ticker} ({timeframe}) from Polygon…"):
            df = fetch_polygon(ticker, timeframe)
        metrics = score_tradeability(df)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Trend Score", f"{metrics['trend_score']}/10")
        m2.metric("Liquidity Score", f"{metrics['liquidity_score']}/10")
        m3.metric("Volatility Regime", metrics["vol_regime"])
        m4.metric("Setup Quality", metrics["quality"])

        atr_pct_txt = f"{metrics['atr_pct']*100:.2f}%" if metrics['atr_pct'] is not None else "n/a"
        st.success(f"{ticker} @ {metrics['last_close']:.2f} • {metrics['last_date']} • ATR% ~ {atr_pct_txt} • TF={timeframe}")

        rec = {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "ticker": ticker,
            "timeframe": timeframe,
            "last_close": metrics["last_close"],
            "trend_score": metrics["trend_score"],
            "liquidity_score": metrics["liquidity_score"],
            "vol_regime": metrics["vol_regime"],
            "atr_pct": metrics["atr_pct"],
            "quality": metrics["quality"],
        }
        append_journal(rec)
        _ = try_sheets_append(rec)

        with st.expander("Journal (latest scans)"):
            jdf = load_journal(500)
            if not jdf.empty:
                st.dataframe(jdf.tail(50), use_container_width=True)
                buff = io.StringIO()
                jdf.to_csv(buff, index=False)
                st.download_button("Download journal CSV", buff.getvalue(), file_name="tradeability_log.csv", mime="text/csv")
            else:
                st.caption("No journal entries yet.")

    except Exception as e:
        st.error(f"Error: {e}")
        if not POLY_KEY:
            st.info("Add POLYGON_API_KEY or POLYGON_KEY in Render → Environment and redeploy.")

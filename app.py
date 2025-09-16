# app.py — Vega Cockpit (focused, dark, no-plotly)
import os
import io
import glob
import datetime as dt
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import yfinance as yf

# (safe if you later import ib_insync elsewhere)
import nest_asyncio as _na
_na.apply()

st.set_page_config(page_title="Vega Cockpit", layout="wide")

APP_ENV = os.getenv("APP_ENV", "prod")
st.sidebar.caption(f"Environment: **{APP_ENV}**")

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data(ttl=900, show_spinner=False)
def yf_hist(symbol: str, period="6mo", interval="1d") -> pd.DataFrame:
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    df = df.rename(columns=str.lower).reset_index().rename(columns={"index": "date"})
    return df

def pct_change(series: pd.Series, periods: int) -> float:
    if len(series) <= periods or series.iloc[-periods-1] == 0:
        return np.nan
    return 100 * (series.iloc[-1] / series.iloc[-periods-1] - 1)

def tv_embed(symbol: str, interval: str = "D", theme: str = "dark", height: int = 560):
    # one TradingView widget only
    widget = f"""
    <div class="tradingview-widget-container">
      <div id="tvchart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "autosize": true,
          "symbol": "{symbol}",
          "interval": "{interval}",
          "timezone": "Etc/UTC",
          "theme": "{theme}",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "rgba(0,0,0,0)",
          "hide_top_toolbar": false,
          "allow_symbol_change": true,
          "container_id": "tvchart"
        }});
      </script>
    </div>
    """
    st.components.v1.html(widget, height=height, scrolling=False)

def list_pdfs(region: str) -> list[Path]:
    # convention: reports/<REGION>/*.pdf  (REGION in {USA, CANADA, MEXICO, APAC, EUROPE})
    folder = Path("reports") / region.upper()
    return sorted(folder.glob("*.pdf"))

# -----------------------------
# Layout
# -----------------------------
st.title("Vega Cockpit — Core Starter")

tab_dash, tab_apac, tab_scanner, tab_reports, tab_system = st.tabs(
    ["Dashboard", "APAC Panel", "Scanner", "Reports", "System"]
)

# -----------------------------
# Dashboard — ticker input + quick chart/table
# -----------------------------
with tab_dash:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Quick Ticker")
        symbol = st.text_input("Symbol", value="SPY", placeholder="e.g., AAPL, MSFT, TSLA, SPY")
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
        interval = st.selectbox("Interval", ["1d", "1h", "30m", "15m"], index=0)
        df = yf_hist(symbol, period=period, interval=interval)
        if df.empty:
            st.warning("No data found for that symbol/period.")
        else:
            # native Streamlit chart (no plotly)
            st.line_chart(df.set_index("date")["close"], height=320)
            st.caption("Close price (auto-adjusted)")
            st.dataframe(df.tail(25), use_container_width=True)

    with c2:
        st.subheader("TradingView (single)")
        tv_interval = "D" if interval.endswith("d") else "60"
        tv_embed(symbol, interval=tv_interval, theme="dark", height=420)

# -----------------------------
# APAC Panel — table summary + one TV chart
# -----------------------------
with tab_apac:
    st.subheader("APAC Indices — Table Summary")
    apac_map = {
        "Nikkei 225": "^N225",
        "ASX 200": "^AXJO",
        "CSI 300": "000300.SS",
        "Hang Seng": "^HSI",
        "USDJPY": "JPY=X",
        "AUDUSD": "AUDUSD=X",
    }
    rows = []
    for name, sym in apac_map.items():
        d = yf_hist(sym, period="6mo", interval="1d")
        if d.empty:
            rows.append({"Name": name, "Symbol": sym, "Last": np.nan, "1D%": np.nan, "1W%": np.nan, "1M%": np.nan})
        else:
            last = float(d["close"].iloc[-1])
            d1 = pct_change(d["close"], 1)
            d5 = pct_change(d["close"], 5)
            d21 = pct_change(d["close"], 21)
            rows.append({"Name": name, "Symbol": sym, "Last": round(last, 2), "1D%": round(d1, 2),
                         "1W%": round(d5, 2), "1M%": round(d21, 2)})
    tdf = pd.DataFrame(rows)
    st.dataframe(tdf, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("One APAC Chart")
    picked = st.selectbox("Pick index/cross to view", list(apac_map.keys()))
    tv_embed(apac_map[picked], interval="D", theme="dark", height=560)

# -----------------------------
# Scanner — simple, usable stub
# -----------------------------
with tab_scanner:
    st.subheader("IBKR Stock Scanner (Stub)")
    st.caption("This runs a safe example now. We’ll wire real feeds in the next upgrade.")
    universe = st.text_area(
        "Symbols (comma-separated)",
        value="AAPL, MSFT, SPY, TSLA, NVDA, AMZN",
    )
    lookback = st.selectbox("Lookback (days)", [1, 5, 21], index=0)
    syms = [s.strip().upper() for s in universe.split(",") if s.strip()]
    out = []
    for s in syms:
        d = yf_hist(s, period="6mo", interval="1d")
        if d.empty: continue
        last = float(d["close"].iloc[-1])
        change = pct_change(d["close"], lookback)
        out.append({"symbol": s, "last": round(last, 2), f"{lookback}d%": round(change, 2)})
    sdf = pd.DataFrame(out).sort_values(by=f"{lookback}d%", ascending=False)
    st.dataframe(sdf, use_container_width=True, hide_index=True)

# -----------------------------
# Reports — show PDFs by region
# -----------------------------
with tab_reports:
    st.subheader("Daily Reports (PDF)")
    region = st.selectbox("Region", ["USA", "CANADA", "MEXICO", "APAC", "EUROPE"], index=3)
    pdfs = list_pdfs(region)
    if not pdfs:
        st.info(f"No PDFs found in `reports/{region}` yet.")
    else:
        for p in pdfs[::-1]:
            with open(p, "rb") as f:
                st.download_button(
                    label=f"Download {p.name}",
                    data=f.read(),
                    file_name=p.name,
                    mime="application/pdf",
                    use_container_width=True,
                )

# -----------------------------
# System — health
# -----------------------------
with tab_system:
    st.subheader("Health / Liveness")
    checks = [
        ("Python", os.sys.version.split()[0], True),
        ("Streamlit", st.__version__, True),
        ("yfinance", yf.__version__, True),
        ("ENV PORT", os.getenv("PORT", "not-set"), True),
    ]
    for k, v, ok in checks:
        st.write(f"**{k}**: `{v}` — {'✅ OK' if ok else '❌ FAIL'}")
    st.success("System check complete.")

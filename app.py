# app.py — Vega Cockpit (focused, dark, no-plotly) — with TradingView Connect + Stay Out vs Get Back In
import os
import sys
from pathlib import Path
import datetime as dt
import glob

import pandas as pd
import numpy as np
import streamlit as st
import yfinance as yf
import yaml

# (safe if ib_insync appears anywhere in your codebase)
import nest_asyncio as _na
_na.apply()

# ---------------------------------------
# Streamlit config
# ---------------------------------------
st.set_page_config(page_title="Vega Cockpit", layout="wide")
APP_ENV = os.getenv("APP_ENV", "prod")
st.sidebar.caption(f"Environment: **{APP_ENV}**")

# ---------------------------------------
# Ensure we can import src/* modules
# ---------------------------------------
ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# TradingView Connect module (drop-in)
# Save tv_connect.py at: src/integrations/tv_connect.py
try:
    from integrations.tv_connect import tradingview_panel  # type: ignore
    _tv_import_err = None
except Exception as e:
    tradingview_panel = None
    _tv_import_err = str(e)

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data(ttl=900, show_spinner=False)
def yf_hist(symbol: str, period="6mo", interval="1d") -> pd.DataFrame:
    try:
        df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
    except Exception:
        return pd.DataFrame()
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    df = df.rename(columns=str.lower).reset_index(names="date")
    if "date" not in df.columns:
        df = df.reset_index().rename(columns={"index": "date"})
    return df

def pct_change(series: pd.Series, periods: int) -> float:
    try:
        if len(series) <= periods or series.iloc[-periods-1] == 0:
            return np.nan
        return 100 * (series.iloc[-1] / series.iloc[-periods-1] - 1)
    except Exception:
        return np.nan

def sma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n).mean()

def tv_embed(symbol: str, interval: str = "D", theme: str = "dark", height: int = 720):
    widget = f"""
    <div class="tradingview-widget-container" style="height:{height}px;">
      <div id="tvchart" style="height:{height}px;"></div>
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
    folder = Path("reports") / region.upper()
    return sorted(folder.glob("*.pdf"))

# -----------------------------
# Layout (added Stay Out vs Get Back In)
# -----------------------------
st.title("Vega Cockpit — Core Starter")

tab_dash, tab_apac, tab_scan, tab_europe, tab_reports, tab_stayout, tab_system = st.tabs(
    ["Dashboard", "APAC Panel", "Scanner", "Europe", "Reports", "Stay Out vs Get Back In", "System"]
)

# -----------------------------
# DASHBOARD — big TradingView + quick chart/table
# -----------------------------
with tab_dash:
    st.subheader("Quick Ticker")
    col = st.columns(3)
    with col[0]:
        symbol = st.text_input("Symbol", value="SPY", placeholder="e.g., AAPL, MSFT, TSLA, SPY").strip().upper()
    with col[1]:
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
    with col[2]:
        interval = st.selectbox("Interval", ["1d", "1h", "30m", "15m"], index=0)

    # --- TradingView full-width ---
    st.markdown("### TradingView Chart")
    tv_interval = "D" if interval.endswith("d") else "60"
    tv_embed(symbol or "SPY", interval=tv_interval, theme="dark", height=720)

    # --- Native chart + table ---
    df = yf_hist(symbol or "SPY", period=period, interval=interval)
    if df.empty:
        st.warning("No data found for that symbol/period.")
    else:
        st.line_chart(df.set_index("date")["close"], height=300, use_container_width=True)
        st.caption("Close price (auto-adjusted). Latest 25 rows below.")
        st.dataframe(df.tail(25), use_container_width=True)

# -----------------------------
# APAC — table summary + single chart picker
# -----------------------------
with tab_apac:
    st.subheader("APAC Indices — Summary")
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
            rows.append({
                "Name": name,
                "Symbol": sym,
                "Last": round(last, 2),
                "1D%": round(pct_change(d["close"], 1), 2),
                "1W%": round(pct_change(d["close"], 5), 2),
                "1M%": round(pct_change(d["close"], 21), 2),
            })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Single APAC Chart")
    picked = st.selectbox("Pick index/cross", list(apac_map.keys()))
    tv_embed(apac_map[picked], interval="D", theme="dark", height=560)

# -----------------------------
# SCANNER — working now (Yahoo Finance backbone)
# -----------------------------
with tab_scan:
    st.subheader("Stock Scanner (live % change)")
    universe = st.text_area(
        "Symbols (comma-separated)",
        value="AAPL, MSFT, SPY, TSLA, NVDA, AMZN",
    )
    lookback = st.selectbox("Lookback (days)", [1, 5, 21], index=0)

    syms = [s.strip().upper() for s in universe.split(",") if s.strip()]
    results = []
    for s in syms:
        d = yf_hist(s, period="6mo", interval="1d")
        if d.empty:
            continue
        last = float(d["close"].iloc[-1])
        chg = pct_change(d["close"], lookback)
        results.append({"symbol": s, "last": round(last, 2), "change%": round(chg, 2)})

    if results:
        sdf = pd.DataFrame(results).sort_values(by="change%", ascending=False)
        st.dataframe(sdf, use_container_width=True, hide_index=True)
    else:
        st.warning("No data returned for given symbols.")

    st.caption("Powered by Yahoo Finance for now. IBKR/Polygon wiring comes next.")

# -----------------------------
# EUROPE — table (no YAML parsing error)
# -----------------------------
with tab_europe:
    st.subheader("Europe Trading — Indices & ETFs")
    config = """
    exchanges:
      - name: London (LSE)
        indices: ["^FTSE"]
        etfs: ["EWU", "EZU"]
      - name: Frankfurt (Xetra)
        indices: ["^GDAXI"]
        etfs: ["EWG", "DAX"]
      - name: Paris (Euronext)
        indices: ["^FCHI"]
        etfs: ["EWQ"]
      - name: Europe Broad
        indices: ["^STOXX50E"]
        etfs: ["VGK", "FEZ"]
    """
    data = yaml.safe_load(config)
    rows = [{"Exchange": ex["name"], "Indices": ", ".join(ex["indices"]), "ETFs": ", ".join(ex["etfs"])}
            for ex in data["exchanges"]]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# -----------------------------
# REPORTS — list & download PDFs per region
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
# STAY OUT vs GET BACK IN — risk toggle + TradingView panel
# -----------------------------
with tab_stayout:
    st.subheader("Stay Out vs Get Back In")

    # --- Simple, transparent risk model (expand later) ---
    # Signals:
    # 1) VIX > 20 -> Risk-Off
    # 2) SPY close < SPY 50-day SMA -> Risk-Off
    # If both false -> Risk-On
    spy = yf_hist("SPY", period="6mo", interval="1d")
    vix = yf_hist("^VIX", period="6mo", interval="1d")

    # Compute signals
    risk_notes = []
    is_risk_off = False

    if not vix.empty:
        vix_last = float(vix["close"].iloc[-1])
        if vix_last > 20:
            is_risk_off = True
            risk_notes.append(f"VIX {vix_last:.1f} > 20 (Risk-Off)")
        else:
            risk_notes.append(f"VIX {vix_last:.1f} ≤ 20")
    else:
        risk_notes.append("VIX data unavailable")

    if not spy.empty:
        s50 = sma(spy["close"], 50)
        if len(s50.dropna()) > 0:
            if float(spy['close'].iloc[-1]) < float(s50.iloc[-1]):
                is_risk_off = True
                risk_notes.append("SPY below 50-day SMA (Risk-Off)")
            else:
                risk_notes.append("SPY above 50-day SMA")
        else:
            risk_notes.append("Not enough data for SPY 50-SMA")
    else:
        risk_notes.append("SPY data unavailable")

    status = "🟥 STAY OUT (Risk-Off)" if is_risk_off else "🟩 GET BACK IN (Risk-On)"
    st.markdown(f"### {status}")
    st.caption(" • ".join(risk_notes))

    # --- TradingView Connect panel (no API/creds) ---
    st.divider()
    st.subheader("TradingView Connect")
    if tradingview_panel is None:
        st.warning("TradingView panel unavailable — couldn’t import `src/integrations/tv_connect.py`.")
        if _tv_import_err:
            with st.expander("Import error details"):
                st.code(_tv_import_err)
        st.info("Place tv_connect.py at `src/integrations/tv_connect.py` to enable this panel.")
    else:
        # Default symbols: core equity + volatility + FX hedge
        items = [
            {"label": "S&P 500 ETF", "symbol": "SPY", "exchange": "AMEX"},
            {"label": "NASDAQ 100 ETF", "symbol": "QQQ", "exchange": "AMEX"},
            {"label": "Russell 2000 ETF", "symbol": "IWM", "exchange": "AMEX"},
            {"label": "VIX (CBOE)", "symbol": "VIX", "exchange": "CBOE"},
            {"label": "USD/MXN", "symbol": "USDMXN", "exchange": "FX"},
        ]
        default_ivl = "60" if is_risk_off else "D"
        tradingview_panel(items, default_interval=default_ivl, show_embed_preview=True, embed_height=520)

# -----------------------------
# SYSTEM — health
# -----------------------------
with tab_system:
    st.subheader("Health / Liveness")
    checks = [
        ("Python", os.sys.version.split()[0], True),
        ("Streamlit", st.__version__, True),
        ("yfinance", yf.__version__, True),
        ("ENV PORT", os.getenv("PORT", "not-set"), True),
        ("TV Panel Import", "OK" if _tv_import_err is None else "FAILED", _tv_import_err is None),
    ]
    for k, v, ok in checks:
        st.write(f"**{k}**: `{v}` — {'✅ OK' if ok else '❌ FAIL'}")
    if _tv_import_err:
        st.code(_tv_import_err, language="text")
    st.success("System check complete.")

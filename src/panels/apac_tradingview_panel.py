# apac_tradingview_panel.py
# Streamlit module: Asia-Pacific Trading Day cockpit one‑pager using TradingView embeds
# Drop this file into your Vega repo (e.g., src/panels/) and add it to your router/menu.
# Requirements: streamlit (core). No external API keys needed — TradingView embeds.

from __future__ import annotations
import streamlit as st
from textwrap import dedent

st.set_page_config(page_title="Vega | APAC Trading Day", layout="wide")

# =============================
# ======= CONFIG / INPUT ======
# =============================
# You can flip these on/off as needed. Symbols chosen for broad availability on TradingView.
APAC_INDEX_SYMBOLS = [
    ("Japan — Nikkei 225", "TVC:NI225"),         # Nikkei 225
    ("South Korea — KOSPI", "INDEX:KS11"),       # KOSPI
    ("Hong Kong — Hang Seng", "INDEX:HSI"),      # Hang Seng Index
    ("Australia — S&P/ASX 200", "ASX:XJO"),      # ASX 200
    ("China — CSI 300", "SSE:000300"),           # CSI 300
]

FX_SYMBOLS = [
    ("USD/JPY", "FX_IDC:USDJPY"),
    ("AUD/USD", "FX_IDC:AUDUSD"),
    ("USD/KRW", "FX_IDC:USDKRW"),
    ("USD/CNY", "FX_IDC:USDCNY"),
    ("USD/HKD", "OANDA:USDHKD"),
]

COMMODITY_SYMBOLS = [
    ("Brent Crude", "TVC:UKOIL"),
    ("Gold (XAUUSD)", "OANDA:XAUUSD"),
    ("Copper (COMEX)", "COMEX:HG1!"),
]

ETF_TILES = [
    ("Japan (DXJ / EWJ)", "🟢 Trade Now", "AI/semis leadership, weak JPY tailwind; watch BoJ headlines."),
    ("Korea (EWY)", "🟢 Trade Now", "Semiconductor export strength; use trailing stops on pullbacks."),
    ("Australia (EWA/A200)", "🟡 Wait", "Range‑bound; want breakout above recent highs; AUD strength headwind."),
    ("Hong Kong (EWH / 2800.HK)", "🟡 Wait", "China‑linked; await concrete stimulus for confirmation."),
    ("China (MCHI/FXI/ASHR)", "🔴 Avoid", "Soft data + policy uncertainty; wait for confirmed easing."),
]

HEDGE_TILES = [
    ("SPXU (3x short S&P)", "🟡 Monitor", "Use if VIX > 20 and U.S. breadth deteriorates."),
    ("SQQQ (3x short Nasdaq)", "🟢 Watch Closely", "Primary hedge vs AI/semis unwind; trigger on NDX support break."),
    ("RWM (short Russell 2000)", "🟡 Optional", "Small‑cap hedge on risk‑off / credit stress."),
]

# =============================
# ======= UI HELPERS ==========
# =============================

def tv_advanced_chart(symbol: str, interval: str = "60", theme: str = "light", studies: list[str] | None = None,
                      height: int = 520, hide_side_toolbar: bool = False) -> str:
    """Return TradingView advanced chart embed HTML for a given symbol.
    interval: "1"=1m, "5"=5m, "15"=15m, "60"=1h, "240"=4h, "D"=1d, "W"=1w, "M"=1m
    studies: e.g., ["RSI@tv-basicstudies","MAExp@tv-basicstudies","MASimple@tv-basicstudies"]
    """
    if studies is None:
        studies = ["RSI@tv-basicstudies", "MASimple@tv-basicstudies", "MAExp@tv-basicstudies"]
    studies_js = ",\n                ".join([f'"{s}"' for s in studies])
    html = f"""
    <div class="tradingview-widget-container" style="height:{height}px;">
      <div id="tv_{symbol.replace(':','_').replace('!','_')}" style="height:{height}px;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "width": "100%",
          "height": {height},
          "symbol": "{symbol}",
          "interval": "{interval}",
          "timezone": "Etc/UTC",
          "theme": "{theme}",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "#f1f3f6",
          "enable_publishing": false,
          "allow_symbol_change": true,
          "hide_top_toolbar": false,
          "hide_side_toolbar": {str(hide_side_toolbar).lower()},
          "container_id": "tv_{symbol.replace(':','_').replace('!','_')}",
          "studies": [
                {studies_js}
          ]
        }});
      </script>
    </div>
    """
    return dedent(html)


def tile(label: str, status: str, note: str):
    cls = "bg-green-50" if "🟢" in status else ("bg-yellow-50" if "🟡" in status else "bg-red-50")
    st.markdown(f"""
    <div style='border:1px solid #e5e7eb;border-radius:14px;padding:12px;background:#fff;'>
      <div style='font-weight:600;font-size:0.95rem;margin-bottom:6px;'>{label}</div>
      <div style='font-size:1.1rem;margin-bottom:6px;'>{status}</div>
      <div style='color:#4b5563;font-size:0.9rem;'>{note}</div>
    </div>
    """, unsafe_allow_html=True)

# =============================
# ========== LAYOUT ===========
# =============================

st.title("🌏 APAC Trading Day — TradingView Panel")

with st.expander("⚙️ Panel settings", expanded=False):
    intr = st.selectbox("Default interval", ["60", "240", "D", "W"], index=2, help="1h, 4h, 1D, 1W")
    tv_theme = st.selectbox("Chart theme", ["light", "dark"], index=0)
    chart_h = st.slider("Chart height (px)", min_value=360, max_value=800, value=520, step=20)
    show_fx = st.toggle("Show FX panel", value=True)
    show_cmd = st.toggle("Show Commodities panel", value=True)

# -----------------------------
# Indices row
# -----------------------------
st.subheader("📈 APAC Indices")
cols = st.columns(3)
for i, (label, sym) in enumerate(APAC_INDEX_SYMBOLS):
    with cols[i % 3]:
        st.markdown(f"**{label}** — `{sym}`")
        st.components.v1.html(tv_advanced_chart(sym, interval=intr, theme=tv_theme, height=chart_h), height=chart_h + 20)

# -----------------------------
# FX row
# -----------------------------
if show_fx:
    st.subheader("💱 FX (APAC Crosses)")
    cols_fx = st.columns(3)
    for i, (label, sym) in enumerate(FX_SYMBOLS):
        with cols_fx[i % 3]:
            st.markdown(f"**{label}** — `{sym}`")
            st.components.v1.html(tv_advanced_chart(sym, interval=intr, theme=tv_theme, height=chart_h, hide_side_toolbar=True), height=chart_h + 20)

# -----------------------------
# Commodities row
# -----------------------------
if show_cmd:
    st.subheader("🛢️ Commodities")
    cols_cmd = st.columns(3)
    for i, (label, sym) in enumerate(COMMODITY_SYMBOLS):
        with cols_cmd[i % 3]:
            st.markdown(f"**{label}** — `{sym}`")
            st.components.v1.html(tv_advanced_chart(sym, interval=intr, theme=tv_theme, height=chart_h, hide_side_toolbar=True), height=chart_h + 20)

# -----------------------------
# Trade Now vs Wait tiles
# -----------------------------
st.subheader("📊 Tactical Watchlist — Trade Now vs Wait")
cols_tiles = st.columns(3)
for i, (label, status, note) in enumerate(ETF_TILES):
    with cols_tiles[i % 3]:
        tile(label, status, note)

# -----------------------------
# Hedges tiles
# -----------------------------
st.subheader("🛡️ Tactical Hedges")
cols_hedge = st.columns(3)
for i, (label, status, note) in enumerate(HEDGE_TILES):
    with cols_hedge[i % 3]:
        tile(label, status, note)

# -----------------------------
# Notes
# -----------------------------
st.info(
    "Charts are live TradingView embeds with RSI + SMA + EMA. Interval is configurable. "
    "Symbols chosen for broad availability; adjust symbols to your preferred feeds if needed."
)

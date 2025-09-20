# src/pages/05_TradingView_Charts.py
import json, urllib.parse
import streamlit as st

st.set_page_config(page_title="TradingView Charts", layout="wide")
st.title("TradingView — Advanced Charts & Heatmap")

# --------------------------
# Watchlists (edit as you like)
# Use exchange prefixes for best resolution on TV:
#   NYSEARCA/AMEX for ETFs, NASDAQ for QQQ, CBOE for VIX, etc.
NA_LIST  = [
    "NYSEARCA:SPY", "NASDAQ:QQQ", "NYSEARCA:DIA", "NYSEARCA:IWM",
    "CBOE:VIX", "NYSEARCA:XLF", "NYSEARCA:XLE", "NYSEARCA:XLK"
]
EU_LIST  = ["NYSEARCA:VGK", "NYSEARCA:EZU", "NYSEARCA:FEZ"]
APAC_LIST = ["NYSEARCA:EWJ", "NYSEARCA:EWA", "NYSEARCA:EWH", "NYSEARCA:EWY", "TVC:HSI"]

# --------------------------
def tv_advanced_chart_html(symbol: str, interval: str="D", theme: str="light",
                           studies=None, autosize=True, height=640) -> str:
    """Return HTML embed for TradingView Advanced Real-Time Chart widget."""
    if studies is None:
        # Built-in study names (TradingView)
        studies = ["RSI@tv-basicstudies", "MASimple@tv-basicstudies", "MAExp@tv-basicstudies"]
    config = {
        "symbol": symbol,
        "interval": interval,            # "1", "5", "15", "60", "240", "D", "W", "M"
        "timezone": "Etc/UTC",
        "theme": theme,                  # "light" or "dark"
        "style": "1",                    # candle
        "locale": "en",
        "studies": studies,
        "allow_symbol_change": True,
        "hide_side_toolbar": False,
        "withdateranges": True,
        "details": True,
        "hotlist": True,
        "calendar": True,
        "autosize": autosize,
        "height": height if not autosize else None,
    }
    # Build the widget
    return f"""
<div class="tradingview-widget-container" style="height:{height}px;">
  <div id="tradingview_chart"></div>
</div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
  new TradingView.widget({json.dumps(config)});
</script>
"""

def tv_heatmap_html(data_source: str="SPX500", theme: str="light", height: int=640) -> str:
    """
    TradingView Stock Heatmap widget.
    Common data_source choices that work well: "SPX500", "NASDAQ100", "DJI".
    """
    config = {
        "dataSource": data_source,
        "blockColor": "change",
        "blockSize": "market_cap",
        "grouping": "sector",
        "theme": theme,
        "locale": "en",
        "allowZoom": True,
        "showSymbolTooltip": True,
        "width": "100%",
        "height": height,
    }
    return f"""
<div class="tradingview-widget-container" style="height:{height}px;">
  <div class="tradingview-widget-container__widget"></div>
</div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js" async>
{json.dumps(config)}
</script>
"""

# --------------------------
# Controls
c1, c2, c3, c4 = st.columns([2,2,1,1])
region = c1.selectbox("Region", ["North America", "Europe", "APAC"], index=0)
interval = c2.selectbox("Interval", ["1", "5", "15", "60", "240", "D", "W", "M"], index=5)
theme = c3.selectbox("Theme", ["light", "dark"], index=0)
show_heatmap = c4.checkbox("Heatmap", value=True)

if region == "North America":
    symbols = NA_LIST
    default_heatmap = "SPX500"   # S&P 500
elif region == "Europe":
    symbols = EU_LIST
    default_heatmap = "SPX500"   # Heatmap choices are limited; SPX500 works everywhere
else:
    symbols = APAC_LIST
    default_heatmap = "SPX500"

symbol = st.selectbox("Symbol", symbols, index=0)

# Optional: manual entry
manual = st.text_input("Or type a TradingView symbol (e.g., NYSEARCA:SPY, NASDAQ:QQQ, CBOE:VIX, TVC:HSI)", "").strip()
if manual:
    symbol = manual

# Render chart
from streamlit.components.v1 import html
st.subheader("Advanced Chart")
html(tv_advanced_chart_html(symbol, interval=interval, theme=theme), height=660, scrolling=False)

# Render heatmap
if show_heatmap:
    st.subheader("Stock Heatmap")
    data_source = st.selectbox("Heatmap universe", ["SPX500", "NASDAQ100", "DJI"], index=["SPX500","NASDAQ100","DJI"].index(default_heatmap))
    html(tv_heatmap_html(data_source=data_source, theme=theme, height=600), height=620, scrolling=False)

st.caption("Tip: Edit the watchlists at the top of this file to match your symbols. Exchange prefixes improve resolution.")

NYSEARCA:SPY, NASDAQ:QQQ, NYSEARCA:DIA, NYSEARCA:IWM

CBOE:VIX, NYSEARCA:VGK, NYSEARCA:EZU, NYSEARCA:EWJ, TVC:HSI

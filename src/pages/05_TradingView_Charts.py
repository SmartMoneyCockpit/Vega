import os, json
from urllib.parse import quote
import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="TradingView Charts", layout="wide")
st.title("TradingView — Advanced Charts & Heatmap")

def _load_presets(section: str, fallback: dict) -> dict:
    try:
        cfg = json.load(open("config/tv_presets.json", "r", encoding="utf-8"))
        base = dict(fallback); base.update(cfg.get(section, {})); return base
    except Exception:
        return dict(fallback)

def _qp_get(name, default=None):
    try:
        v = st.query_params.get(name, default)
    except Exception:
        v = st.experimental_get_query_params().get(name, [default])
        v = v[0] if isinstance(v, list) else v
    if name == "height":
        try: return int(v)
        except: return default
    return v

def tv_advanced_chart_html(symbol: str, *, interval: str, theme: str,
                           studies: list, studies_overrides: dict | None,
                           height: int) -> str:
    cfg = {
        "symbol": symbol, "interval": interval, "timezone": "Etc/UTC",
        "theme": theme, "style": "1", "locale": "en",
        "studies": studies,
        "allow_symbol_change": True, "withdateranges": True,
        "details": True, "hotlist": True, "calendar": True,
        "autosize": True, "container_id": "tv_chart"
    }
    if studies_overrides:
        cfg["studies_overrides"] = studies_overrides
    return f"""
<div id="tv_chart" style="height:{height}px;"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script> new TradingView.widget({json.dumps(cfg)}); </script>
"""

def tv_heatmap_html(data_source: str, theme: str, height: int=600) -> str:
    cfg = {
        "dataSource": data_source, "blockColor": "change", "blockSize": "market_cap",
        "grouping": "sector", "theme": theme, "locale": "en",
        "allowZoom": True, "showSymbolTooltip": True, "width": "100%", "height": height
    }
    return f"""
<div class="tradingview-widget-container" style="height:{height}px;">
  <div class="tradingview-widget-container__widget"></div>
</div>
<script src="https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js" async>
{json.dumps(cfg)}
</script>
"""

# Presets (defaults: QQQ, D, dark, 900px; studies include EMA9/21/50/200)
PRE = _load_presets("charts", {
    "symbol": "NASDAQ:QQQ", "interval": "D", "theme": "dark", "height": 900,
    "studies": [
        "MAExp@tv-basicstudies","MAExp@tv-basicstudies","MAExp@tv-basicstudies","MAExp@tv-basicstudies",
        "RSI@tv-basicstudies","MACD@tv-basicstudies","ATR@tv-basicstudies","OBV@tv-basicstudies","Volume@tv-basicstudies"
    ],
    "studies_overrides": {
        "MAExp@tv-basicstudies.0.length": 9,
        "MAExp@tv-basicstudies.1.length": 21,
        "MAExp@tv-basicstudies.2.length": 50,
        "MAExp@tv-basicstudies.3.length": 200
    }
})

symbol   = _qp_get("symbol",   PRE["symbol"])
interval = _qp_get("interval", PRE["interval"])
theme    = _qp_get("theme",    PRE["theme"])
height   = _qp_get("height",   PRE["height"])
studies  = PRE.get("studies", [])
studies_overrides = PRE.get("studies_overrides", {})

c1, c2, c3, c4 = st.columns([2,2,1,1])
region = c1.selectbox("Region", ["North America","Europe","APAC"], index=0)
interval = c2.selectbox("Interval", ["1","5","15","60","240","D","W","M"],
                        index=["1","5","15","60","240","D","W","M"].index(interval if interval in ["1","5","15","60","240","D","W","M"] else "D"))
theme = c3.selectbox("Theme", ["light","dark"], index=(0 if theme=="light" else 1))
height = c4.slider("Height", 480, 1400, int(height), step=20)

NA  = ["NYSEARCA:SPY","NASDAQ:QQQ","NYSEARCA:DIA","NYSEARCA:IWM","CBOE:VIX","NYSEARCA:XLK","NYSEARCA:XLE"]
EU  = ["NYSEARCA:VGK","NYSEARCA:EZU","NYSEARCA:FEZ","TVC:FTSE"]
AP  = ["NYSEARCA:EWJ","NYSEARCA:EWA","NYSEARCA:EWH","NYSEARCA:EWY","TVC:HSI"]
choices = NA if region=="North America" else (EU if region=="Europe" else AP)
symbol = st.selectbox("Symbol", choices, index=0 if symbol not in choices else choices.index(symbol))
manual = st.text_input("Or type a TV symbol (e.g., NYSEARCA:SPY)", "").strip()
if manual: symbol = manual

st.subheader("Advanced Chart")
html(tv_advanced_chart_html(symbol, interval=interval, theme=theme,
                            studies=studies, studies_overrides=studies_overrides,
                            height=height),
     height=height+20, scrolling=False)

st.subheader("Stock Heatmap")
heat_univ = st.selectbox("Heatmap universe", ["SPX500","NASDAQ100","DJI"], index=0)
html(tv_heatmap_html(heat_univ, theme, 600), height=620, scrolling=False)

rel = f"?symbol={quote(symbol)}&interval={interval}&theme={theme}&height={height}"
st.text_input("Preset link (copy & bookmark)", value=rel)
st.markdown(f"[Open with these settings]({rel})  •  "
            f"[Open on TradingView](https://www.tradingview.com/chart/?symbol={quote(symbol)}&interval={interval})")
st.caption("Defaults come from config/tv_presets.json; query parameters override them.")

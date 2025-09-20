import os, json
from urllib.parse import quote
import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="TradingView Charts", layout="wide")
st.title("TradingView — Advanced Charts & Heatmap")

# Overlay code maps (same as dashboards)
OVERLAY_CODES = {
    "EMA 9":"e9", "EMA 21":"e21", "EMA 50":"e50", "EMA 200":"e200",
    "Bollinger (20,2)":"bb", "Ichimoku (9/26/52)":"ichi",
}
CODE_TO_OVERLAY = {v:k for k,v in OVERLAY_CODES.items()}
EMA_ORDER = ["EMA 9","EMA 21","EMA 50","EMA 200"]

def _load_presets(section: str, fallback: dict) -> dict:
    try:
        cfg = json.load(open("config/tv_presets.json", "r", encoding="utf-8"))
        base = dict(fallback); base.update(cfg.get(section, {})); return base
    except Exception:
        return dict(fallback)

def _get_qp() -> dict:
    try:
        qp = st.query_params
        out = {}
        for k, v in qp.items():
            if isinstance(v, list): out[k] = v[0] if v else ""
            else: out[k] = v
        return out
    except Exception:
        qp = st.experimental_get_query_params()
        return {k: (v[0] if isinstance(v, list) and v else "") for k, v in qp.items()}

def _decode_overlays(code_csv: str, default: list[str]) -> list[str]:
    if not code_csv: return default
    parts = [p.strip() for p in code_csv.split(",") if p.strip()]
    names = [CODE_TO_OVERLAY.get(p) for p in parts if CODE_TO_OVERLAY.get(p)]
    return names or default

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

# Presets (defaults include 4×EMA + pane studies)
PRE = _load_presets("charts", {
    "symbol": "NASDAQ:QQQ", "interval": "D", "theme": "dark", "height": 900,
    "studies": [],
    "studies_overrides": {}
})

# Query params
qp = _get_qp()
symbol   = qp.get("symbol", PRE["symbol"])
interval = qp.get("interval", PRE["interval"])
theme    = qp.get("theme", PRE["theme"])
try: height = int(qp.get("height", PRE["height"]))
except: height = PRE["height"]

# Build studies from ov=... if provided, else from presets file
OV_MAP = {
    "EMA 9":   ("MAExp@tv-basicstudies", 9),
    "EMA 21":  ("MAExp@tv-basicstudies", 21),
    "EMA 50":  ("MAExp@tv-basicstudies", 50),
    "EMA 200": ("MAExp@tv-basicstudies", 200),
    "Bollinger (20,2)": ("BollingerBands@tv-basicstudies", None),
    "Ichimoku (9/26/52)": ("IchimokuCloud@tv-basicstudies", None),
}
default_names = ["EMA 9","EMA 21","EMA 50","EMA 200"]  # default overlays
names = _decode_overlays(qp.get("ov",""), default_names)

# EMAs first for reliable per-instance overrides
ordered = [n for n in EMA_ORDER if n in names] + [n for n in names if n not in EMA_ORDER]
overlay_studies, ema_lengths = [], []
for name in ordered:
    study, length = OV_MAP[name]
    overlay_studies.append(study)
    if study == "MAExp@tv-basicstudies" and isinstance(length, int):
        ema_lengths.append(length)

PANE_STUDIES = ["RSI@tv-basicstudies","MACD@tv-basicstudies","ATR@tv-basicstudies","OBV@tv-basicstudies","Volume@tv-basicstudies"]
studies = overlay_studies + PANE_STUDIES
studies_overrides = {f"MAExp@tv-basicstudies.{i}.length": ln for i, ln in enumerate(ema_lengths)}

# Controls
c1, c2, c3, c4 = st.columns([2,2,1,1])
region  = c1.selectbox("Region", ["North America","Europe","APAC"], index=0)
interval = c2.selectbox("Interval", ["1","5","15","60","240","D","W","M"],
                        index=["1","5","15","60","240","D","W","M"].index(interval) if interval in ["1","5","15","60","240","D","W","M"] else 5)
theme    = c3.selectbox("Theme", ["light","dark"], index=(0 if theme=="light" else 1))
height   = c4.slider("Height", 480, 1400, int(height), step=20)

NA  = ["NYSEARCA:SPY","NASDAQ:QQQ","NYSEARCA:DIA","NYSEARCA:IWM","CBOE:VIX","NYSEARCA:XLK","NYSEARCA:XLE"]
EU  = ["NYSEARCA:VGK","NYSEARCA:EZU","NYSEARCA:FEZ","TVC:FTSE"]
AP  = ["NYSEARCA:EWJ","NYSEARCA:EWA","NYSEARCA:EWH","NYSEARCA:EWY","TVC:HSI"]
choices = NA if region=="North America" else (EU if region=="Europe" else AP)
symbol = st.selectbox("Symbol", choices, index=0 if symbol not in choices else choices.index(symbol))
manual = st.text_input("Or type a TV symbol (e.g., NYSEARCA:SPY)", "").strip()
if manual: symbol = manual

# Chart + Heatmap
st.subheader("Advanced Chart")
html(tv_advanced_chart_html(symbol, interval=interval, theme=theme,
                            studies=studies, studies_overrides=studies_overrides,
                            height=height),
     height=height+20, scrolling=False)

st.subheader("Stock Heatmap")
heat_univ = st.selectbox("Heatmap universe", ["SPX500","NASDAQ100","DJI"], index=0)
html(tv_heatmap_html(heat_univ, theme, 600), height=620, scrolling=False)

# Share link (preserves overlays via ov=)
ov_param = ",".join(OVERLAY_CODES[n] for n in ordered if n in OVERLAY_CODES)
rel = f"?symbol={quote(symbol)}&interval={interval}&theme={theme}&height={height}&ov={ov_param}"
st.text_input("Preset link (copy & bookmark)", value=rel)
st.markdown(f"[Open with these settings]({rel})  •  "
            f"[Open on TradingView](https://www.tradingview.com/chart/?symbol={quote(symbol)}&interval={interval})")
st.caption("Defaults read from config/tv_presets.json if ov= is omitted.")

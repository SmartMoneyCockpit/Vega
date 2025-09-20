
# src/components/tv_bridge.py
from __future__ import annotations
import os, json, urllib.parse
import streamlit as st
from streamlit.components.v1 import html

# ---- Overlay code maps (common built-ins) ----
OVERLAY_CODES = {
    "EMA 9": ("MAExp@tv-basicstudies", 9),
    "EMA 21": ("MAExp@tv-basicstudies", 21),
    "EMA 50": ("MAExp@tv-basicstudies", 50),
    "EMA 200": ("MAExp@tv-basicstudies", 200),
    "Bollinger (20,2)": ("BollingerBands@tv-basicstudies", None),
    "Ichimoku (9/26/52)": ("IchimokuCloud@tv-basicstudies", None),
}
DEFAULT_STUDIES = [s.strip() for s in (os.getenv("TV_DEFAULT_STUDIES","e9,e21,e50,e200")).split(",") if s.strip()]
CODE_MAP = {"e9":"EMA 9","e21":"EMA 21","e50":"EMA 50","e200":"EMA 200","bb":"Bollinger (20,2)","ichi":"Ichimoku (9/26/52)"}

def _studies_from_codes(codes: list[str] | None):
    codes = codes or DEFAULT_STUDIES
    names = [CODE_MAP.get(c, c) for c in codes]
    studies = []
    overrides = {}
    for name in names:
        if name in OVERLAY_CODES:
            study, length = OVERLAY_CODES[name]
            studies.append(study)
            # Per-instance length overrides for EMAs
            if length:
                overrides[f"{study}.length"] = length
    return studies, overrides

# ---------- URL Builders (iframe) ----------
def tv_embed_url(symbol: str, interval: str = "D", theme: str = "dark") -> str:
    tmpl = os.getenv("TV_EMBED_TEMPLATE", "")
    symbol_q = urllib.parse.quote(symbol, safe=":/")
    if tmpl:
        return (tmpl.replace("{SYMBOL}", symbol_q).replace("{INTERVAL}", interval).replace("{THEME}", theme))
    params = {"symbol": symbol_q, "interval": interval, "theme": theme, "hide_top_toolbar": "0", "hide_legend": "0"}
    return "https://s.tradingview.com/widgetembed/?" + urllib.parse.urlencode(params)

def tv_heatmap_url(region: str = "USA", prefer_auth: bool = True) -> str | None:
    key = region.upper().replace(" ","_")
    auth_url = os.getenv(f"TV_HEATMAP_{key}_AUTH_URL", "")
    pub_url  = os.getenv(f"TV_HEATMAP_{key}_PUBLIC_URL", "")
    if prefer_auth and auth_url: return auth_url
    return pub_url or None

# ---------- Renderers ----------
def render_chart(symbol: str, interval: str = "D", theme: str = "dark", height: int = 600, overlays: list[str] | None = None, mode: str = "auto"):
    """Render a TradingView chart.
    mode='iframe' uses widgetembed (best for authenticated browser sessions).
    mode='tvjs' uses tv.js with studies list (best for controlling built-in overlays).
    mode='auto': use tv.js if overlays provided; otherwise iframe.
    """
    if not symbol:
        st.info("Select a symbol to show TradingView."); return
    if mode == "auto":
        mode = "tvjs" if overlays else "iframe"

    if mode == "iframe":
        url = tv_embed_url(symbol, interval=interval, theme=theme)
        st.components.v1.iframe(url, height=height, scrolling=True)
        return

    # tv.js mode: supports studies programmatically
    studies, overrides = _studies_from_codes(overlays or [])
    cfg = {
        "symbol": symbol, "interval": interval, "timezone": "Etc/UTC",
        "theme": theme, "style": "1", "locale": "en",
        "studies": studies, "allow_symbol_change": True, "withdateranges": True,
        "details": True, "hotlist": True, "calendar": True,
        "autosize": True, "container_id": "tv_chart",
    }
    if overrides: cfg["studies_overrides"] = overrides
    html(f"""
<div id="tv_chart" style="height:{height}px;"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script> new TradingView.widget({json.dumps(cfg)}); </script>
""", height=height)

def render_heatmap(region: str = "USA", height: int = 520):
    url = tv_heatmap_url(region, prefer_auth=True) or tv_heatmap_url(region, prefer_auth=False)
    if url:
        st.components.v1.iframe(url, height=height, scrolling=True)
    else:
        st.warning(f"No heatmap URL configured for {region}. Set TV_HEATMAP_{region.upper()}_AUTH_URL or _PUBLIC_URL.")

def render_login_helper():
    st.markdown("""
**TradingView Login**
- If you're already logged into TradingView in this browser, authenticated iframes will load your layouts/watchlists.
- If you see public data, open TradingView, sign in, then refresh this tab.
- Some browsers block third‑party cookies; allow cookies for `tradingview.com` for authenticated iframes.
""")
    st.link_button("Open TradingView Sign In", "https://www.tradingview.com/#signin")

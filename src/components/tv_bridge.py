# src/components/tv_bridge.py (refreshable)
from __future__ import annotations
import os, json, urllib.parse, time
import streamlit as st
from streamlit.components.v1 import html

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

def _studies_from_codes(codes):
    codes = codes or DEFAULT_STUDIES
    names = [CODE_MAP.get(c, c) for c in codes]
    studies, overrides = [], {}
    for name in names:
        if name in OVERLAY_CODES:
            study, length = OVERLAY_CODES[name]
            studies.append(study)
            if length: overrides[f"{study}.length"] = length
    return studies, overrides

def tv_embed_url(symbol: str, interval: str = "D", theme: str = "dark", ts: int | None = None) -> str:
    tmpl = os.getenv("TV_EMBED_TEMPLATE", "")
    symbol_q = urllib.parse.quote(symbol, safe=":/")
    if tmpl:
        url = (tmpl.replace("{SYMBOL}", symbol_q).replace("{INTERVAL}", interval).replace("{THEME}", theme))
    else:
        params = {"symbol": symbol_q, "interval": interval, "theme": theme, "hide_top_toolbar": "0", "hide_legend": "0"}
        url = "https://s.tradingview.com/widgetembed/?" + urllib.parse.urlencode(params)
    if ts is None: ts = int(time.time())
    sep = "&" if ("?" in url) else "?"
    return f"{url}{sep}ts={ts}"

def tv_heatmap_url(region: str = "USA", prefer_auth: bool = True, ts: int | None = None) -> str | None:
    key = region.upper().replace(" ","_")
    auth_url = os.getenv(f"TV_HEATMAP_{key}_AUTH_URL", "")
    pub_url  = os.getenv(f"TV_HEATMAP_{key}_PUBLIC_URL", "")
    url = (auth_url if (prefer_auth and auth_url) else (pub_url or None))
    if not url: return None
    if ts is None: ts = int(time.time())
    sep = "&" if ("?" in url) else "?"
    return f"{url}{sep}ts={ts}"

def render_refresh_bar(label="↻ Refresh after TradingView sign‑in"):
    if st.button(label, type="primary"):
        st.session_state["_tv_ts"] = int(time.time())
        st.experimental_rerun()

def render_chart(symbol: str, interval: str = "D", theme: str = "dark", height: int = 600, overlays=None, mode: str = "auto"):
    if not symbol:
        st.info("Select a symbol to show TradingView."); return
    ts = st.session_state.get("_tv_ts", int(time.time()))
    if mode == "auto":
        mode = "tvjs" if overlays else "iframe"
    if mode == "iframe":
        url = tv_embed_url(symbol, interval=interval, theme=theme, ts=ts)
        st.components.v1.iframe(url, height=height, scrolling=True, key=f"tv_iframe_{ts}")
        render_refresh_bar()
        return
    studies, overrides = _studies_from_codes(overlays or [])
    cfg = {"symbol": symbol, "interval": interval, "timezone": "Etc/UTC", "theme": theme, "style": "1",
           "locale": "en", "studies": studies, "allow_symbol_change": True, "withdateranges": True,
           "details": True, "hotlist": True, "calendar": True, "autosize": True, "container_id": "tv_chart"}
    if overrides: cfg["studies_overrides"] = overrides
    html(f"""<div id="tv_chart" style="height:{height}px;"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script> new TradingView.widget({json.dumps(cfg)}); </script>""", height=height, key=f"tv_js_{ts}")
    render_refresh_bar()

def render_heatmap(region: str = "USA", height: int = 520):
    ts = st.session_state.get("_tv_ts", int(time.time()))
    url = tv_heatmap_url(region, prefer_auth=True, ts=ts) or tv_heatmap_url(region, prefer_auth=False, ts=ts)
    if url:
        st.components.v1.iframe(url, height=height, scrolling=True, key=f"tv_heatmap_{region}_{ts}")
        render_refresh_bar("↻ Refresh heatmap")
    else:
        st.warning(f"No heatmap URL configured for {region}. Set TV_HEATMAP_{region.upper()}_AUTH_URL or _PUBLIC_URL.")

def render_login_helper():
    st.markdown("""**TradingView Login**
- Keep this cockpit tab open.
- In a new tab, open TradingView and **sign in**.
- Return here and click **Refresh after TradingView sign‑in**.
- If you still see public data, allow third‑party cookies for `tradingview.com` / `s.tradingview.com` in your browser.
""")
    st.link_button("Open TradingView Sign In", "https://www.tradingview.com/#signin")

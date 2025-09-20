
# src/components/tv_bridge.py
from __future__ import annotations
import os, urllib.parse
import streamlit as st

# ---------- URL Builders ----------
def tv_embed_url(symbol: str, interval: str = "D", theme: str = "dark", height: int = 900, overlays: list[str] | None = None) -> str:
    """Build a TradingView widget URL.
    If TV_EMBED_TEMPLATE is set (e.g. 'https://s.tradingview.com/widgetembed/?symbol={SYMBOL}&interval={INTERVAL}&theme={THEME}'),
    we substitute values. Otherwise we fall back to a generic widget link.
    """
    tmpl = os.getenv("TV_EMBED_TEMPLATE", "")
    symbol_q = urllib.parse.quote(symbol, safe=":/")
    if tmpl:
        return (tmpl
                .replace("{SYMBOL}", symbol_q)
                .replace("{INTERVAL}", interval)
                .replace("{THEME}", theme))
    # Generic fallback (public widget)
    params = {
        "symbol": symbol_q,
        "interval": interval,
        "theme": theme,
        "hide_top_toolbar": "0",
        "hide_legend": "0",
    }
    return "https://s.tradingview.com/widgetembed/?" + urllib.parse.urlencode(params)

def tv_heatmap_url(region: str = "USA", prefer_auth: bool = True) -> str | None:
    region_key = region.upper().replace(" ", "_")
    auth_url = os.getenv(f"TV_HEATMAP_{region_key}_AUTH_URL", "")
    pub_url  = os.getenv(f"TV_HEATMAP_{region_key}_PUBLIC_URL", "")
    if prefer_auth and auth_url:
        return auth_url
    return pub_url or None

# ---------- Renderers ----------
def render_chart(symbol: str, interval: str = "D", theme: str = "dark", height: int = 600, overlays: list[str] | None = None):
    if not symbol:
        st.info("Select a symbol to show TradingView."); return
    url = tv_embed_url(symbol, interval=interval, theme=theme, height=height, overlays=overlays or [])
    st.components.v1.iframe(url, height=height, scrolling=True)

def render_heatmap(region: str = "USA", height: int = 520):
    url = tv_heatmap_url(region, prefer_auth=True) or tv_heatmap_url(region, prefer_auth=False)
    if url:
        st.components.v1.iframe(url, height=height, scrolling=True)
    else:
        st.warning(f"No heatmap URL configured for {region}. Set TV_HEATMAP_{region.upper()}_AUTH_URL or _PUBLIC_URL.")

# ---------- Login Helper ----------
def render_login_helper():
    st.markdown("""
    **TradingView Login**  
    - If you are already logged into TradingView *in this browser*, authenticated embeds will load automatically.  
    - If you see limited/public data, click the button below to open TradingView and sign in, then return here and refresh.  
    - Some browsers block third‑party cookies by default; you may need to allow cookies for `tradingview.com` to view authenticated iframes.
    """)
    st.link_button("Open TradingView Sign In", "https://www.tradingview.com/#signin")

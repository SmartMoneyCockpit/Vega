# src/components/tv_bridge.py — TradingView tv.js bridge (built-ins only, Heikin-Ashi, colored EMAs)
from __future__ import annotations
import os, json, urllib.parse, time
import streamlit as st
from streamlit.components.v1 import html

# === Built-in studies we support ===
# We'll pass per-instance "inputs" so each EMA gets its own length.
BUILTINS = {
    "EMA 9":      {"id": "MAExp@tv-basicstudies", "inputs": {"length": 9},   "plot_color": "#1e90ff"},  # blue
    "EMA 21":     {"id": "MAExp@tv-basicstudies", "inputs": {"length": 21},  "plot_color": "#001f5b"},  # navy
    "EMA 50":     {"id": "MAExp@tv-basicstudies", "inputs": {"length": 50},  "plot_color": "#ff0000"},  # red
    "EMA 200":    {"id": "MAExp@tv-basicstudies", "inputs": {"length": 200}, "plot_color": "#ffffff"},  # white
    "Bollinger (20,2)": {"id": "BollingerBands@tv-basicstudies", "inputs": {"length": 20, "mult": 2}},
    "Ichimoku (9/26/52)": {"id": "IchimokuCloud@tv-basicstudies", "inputs": {"conversion": 9, "base": 26, "span": 52, "displacement": 26}},
    "MACD (12/26/9)": {"id": "MACD@tv-basicstudies", "inputs": {"fastLength": 12, "slowLength": 26, "signalLength": 9}},
    "RSI (14)":    {"id": "RSI@tv-basicstudies", "inputs": {"length": 14}},
    "OBV":         {"id": "OBV@tv-basicstudies", "inputs": {}},
    "ATR (14)":    {"id": "ATR@tv-basicstudies", "inputs": {"length": 14}},
}

# Default overlays when the page loads (codes map below)
DEFAULT_STUDIES = [s.strip() for s in (os.getenv("TV_DEFAULT_STUDIES", "e9,e21,e50,e200,bb,ichi,macd,rsi,obv,atr")).split(",") if s.strip()]

CODE_TO_NAME = {
    "e9":"EMA 9","e21":"EMA 21","e50":"EMA 50","e200":"EMA 200",
    "bb":"Bollinger (20,2)","ichi":"Ichimoku (9/26/52)",
    "macd":"MACD (12/26/9)","rsi":"RSI (14)","obv":"OBV","atr":"ATR (14)"
}

def _cachebust_url(url: str) -> str:
    ts = int(time.time())
    sep = '&' if ('?' in url) else '?'
    return f"{url}{sep}ts={ts}"

def tv_embed_url(symbol: str, interval: str='D', theme: str='dark') -> str:
    tmpl = os.getenv('TV_EMBED_TEMPLATE', '')
    symbol_q = urllib.parse.quote(symbol, safe=':/')
    if tmpl:
        return (tmpl.replace('{SYMBOL}', symbol_q).replace('{INTERVAL}', interval).replace('{THEME}', theme))
    params = {'symbol': symbol_q, 'interval': interval, 'theme': theme, 'hide_top_toolbar': '0', 'hide_legend': '0'}
    return 'https://s.tradingview.com/widgetembed/?' + urllib.parse.urlencode(params)

def tv_heatmap_url(region: str='USA', prefer_auth: bool=True) -> str | None:
    key = region.upper().replace(' ','_')
    auth_url = os.getenv(f'TV_HEATMAP_{key}_AUTH_URL', '')
    pub_url  = os.getenv(f'TV_HEATMAP_{key}_PUBLIC_URL', '')
    if prefer_auth and auth_url: return auth_url
    return pub_url or None

def render_refresh_bar(label='Refresh after TradingView sign-in'):
    if st.button(label):
        st.rerun()

def _names_from_codes(codes):
    return [CODE_TO_NAME.get(c, c) for c in (codes or DEFAULT_STUDIES)]

def _build_studies_and_overrides(names):
    """Return (studies_list, studies_overrides) suitable for TradingView.widget config.

    studies_list: list of dicts like {"id": "...", "inputs": {...}}
    studies_overrides: per-instance style overrides using the instance index suffix .0, .1, ...
    """
    studies = []
    overrides = {}

    # Track how many times we've added a given study id to compute the instance index
    id_counts = {}

    for name in names:
        spec = BUILTINS.get(name)
        if not spec:
            continue
        study_id = spec["id"]
        inputs = spec.get("inputs", {}) or {}
        # Append as an object with inputs (CRITICAL for unique EMA lengths)
        studies.append({"id": study_id, "inputs": inputs})

        # Instance index for overrides (EMA colors, linewidths)
        idx = id_counts.get(study_id, 0)
        id_counts[study_id] = idx + 1

        color = spec.get("plot_color")
        if color is not None:
            overrides[f"{study_id}.{idx}.plot_0.color"] = color
            overrides[f"{study_id}.{idx}.plot_0.linewidth"] = 2

    return studies, overrides

def render_chart(symbol: str, interval: str='D', theme: str='dark', height: int=600, overlays=None, mode: str='auto'):
    if not symbol:
        st.warning("No symbol provided.")
        return

    # iframe mode (uses TradingView hosted embed)
    if mode == 'iframe':
        url = _cachebust_url(tv_embed_url(symbol, interval=interval, theme=theme))
        html(f'<iframe src="{url}" height="{height}" width="100%" frameborder="0" style="border:0;" scrolling="yes"></iframe>', height=height)
        render_refresh_bar("Refresh after TradingView sign-in")
        return

    # tv.js mode (full control over built-ins)
    study_names = _names_from_codes(overlays)
    studies, overrides = _build_studies_and_overrides(study_names)

    cfg = {
        "symbol": symbol,
        "interval": interval,
        "timezone": "Etc/UTC",
        "theme": theme,
        "style": "3",  # 3 = Heikin-Ashi (requested)
        "locale": "en",
        "withdateranges": True,
        "allow_symbol_change": True,
        "details": True,
        "hotlist": False,
        "calendar": True,
        "autosize": True,
        "container_id": "tv_chart",
        "studies": studies,
    }
    if overrides:
        cfg["studies_overrides"] = overrides

    # Render container + script
    html(
        '<div id="tv_chart" style="height:%spx;"></div>'
        '<script src="https://s3.tradingview.com/tv.js"></script>'
        '<script> new TradingView.widget(%s); </script>' % (height, json.dumps(cfg)),
        height=height
    )

def render_heatmap(region: str='USA', height: int=520):
    url = tv_heatmap_url(region, prefer_auth=True) or tv_heatmap_url(region, prefer_auth=False)
    if url:
        url = _cachebust_url(url)
        html(f'<iframe src="{url}" height="{height}" width="100%" frameborder="0" style="border:0;" scrolling="yes"></iframe>', height=height)
        render_refresh_bar('Refresh heatmap')
    else:
        st.warning(f'No heatmap URL configured for {region}. Set TV_HEATMAP_{region.upper()}_AUTH_URL or _PUBLIC_URL.')

def render_login_helper():
    st.markdown(
        "**TradingView Login**\n"
        "- Keep this cockpit tab open.\n"
        "- If charts look logged-out, click the button below, sign in on TradingView, then click **Refresh** under the chart.\n"
        "- Allow third-party cookies for `tradingview.com` / `s.tradingview.com` in your browser."
    )
    st.link_button('Open TradingView Sign In', 'https://www.tradingview.com/#signin')

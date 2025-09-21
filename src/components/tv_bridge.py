# src/components/tv_bridge.py
from __future__ import annotations
import os, json, urllib.parse, time
import streamlit as st
from streamlit.components.v1 import html

# -------------------------------------------------------------------
# Utility helpers
# -------------------------------------------------------------------

def _cachebust_url(url: str) -> str:
    ts = int(time.time())
    sep = '&' if ('?' in url) else '?'
    return f"{url}{sep}ts={ts}"

def tv_embed_url(symbol: str, interval: str='D', theme: str='dark') -> str:
    tmpl = os.getenv('TV_EMBED_TEMPLATE', '')
    symbol_q = urllib.parse.quote(symbol, safe=':/')
    if tmpl:
        return (
            tmpl.replace('{SYMBOL}', symbol_q)
                .replace('{INTERVAL}', interval)
                .replace('{THEME}', theme)
        )
    params = {
        'symbol': symbol_q,
        'interval': interval,
        'theme': theme,
        'hide_top_toolbar': '0',
        'hide_legend': '0',
    }
    return 'https://s.tradingview.com/widgetembed/?' + urllib.parse.urlencode(params)

def tv_heatmap_url(region: str='USA', prefer_auth: bool=True) -> str | None:
    key = region.upper().replace(' ','_')
    auth_url = os.getenv(f'TV_HEATMAP_{key}_AUTH_URL', '')
    pub_url  = os.getenv(f'TV_HEATMAP_{key}_PUBLIC_URL', '')
    if prefer_auth and auth_url:
        return auth_url
    return pub_url or None

def render_refresh_bar(label='Refresh after TradingView sign-in'):
    if st.button(label):
        st.rerun()

# -------------------------------------------------------------------
# Chart rendering
# -------------------------------------------------------------------

def render_chart(symbol: str,
                 interval: str='D',
                 theme: str='dark',
                 height: int=600,
                 overlays=None,
                 mode: str='tvjs'):
    """Render a TradingView chart with built-in studies only."""

    if not symbol:
        st.warning("No symbol provided.")
        return

    # iframe mode just shows a saved layout (no control over studies)
    if mode == 'iframe':
        url = _cachebust_url(tv_embed_url(symbol, interval=interval, theme=theme))
        html(
            f'<iframe src="{url}" height="{height}" width="100%" frameborder="0" '
            f'style="border:0;" scrolling="yes"></iframe>',
            height=height
        )
        render_refresh_bar("Refresh after TradingView sign-in")
        return

    # --- tv.js mode: full control over built-ins ---
    studies = [
        # EMAs
        {"id": "MAExp@tv-basicstudies", "inputs": {"length": 9}},
        {"id": "MAExp@tv-basicstudies", "inputs": {"length": 21}},
        {"id": "MAExp@tv-basicstudies", "inputs": {"length": 50}},
        {"id": "MAExp@tv-basicstudies", "inputs": {"length": 200}},

        # Overlays
        {"id": "BollingerBands@tv-basicstudies", "inputs": {"length": 20, "mult": 2}},
        {"id": "IchimokuCloud@tv-basicstudies",
         "inputs": {"conversion": 9, "base": 26, "span": 52, "displacement": 26}},

        # Indicator panes
        {"id": "MACD@tv-basicstudies",
         "inputs": {"fastLength": 12, "slowLength": 26, "signalLength": 9}},
        {"id": "RSI@tv-basicstudies", "inputs": {"length": 14}},
        {"id": "OBV@tv-basicstudies", "inputs": {}},
        {"id": "ATR@tv-basicstudies", "inputs": {"length": 14}},
    ]

    # EMA colors per instance
    studies_overrides = {
        "MAExp@tv-basicstudies.0.plot_0.color": "#1e90ff",  # EMA 9 blue
        "MAExp@tv-basicstudies.0.plot_0.linewidth": 2,
        "MAExp@tv-basicstudies.1.plot_0.color": "#001f5b",  # EMA 21 navy
        "MAExp@tv-basicstudies.1.plot_0.linewidth": 2,
        "MAExp@tv-basicstudies.2.plot_0.color": "#ff0000",  # EMA 50 red
        "MAExp@tv-basicstudies.2.plot_0.linewidth": 2,
        "MAExp@tv-basicstudies.3.plot_0.color": "#ffffff",  # EMA 200 white
        "MAExp@tv-basicstudies.3.plot_0.linewidth": 2,
    }

    cfg = {
        "container_id": "tv_chart",
        "symbol": symbol,
        "interval": interval,
        "theme": theme,
        "style": 3,  # Heikin-Ashi candles
        "autosize": True,
        "timezone": "Etc/UTC",
        "locale": "en",
        "withdateranges": True,
        "allow_symbol_change": True,
        "details": True,
        "calendar": True,
        "studies": studies,
        "studies_overrides": studies_overrides,
        "overrides": {
            "paneProperties.legendProperties.showStudyTitles": True,
            "paneProperties.legendProperties.showStudyValues": True,
            "paneProperties.legendProperties.showSeriesOHLC": False,
        },
    }

    html(
        '<div id="tv_chart" style="height:%spx;"></div>'
        '<script src="https://s3.tradingview.com/tv.js"></script>'
        '<script>new TradingView.widget(%s);</script>' % (height, json.dumps(cfg)),
        height=height
    )

# -------------------------------------------------------------------
# Heatmap rendering
# -------------------------------------------------------------------

def render_heatmap(region: str='USA', height: int=520):
    """Render TradingView heatmap iframe (auth or public)."""
    url = tv_heatmap_url(region, prefer_auth=True) or tv_heatmap_url(region, prefer_auth=False)
    if url:
        url = _cachebust_url(url)
        html(
            f'<iframe src="{url}" height="{height}" width="100%" frameborder="0" '
            f'style="border:0;" scrolling="yes"></iframe>',
            height=height
        )
        render_refresh_bar('Refresh heatmap')
    else:
        st.warning(
            f'No heatmap URL configured for {region}. '
            f'Set TV_HEATMAP_{region.upper()}_AUTH_URL or _PUBLIC_URL.'
        )

# -------------------------------------------------------------------
# Login helper
# -------------------------------------------------------------------

def render_login_helper():
    st.markdown(
        "**TradingView Login**\n"
        "- Keep this cockpit tab open.\n"
        "- If charts look logged-out, click the button below, sign in on TradingView, then click **Refresh** under the chart.\n"
        "- Allow third-party cookies for `tradingview.com` / `s.tradingview.com` in your browser."
    )
    st.link_button('Open TradingView Sign In', 'https://www.tradingview.com/#signin')

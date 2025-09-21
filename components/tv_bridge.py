# src/components/tv_bridge.py
from __future__ import annotations
import os, json, urllib.parse, time
import streamlit as st
from streamlit.components.v1 import html

def _cachebust_url(url: str) -> str:
    ts = int(time.time()); sep = '&' if ('?' in url) else '?'
    return f"{url}{sep}ts={ts}"

# --- PUBLIC widget URL (2-indicator limit) -------------------------------
def tv_public_embed_url(symbol: str, interval: str='D', theme: str='dark') -> str:
    # Optional override template for the PUBLIC widget
    tmpl = os.getenv('TV_EMBED_TEMPLATE', '')
    symbol_q = urllib.parse.quote(symbol, safe=':/')
    if tmpl:
        return (tmpl.replace('{SYMBOL}', symbol_q)
                    .replace('{INTERVAL}', interval)
                    .replace('{THEME}', theme))
    params = dict(
        symbol=symbol_q, interval=interval, theme=theme,
        hide_top_toolbar='0', hide_legend='0',
        timezone="Etc/UTC", locale="en", withdateranges="1",
        allow_symbol_change="1", save_image="0", style="1",
    )
    return 'https://s.tradingview.com/widgetembed/?' + urllib.parse.urlencode(params)

# --- AUTHENTICATED account URL (mirrors your logged-in TV account) -------
def tv_authenticated_url(symbol: str) -> str:
    """
    Loads TradingView's full chart page. The browser will send your
    tradingview.com cookies, so you get your paid plan features (more indicators,
    saved layouts, etc.). If third-party cookies are blocked, it behaves like logged out.
    """
    # Optional override lets you hard-pin a specific layout/chart URL from TV
    tmpl = os.getenv('TV_IFRAME_URL_TEMPLATE', '')
    symbol_q = urllib.parse.quote(symbol, safe=':/')
    if tmpl:
        return tmpl.replace('{SYMBOL}', symbol_q)
    # Default: plain chart URL with the symbol
    return f"https://www.tradingview.com/chart/?symbol={symbol_q}&utm_source=vega&feature=embed"

def tv_heatmap_url(region: str='USA', prefer_auth: bool=True) -> str | None:
    key = region.upper().replace(' ','_')
    auth_url = os.getenv(f'TV_HEATMAP_{key}_AUTH_URL', '')
    pub_url  = os.getenv(f'TV_HEATMAP_{key}_PUBLIC_URL', '')
    if prefer_auth and auth_url:
        return auth_url
    return pub_url or None

def render_refresh_bar(label='Refresh after TradingView sign-in'):
    if st.button(label): st.rerun()

def render_chart(symbol: str, interval: str='D', theme: str='dark', height: int=600, overlays=None, mode: str='auto'):
    if not symbol:
        st.warning("No symbol provided."); return

    # --- NEW: real authenticated iframe when mode == 'iframe'
    if str(mode).lower() == 'iframe':
        url = _cachebust_url(tv_authenticated_url(symbol))
        html(
            f'<iframe src="{url}" height="{height}" width="100%" '
            f'frameborder="0" style="border:0;" scrolling="yes" '
            f'sandbox="allow-scripts allow-same-origin allow-popups"></iframe>',
            height=height
        )
        st.caption("Tip: If you still see only 2 indicators, allow third-party cookies for tradingview.com.")
        render_refresh_bar("Refresh after TradingView sign-in")
        return

    # --- PUBLIC 'auto' mode (unchanged): tv.js + built-ins ----------------
    studies_ids = [
        "MAExp@tv-basicstudies","MAExp@tv-basicstudies","MAExp@tv-basicstudies","MAExp@tv-basicstudies",
        "BollingerBands@tv-basicstudies","IchimokuCloud@tv-basicstudies",
        "MACD@tv-basicstudies","RSI@tv-basicstudies","OBV@tv-basicstudies","ATR@tv-basicstudies",
    ]
    studies_overrides = {
        "MAExp@tv-basicstudies.0.inputs.length": 9,
        "MAExp@tv-basicstudies.0.plot.color": "#1e90ff",
        "MAExp@tv-basicstudies.0.plot.linewidth": 2,
        "MAExp@tv-basicstudies.1.inputs.length": 21,
        "MAExp@tv-basicstudies.1.plot.color": "#001f5b",
        "MAExp@tv-basicstudies.1.plot.linewidth": 2,
        "MAExp@tv-basicstudies.2.inputs.length": 50,
        "MAExp@tv-basicstudies.2.plot.color": "#ff0000",
        "MAExp@tv-basicstudies.2.plot.linewidth": 2,
        "MAExp@tv-basicstudies.3.inputs.length": 200,
        "MAExp@tv-basicstudies.3.plot.color": "#ffffff",
        "MAExp@tv-basicstudies.3.plot.linewidth": 2,
        "BollingerBands@tv-basicstudies.0.inputs.length": 20,
        "BollingerBands@tv-basicstudies.0.inputs.mult": 2,
        "IchimokuCloud@tv-basicstudies.0.inputs.conversion": 9,
        "IchimokuCloud@tv-basicstudies.0.inputs.base": 26,
        "IchimokuCloud@tv-basicstudies.0.inputs.span": 52,
        "IchimokuCloud@tv-basicstudies.0.inputs.displacement": 26,
        "MACD@tv-basicstudies.0.inputs.fastLength": 12,
        "MACD@tv-basicstudies.0.inputs.slowLength": 26,
        "MACD@tv-basicstudies.0.inputs.signalLength": 9,
        "RSI@tv-basicstudies.0.inputs.length": 14,
        "ATR@tv-basicstudies.0.inputs.length": 14,
    }
    cfg = {
        "container_id": "tv_chart","symbol": symbol,"interval": interval,"theme": theme,
        "style": 3,"autosize": True,"timezone": "Etc/UTC","locale": "en",
        "withdateranges": True,"allow_symbol_change": True,"details": True,"calendar": True,
        "studies": studies_ids,"studies_overrides": studies_overrides,
        "overrides": {
            "paneProperties.legendProperties.showStudyTitles": True,
            "paneProperties.legendProperties.showStudyValues": True,
            "paneProperties.legendProperties.showSeriesOHLC": False,
        },
    }
    html(
        '''
        <div id="tv_chart" style="height:%spx;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
          (function() {
            window.vegaTV = new TradingView.widget(%s);
            window.addEventListener("message", function(e) {
              try {
                var d = e.data || {};
                if (d && d.type === "VEGA_SET_SYMBOL" && window.vegaTV && window.vegaTV.onChartReady) {
                  window.vegaTV.onChartReady(function() {
                    var sym = d.symbol || "%s";
                    var ivl = d.interval || "%s";
                    window.vegaTV.chart().setSymbol(sym, ivl);
                  });
                }
              } catch (err) {}
            }, false);
          })();
        </script>
        ''' % (height, json.dumps(cfg), symbol, interval),
        height=height
    )

def render_heatmap(region: str='USA', height: int=520):
    url = tv_heatmap_url(region, prefer_auth=True) or tv_heatmap_url(region, prefer_auth=False)
    if url:
        url = _cachebust_url(url)
        html(f'<iframe src="{url}" height="{height}" width="100%%" frameborder="0" style="border:0;" scrolling="yes"></iframe>', height=height)
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

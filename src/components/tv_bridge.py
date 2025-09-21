"""
components/tv_bridge.py — Authenticated iframe + public tv.js (compat-safe)
- `render_chart(..., mode="iframe")` uses TradingView /chart (authenticated)
- `render_chart(..., mode="auto")` uses public tv.js widget (2-indicator limit)
- `render_heatmap(..., height=...)` respects explicit height
- `render_login_helper(msg)` retained
- Accepts unknown kwargs for backward compatibility
"""
from typing import Optional, Iterable
import os, urllib.parse, json, time
import streamlit as st
import streamlit.components.v1 as components

CSS = """
<style>
.tradingview-wrap { width: 100%; }
.tradingview-wrap iframe { width: 100%; border: 0; }
</style>
"""

def _theme_color(theme: str) -> str:
    return "light" if str(theme).lower().startswith("l") else "dark"

def _h(v):
    try:
        return max(300, int(v))
    except Exception:
        return 900

def _cachebust(url: str) -> str:
    ts = int(time.time()); sep = '&' if ('?' in url) else '?'
    return f"{url}{sep}ts={ts}"

# ----------------- URLs -----------------

def tv_public_embed_url(symbol: str, interval: str='D', theme: str='dark') -> str:
    """Public widget (2-indicator limit)."""
    tmpl = os.getenv('TV_EMBED_TEMPLATE', '')
    symbol_q = urllib.parse.quote(symbol, safe=':/')
    if tmpl:
        return (tmpl.replace('{SYMBOL}', symbol_q)
                    .replace('{INTERVAL}', interval)
                    .replace('{THEME}', theme))
    params = dict(
        symbol=symbol_q, interval=interval, theme=theme,
        timezone="Etc/UTC", locale="en", withdateranges="1",
        allow_symbol_change="1", save_image="0", style="1",
        hide_top_toolbar="0", hide_legend="0"
    )
    return 'https://s.tradingview.com/widgetembed/?' + urllib.parse.urlencode(params)

def tv_authenticated_url(symbol: str) -> str:
    """Real TradingView chart page (mirrors logged-in account features)."""
    tmpl = os.getenv('TV_IFRAME_URL_TEMPLATE', '')
    symbol_q = urllib.parse.quote(symbol, safe=':/')
    if tmpl:
        return tmpl.replace('{SYMBOL}', symbol_q)
    return f"https://www.tradingview.com/chart/?symbol={symbol_q}&utm_source=vega&feature=embed"

# ----------------- UI helpers -----------------

def render_login_helper(message: Optional[str] = None):
    with st.expander("About TradingView Embeds / Auth vs Public", expanded=False):
        st.markdown("""
- **Public widgets** load without login and are safe for demos (2-indicator cap).
- **Authenticated embeds** mirror your TradingView account (more indicators, saved layouts).
If you expected a private layout and see a public one, you're in **Public mode**.
        """.strip())
        if message:
            st.info(message)

# ----------------- Main renderers -----------------

def render_chart(symbol: str = "NASDAQ:QQQ",
                 interval: str = "D",
                 theme: str = "dark",
                 height: int = 980,
                 overlays: Optional[Iterable[str]] = None,
                 mode: str = "auto",
                 **kwargs):
    theme = _theme_color(theme)
    height = _h(height)
    st.markdown(CSS, unsafe_allow_html=True)

    if str(mode).lower() == "iframe":
        # --- AUTHENTICATED IFRAME PATH ---
        url = _cachebust(tv_authenticated_url(symbol))
        # Debug caption so you can verify we're on /chart/ not /widgetembed/
        st.caption(f"Using authenticated URL: {tv_authenticated_url(symbol)}")
        components.html(
            f'<iframe src="{url}" height="{height}" width="100%" '
            f'frameborder="0" style="border:0;" scrolling="yes" '
            f'sandbox="allow-scripts allow-same-origin allow-popups"></iframe>',
            height=height,
            scrolling=True
        )
        st.caption("Tip: If you still see only 2 indicators, allow third-party cookies for tradingview.com on this domain.")
        return

    # --- PUBLIC tv.js PATH (kept for compatibility / other pages) ---
    tv_interval = {"1":"1", "5":"5", "15":"15", "60":"60", "D":"D", "W":"W", "M":"M"}.get(interval, "D")
    cfg = {
        "width": "100%",
        "height": height,
        "symbol": symbol,
        "interval": tv_interval,
        "timezone": "Etc/UTC",
        "theme": theme,
        "style": "1",
        "locale": "en",
        "toolbar_bg": "rgba(0,0,0,0)",
        "enable_publishing": False,
        "hide_top_toolbar": False,
        "withdateranges": True,
        "save_image": False,
        "container_id": "tv_chart_container"
    }
    components.html(
        f"""
        <div class="tradingview-wrap" style="height:{height}px;">
          <div class="tradingview-widget-container">
            <div id="tv_chart_container"></div>
          </div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
            new TradingView.widget({json.dumps(cfg)});
          </script>
        </div>
        """,
        height=height,
        scrolling=False
    )

def render_heatmap(market: str = "US", theme: str = "dark", height: int = 620):
    theme = _theme_color(theme)
    height = _h(height)
    st.markdown(CSS, unsafe_allow_html=True)
    components.html(
        f"""
        <div class="tradingview-wrap" style="height:{height}px;">
          <div class="tradingview-widget-container">
            <div class="tradingview-widget-container__widget"></div>
          </div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js" async>
          {{
            "exchanges": ["{market.upper()}"],
            "dataSource": "SPX500",
            "grouping": "sector",
            "blockSize": "market_cap_basic",
            "blockColor": "change",
            "locale": "en",
            "colorTheme": "{theme}",
            "hasTopBar": true,
            "isDataSetEnabled": false,
            "isZoomEnabled": true
          }}
          </script>
        </div>
        """,
        height=height,
        scrolling=False
    )

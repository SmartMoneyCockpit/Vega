
"""
components/tv_bridge.py — public TradingView widgets
Now supports:
- render_chart(symbol, interval, theme, height=820, overlays=None, mode='auto')
- render_heatmap(market, theme, height=620)
Any extra keywords are ignored safely to stay backward compatible.
"""
from typing import Optional, Iterable
import streamlit as st
import streamlit.components.v1 as components

WIDGET_CONTAINER_STYLE = """
<style>
.tradingview-wrap { width: 100%; }
.tradingview-wrap iframe { width: 100%; min-height: 520px; border: 0; }
.small iframe { min-height: 420px; }
</style>
"""

def _theme_color(theme: str) -> str:
    return "light" if str(theme).lower().startswith("l") else "dark"

def _coerce_height(h):
    try:
        return max(400, int(h))
    except Exception:
        return 820

def render_login_helper(message: Optional[str] = None):
    with st.expander("About TradingView Embeds / Auth vs Public", expanded=False):
        st.markdown("""
- **Public widgets** load without login and are safe for demos.
- **Authenticated embeds** (coming later) mirror your private layouts.
- If you expected your private layout and see a public widget instead, we're currently in **Public mode**.
        """.strip())
        if message:
            st.info(message)

def render_chart(symbol: str = "NASDAQ:QQQ",
                 interval: str = "D",
                 theme: str = "dark",
                 height: int = 820,
                 overlays: Optional[Iterable[str]] = None,
                 mode: str = "auto",
                 **kwargs):
    """
    Public TradingView symbol chart.
    - `height` controls the iframe height.
    - `overlays` accepted for API compatibility but not used by public widget.
    - `mode` accepted for compatibility ("auto" / "iframe"); ignored here.
    """
    theme = _theme_color(theme)
    height = _coerce_height(height)
    tv_interval = {"1":"1", "5":"5", "15":"15", "60":"60", "D":"D", "W":"W", "M":"M"}.get(interval, "D")
    st.markdown(WIDGET_CONTAINER_STYLE, unsafe_allow_html=True)
    html = f"""
    <div class="tradingview-wrap">
      <div class="tradingview-widget-container">
        <div id="tv_chart_container"></div>
      </div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "autosize": true,
          "symbol": "{symbol}",
          "interval": "{tv_interval}",
          "timezone": "Etc/UTC",
          "theme": "{theme}",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "rgba(0, 0, 0, 0)",
          "enable_publishing": false,
          "hide_top_toolbar": false,
          "withdateranges": true,
          "save_image": false,
          "container_id": "tv_chart_container"
        }});
      </script>
    </div>
    """
    components.html(html, height=height, scrolling=False)

def render_heatmap(market: str = "US", theme: str = "dark", height: int = 620):
    theme = _theme_color(theme)
    height = _coerce_height(height)
    st.markdown(WIDGET_CONTAINER_STYLE, unsafe_allow_html=True)
    html = f"""
    <div class="tradingview-wrap small">
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
        "symbolUrl": "",
        "colorTheme": "{theme}",
        "hasTopBar": true,
        "isDataSetEnabled": false,
        "isZoomEnabled": true
      }}
      </script>
    </div>
    """
    components.html(html, height=height, scrolling=False)

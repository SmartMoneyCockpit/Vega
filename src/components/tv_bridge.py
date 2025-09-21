
"""
components/tv_bridge.py
A lightweight TradingView embedding bridge so pages can import:
    - render_chart
    - render_heatmap
    - render_login_helper
This avoids missing-import crashes on Render when authenticated embeds are not ready.
"""
from typing import Optional
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

def render_login_helper(message: Optional[str] = None):
    """Small helper panel explaining Auth vs Public mode; safe to keep even if you don't use auth."""
    with st.expander("About TradingView Embeds / Auth vs Public", expanded=False):
        st.markdown("""
- **Public widgets** (this page) load without login and are safe for demos.
- **Authenticated embeds** can mirror your private layouts once the auth cookies are wired.
- If you expected your private layout and see a public widget instead, we're currently in **Public mode**.
        """.strip())
        if message:
            st.info(message)

def render_chart(symbol: str = "NASDAQ:QQQ", interval: str = "D", theme: str = "dark", height: int = 560):
    """
    Renders a TradingView symbol chart using the lightweight public widget.
    interval: "1" (1m), "5", "15", "60", "D", "W", "M"
    """
    theme = _theme_color(theme)
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
    """
    Renders TradingView heatmap widget. market options examples: "US", "WORLD", "EU", "CN", "JP"
    """
    theme = _theme_color(theme)
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


"""
components/tv_bridge.py — FORCE HEIGHT PATCH
- Removes `autosize:true` and sets explicit `"height": <height>` for TradingView widget.
- Ensures the outer iframe is also set to the same height.
This fixes cases where the widget stayed short regardless of the Streamlit iframe height.
"""
from typing import Optional, Iterable
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

def render_chart(symbol: str = "NASDAQ:QQQ",
                 interval: str = "D",
                 theme: str = "dark",
                 height: int = 980,
                 **kwargs):
    theme = _theme_color(theme)
    height = _h(height)
    tv_interval = {"1":"1", "5":"5", "15":"15", "60":"60", "D":"D", "W":"W", "M":"M"}.get(interval, "D")
    st.markdown(CSS, unsafe_allow_html=True)
    html = f"""
    <div class="tradingview-wrap">
      <div class="tradingview-widget-container">
        <div id="tv_chart_container"></div>
      </div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "width": "100%",
          "height": {height},
          "symbol": "{symbol}",
          "interval": "{tv_interval}",
          "timezone": "Etc/UTC",
          "theme": "{theme}",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "rgba(0,0,0,0)",
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
    height = _h(height)
    st.markdown(CSS, unsafe_allow_html=True)
    html = f"""
    <div class="tradingview-wrap">
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
    """
    components.html(html, height=height, scrolling=False)

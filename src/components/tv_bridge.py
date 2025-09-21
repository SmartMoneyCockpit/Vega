
"""
components/tv_bridge.py — Forced height + login helper (compat-safe)
- `render_chart(..., height=...)` sets an explicit widget height (no autosize)
- `render_heatmap(..., height=...)` respects explicit height
- `render_login_helper(msg)` restored for pages that import it
- Accepts and ignores unknown kwargs (e.g., overlays, mode) for backward compatibility
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

def render_login_helper(message: Optional[str] = None):
    """Small helper panel describing public vs authenticated TradingView embeds."""
    with st.expander("About TradingView Embeds / Auth vs Public", expanded=False):
        st.markdown("""
- **Public widgets** load without login and are safe for demos.
- **Authenticated embeds** mirror your private layouts once cookies are wired.
If you expected a private layout and see a public one, you're in **Public mode**.
        """.strip())
        if message:
            st.info(message)

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
                 overlays: Optional[Iterable[str]] = None,
                 mode: str = "auto",
                 **kwargs):
    theme = _theme_color(theme)
    height = _h(height)
    tv_interval = {"1":"1", "5":"5", "15":"15", "60":"60", "D":"D", "W":"W", "M":"M"}.get(interval, "D")
    st.markdown(CSS, unsafe_allow_html=True)
    html = f"""
    <div class="tradingview-wrap" style="height:{height}px;">
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
    """
    components.html(html, height=height, scrolling=False)

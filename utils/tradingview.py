"""
Helper functions to embed TradingView widgets in Streamlit.

TradingView does not provide an official Python API for charts, but it offers
embeddable HTML widgets.  The `get_embed_widget` function returns an HTML
string containing a TradingView mini‑chart for a specified symbol.  This HTML
can be rendered in Streamlit using `st.components.v1.html()`.
"""

from typing import Optional


def get_embed_widget(symbol: str, width: int = 700, height: int = 500, interval: str = "D") -> str:
    """Return HTML for an embeddable TradingView widget.

    Parameters
    ----------
    symbol : str
        The symbol to chart, e.g. "NYSE:SPY" or "NASDAQ:AAPL".
    width : int
        Width of the widget in pixels.
    height : int
        Height of the widget in pixels.
    interval : str
        Chart interval (D for daily, 60 for hourly, etc.).
    """
    return f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
      <div id="tradingview_{symbol}" style="height:{height}px;width:{width}px;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "width": {width},
          "height": {height},
          "symbol": "{symbol}",
          "interval": "{interval}",
          "timezone": "America/Mazatlan",
          "theme": "light",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "#f1f3f6",
          "enable_publishing": false,
          "hide_top_toolbar": false,
          "allow_symbol_change": true,
          "hide_legend": false
        }});
      </script>
    </div>
    <!-- TradingView Widget END -->
<<<<<<< HEAD
    """
=======
    """
>>>>>>> 1d7947d895ee627f5b66a78bde632d8d795e9410

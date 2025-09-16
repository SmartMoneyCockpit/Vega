import streamlit as st

def render_focus(symbol: str):
    """
    Show a single TradingView chart ONLY when toggle is on.
    When off, nothing is rendered and no space is reserved.
    """
    if not symbol:
        symbol = "SPY"

    show = st.toggle("Show focus chart", value=False, key="focus_toggle")
    if not show:
        return  # nothing rendered, zero height

    html = f"""
    <div class="tradingview-widget-container">
      <div id="tv_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "autosize": true,
          "symbol": "{symbol}",
          "interval": "D",
          "timezone": "Etc/UTC",
          "theme": "dark",
          "style": "1",
          "locale": "en",
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "container_id": "tv_chart"
        }});
      </script>
    </div>
    """
    st.components.v1.html(html, height=480)

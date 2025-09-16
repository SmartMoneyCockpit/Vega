import streamlit as st
def render_focus(symbol: str, collapsed: bool = True):
    if not symbol: symbol = "SPY"
    html = """
    <div class="tradingview-widget-container">
      <div id="tv_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({
          "autosize": true, "symbol": "%s", "interval": "D",
          "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "en",
          "toolbar_bg": "#222", "hide_side_toolbar": false, "allow_symbol_change": true,
          "container_id": "tv_chart"
        });
      </script>
    </div>
    """ % symbol
    with st.expander(f"Focus Chart — {symbol}", expanded=not collapsed):
        st.components.v1.html(html, height=480)

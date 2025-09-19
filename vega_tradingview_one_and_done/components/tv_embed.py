from streamlit.components.v1 import html

def tv_embed(symbol: str = "NASDAQ:AMZN", interval: str = "D", height: int = 610):
    html(f"""
    <div class="tradingview-widget-container">
      <div id="tvchart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "symbol": "{symbol}",
        "interval": "{interval}",
        "timezone": "exchange",
        "theme": "light",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "hide_top_toolbar": false,
        "hide_legend": false,
        "save_image": false,
        "container_id": "tvchart"
      }});
      </script>
    </div>
    """, height=height)

import streamlit as st

def render_focus(symbol: str) -> None:
    """
    Single TradingView chart:
    - Toggle hides/shows the chart (no space when hidden)
    - Size picker: Compact / Standard / Tall / Full
    """
    if not symbol:
        symbol = "SPY"

    show = st.toggle("Show focus chart", value=False, key=f"focus_toggle_{symbol}")
    if not show:
        return

    size_label = st.radio(
        "Chart height",
        options=["Compact", "Standard", "Tall", "Full"],
        index=1,
        horizontal=True,
        key=f"focus_height_choice_{symbol}",
    )
    height_map = {"Compact": 360, "Standard": 560, "Tall": 720, "Full": 900}
    height = height_map[size_label]

    hide_side_toolbar = True
    hide_top_toolbar  = False

    html = f"""
    <div class="tradingview-widget-container" style="height:{height}px;">
      <div id="tv_chart" style="height:{height}px;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "symbol": "{symbol}",
          "interval": "D",
          "locale": "en",
          "theme": "dark",
          "style": "1",
          "width": "100%",
          "height": {height},
          "hide_side_toolbar": {str(hide_side_toolbar).lower()},
          "hide_top_toolbar": {str(hide_top_toolbar).lower()},
          "allow_symbol_change": true,
          "container_id": "tv_chart"
        }});
      </script>
    </div>
    """
    st.components.v1.html(html, height=height + 12)

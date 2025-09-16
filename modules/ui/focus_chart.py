import streamlit as st

def render_focus(symbol: str) -> None:
    """
    Single TradingView chart:
    - Toggle hides/shows the chart (no space when hidden)
    - Size picker: Compact / Standard / Tall / Full
    """
    if not symbol:
        symbol = "SPY"

    show = st.toggle("Show focus chart", value=False, key="focus_toggle")
    if not show:
        return

    # Size picker
    size_label = st.radio(
        "Chart height",
        options=["Compact", "Standard", "Tall", "Full"],
        index=1,  # default: Standard
        horizontal=True,
        key="focus_height_choice",
    )
    height_map = {"Compact": 360, "Standard": 560, "Tall": 720, "Full": 900}
    height = height_map[size_label]

    # Optional toolbar trim for more vertical space
    hide_side_toolbar = True     # keeps it clean
    hide_top_toolbar  = False    # keep top toolbar (set True if you want maximum space)

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
    # Make Streamlit reserve just enough space for the chosen height
    st.components.v1.html(html, height=height + 12)

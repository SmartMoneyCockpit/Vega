import streamlit as st

def tv_widget_script():
    return "<script type=\"text/javascript\" src=\"https://s3.tradingview.com/tv.js\"></script>"

def chart_widget(symbol: str, theme: str="light", height: int = 600):
    html = f'''
    <div>
      {tv_widget_script()}
      <div id="tvchart"></div>
      <script type="text/javascript">
        new TradingView.widget({{
          "symbol": "{symbol}",
          "interval": "D",
          "timezone": "Etc/UTC",
          "theme": "{theme}",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "#f1f3f6",
          "enable_publishing": false,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "container_id": "tvchart",
          "autosize": true
        }});
      </script>
    </div>
    '''
    st.components.v1.html(html, height=height)

COUNTRY_HEATMAP_PATH = {
    "USA": "usa/", "Canada": "canada/", "Mexico": "mexico/",
    "Japan": "japan/", "Australia": "australia/", "Hong Kong": "hong-kong/", "China": "china/",
    "Europe": "europe/", "UK": "uk/", "Germany": "germany/", "France": "france/",
}

def heatmap_for_country(country: str):
    base = "https://www.tradingview.com/heatmap/stock/"
    path = COUNTRY_HEATMAP_PATH.get(country, "world/")
    html = f'<iframe src="{base}{path}" style="width:100%; height:650px; border:0;" loading="lazy"></iframe>'
    st.components.v1.html(html, height=650)

def screener_for_country(country: str, height: int = 600):
    slug = COUNTRY_HEATMAP_PATH.get(country, "world/").rstrip("/")
    url = f"https://www.tradingview.com/screener/{slug}/"
    html = f'<iframe src="{url}" style="width:100%; height:{height}px; border:0;" loading="lazy"></iframe>'
    st.components.v1.html(html, height=height)

def link_to_tv(symbol: str):
    st.markdown(f"[Open {symbol} on TradingV]()

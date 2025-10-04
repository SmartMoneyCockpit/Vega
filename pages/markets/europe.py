
import streamlit as st
st.title("Europe Trading")
st.caption("Placeholder: DAX example view.")
st.components.v1.html("""
<div class="tradingview-widget-container">
  <div id="tradingview_eu"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({
    "symbol":"XETR:DAX","interval":"D","timezone":"Etc/UTC","theme":"light","style":"1",
    "locale":"en","withdateranges":true,"allow_symbol_change":true,
    "studies":["RSI@tv-basicstudies","MAExp@tv-basicstudies","MASimple@tv-basicstudies"],
    "container_id":"tradingview_eu"
  });
  </script>
</div>
""", height=610)

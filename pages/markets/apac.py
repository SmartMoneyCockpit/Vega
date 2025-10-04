
    import streamlit as st
    def page():
        st.title("APAC Trading")
        st.caption("Placeholder until original is restored.")
        st.components.v1.html("""
<div class="tradingview-widget-container">
  <div id="tradingview_apac"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({
    "symbol":"TVC:NI225","interval":"D","timezone":"Etc/UTC","theme":"light","style":"1",
    "locale":"en","withdateranges":true,"allow_symbol_change":true,
    "studies":["RSI@tv-basicstudies","MAExp@tv-basicstudies","MASimple@tv-basicstudies"],
    "container_id":"tradingview_apac"
  });
  </script>
</div>
""", height=610)

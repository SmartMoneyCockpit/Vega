import streamlit as st
def render_focus(symbol: str):
    if not symbol: symbol='SPY'
    show=st.toggle('Show focus chart', value=False, key=f'focus_toggle_{symbol}')
    if not show: return
    size=st.radio('Chart height', ['Compact','Standard','Tall','Full'], index=1, horizontal=True, key=f'h_{symbol}')
    hm={'Compact':360,'Standard':560,'Tall':720,'Full':900}; h=hm[size]
    st.components.v1.html(f"""
    <div style='height:{h}px'>
      <div id='tv_chart' style='height:{h}px'></div>
      <script src='https://s3.tradingview.com/tv.js'></script>
      <script>new TradingView.widget({{"symbol":"{symbol}","interval":"D","theme":"dark","width":"100%","height":{h},"container_id":"tv_chart"}});</script>
    </div>""", height=h+12)

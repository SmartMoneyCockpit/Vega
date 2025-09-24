import streamlit as st

st.set_page_config(page_title='Vega Cockpit', layout='wide')
st.title('Vega Cockpit – Home')

st.write('Quick links:')

st.page_link('pages/01_North_America_Text_Dashboard.py', label='🌎 North America')
st.page_link('pages/02_Europe_Text_Dashboard.py',       label='🌍 Europe')
st.page_link('pages/02_APAC_Text_Dashboard.py',         label='🌏 APAC')
st.page_link('pages/10_IBKR_Scanner.py',                label='🧪 IBKR Scanner')
st.page_link('pages/10_TradingView_Bridge.py',          label='🔗 TradingView Bridge')
st.page_link('pages/99_Diagnostics.py',                 label='🧰 Diagnostics')

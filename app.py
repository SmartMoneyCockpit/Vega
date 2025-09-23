import streamlit as st
st.set_page_config(page_title='Vega Cockpit', layout='wide')
st.title('Vega Cockpit')

st.page_link('pages/00_Home.py', label='🏠 Home', icon='🏠')
st.page_link('pages/095_IB_Feed_Status.py', label='📡 IB Feed Status')
st.page_link('pages/096_IBKR_Ticker_ib.py', label='⏱️ IBKR Ticker (ib_insync)')
st.page_link('pages/101_North_America.py', label='🌎 North America')
st.page_link('pages/102_Europe.py', label='🌍 Europe')
st.page_link('pages/103_APAC.py', label='🌏 APAC')

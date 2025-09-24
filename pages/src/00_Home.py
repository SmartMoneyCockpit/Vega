# pages/00_Home.py
import streamlit as st
st.title("Vega Cockpit – Home")
st.write("Quick links:")
st.page_link('pages/090_IB_Feed_Status.py', label='📡 IB Feed Status')
st.page_link('pages/091_IBKR_Live_Ticker.py', label='⏱️ IBKR Live Ticker')
st.page_link('pages/101_North_America.py', label='🌎 North America')
st.page_link('pages/102_Europe.py', label='🌍 Europe')
st.page_link('pages/103_APAC.py', label='🌏 APAC')

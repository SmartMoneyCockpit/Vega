import streamlit as st
st.set_page_config(page_title='Home — Vega Cockpit', layout='wide')
st.title('Home — Vega Cockpit')
st.page_link('pages/01_North_America_Text_Dashboard.py', label='🌎 North America — Text Dashboard')
st.page_link('pages/02_Europe_Text_Dashboard.py',        label='🇪🇺 Europe — Text Dashboard')
st.page_link('pages/03_APAC_Text_Dashboard.py',          label='🌏 APAC — Text Dashboard')
st.page_link('pages/04_Screener_Text.py',                label='🧪 Screener — Text')
st.page_link('pages/10_IBKR_Scanner.py',                 label='🔌 IBKR Scanner')

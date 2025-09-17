import streamlit as st
st.set_page_config(page_title='Vega Cockpit', layout='wide')
try:
    st.switch_page('pages/00_Home.py')
except Exception:
    st.title('Vega Cockpit')
    st.page_link('pages/00_Home.py', label='➡️ Go to Home')

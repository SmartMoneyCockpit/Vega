import streamlit as st
from modules.ui.ibkr_scanner_panel import render
st.set_page_config(page_title='IBKR Scanner', layout='wide')
st.title('IBKR Stock Scanner (Environment-Aware)')
render()

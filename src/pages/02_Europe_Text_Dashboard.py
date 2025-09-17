import streamlit as st
from modules.ui.region_text_dashboard import render_region
st.set_page_config(page_title='Europe — Text Dashboard', layout='wide')
st.title('Europe — Vega Cockpit (Text)')
render_region('EU')

import streamlit as st
from modules.ui.region_text_dashboard import render_region
st.set_page_config(page_title='North America — Text Dashboard', layout='wide')
st.title('North America — Vega Cockpit (Text)')
render_region('NA')

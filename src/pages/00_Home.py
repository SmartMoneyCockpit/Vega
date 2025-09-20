import streamlit as st

st.set_page_config(page_title="Home — Vega Cockpit", layout="wide")
st.title("Home — Vega Cockpit")

st.page_link("src/pages/01_NA_Text_Dashboard.py",  label="• North America — Text Dashboard")
st.page_link("src/pages/02_Europe_Text_Dashboard.py", label="• Europe — Text Dashboard")
st.page_link("src/pages/03_APAC_Text_Dashboard.py",  label="• APAC — Text Dashboard")
st.page_link("src/pages/04_Screener_Text.py",        label="• Screener — Text")
# Add others as needed:
# st.page_link("src/pages/08_IBKR_Scanner.py",         label="• IBKR Scanner")

import streamlit as st

st.set_page_config(page_title="Home — Vega Cockpit", layout="wide")
st.title("Home — Vega Cockpit")

st.write("Choose a module from the sidebar:")
st.page_link("pages/01_North_America_Trading.py", label="🌎 North America Trading")
st.page_link("pages/02_Europe_Trading.py", label="🌍 Europe Trading")
st.page_link("pages/03_APAC_Trading.py", label="🌏 APAC Trading")
st.page_link("pages/04_IBKR_Scanner.py", label="🔎 IBKR Scanner")

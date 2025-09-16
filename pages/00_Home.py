import streamlit as st

st.set_page_config(page_title="Home — Vega Cockpit", layout="wide")
st.title("Home — Vega Cockpit")
st.caption("Choose a module from the sidebar or use the links below.")

# Links must be relative to the main script directory and the file
# must live inside the `pages/` folder.
st.page_link("pages/01_North_America_Text_Dashboard.py", label="🌎 North America — Text Dashboard")
st.page_link("pages/02_Europe_Text_Dashboard.py",        label="🇪🇺 Europe — Text Dashboard")
st.page_link("pages/03_APAC_Text_Dashboard.py",          label="🌏 APAC — Text Dashboard")
st.page_link("pages/10_IBKR_Scanner.py",                 label="🔌 IBKR Scanner")

# app.py — entry point for Vega Cockpit
import os
import importlib
import streamlit as st

# ✅ First Streamlit command in the app
st.set_page_config(
    page_title="Vega – Tradeability Meter",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Optional: Sidebar logo (safe even if file is missing)
logo_path = "assets/vega_cockpit_logo.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_column_width=True)

# Navigation (you can add more pages later)
st.sidebar.title("Vega Cockpit")
page = st.sidebar.radio(
    "Modules",
    ["Tradeability Meter"],  # Add more here when needed
    index=0
)

# Load selected module
if page == "Tradeability Meter":
    trade_meter = importlib.import_module("vega_tradeability_meter")
    trade_meter.run()

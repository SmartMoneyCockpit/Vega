# app.py — bootstraps the Tradeability Meter page

import os
import importlib
import streamlit as st

# Sidebar logo (safe even if file is missing)
logo_path = "assets/cockpit_logo.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_column_width=True)  # <-- works on Streamlit 1.35

# Load the meter app (USA/Canada/Mexico tabs)
importlib.import_module("vega_tradeability_meter")

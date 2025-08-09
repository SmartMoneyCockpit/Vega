# app.py — Vega cockpit entry point
import os
import importlib
import streamlit as st

# ✅ First Streamlit call
st.set_page_config(
    page_title="Vega – Cockpit",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Sidebar / Nav
st.sidebar.title("Vega Cockpit")
page = st.sidebar.radio(
    "Modules",
    [
        "Tradeability Meter",
        "Auto-Hedging Engine",
        "Macro Dashboard",
    ],
    index=0,
)

# ---- Lazy import per page (avoids import-time Streamlit calls)
if page == "Tradeability Meter":
    mod = importlib.import_module("vega_tradeability_meter")
    mod.run()

elif page == "Auto-Hedging Engine":
    mod = importlib.import_module("auto_hedging_engine")
    mod.run()

elif page == "Macro Dashboard":
    mod = importlib.import_module("macro_dashboard")
    mod.run()

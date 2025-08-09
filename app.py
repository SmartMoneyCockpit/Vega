# app.py — Vega cockpit entry point (session_state-safe nav)
import importlib
import streamlit as st

# ✅ First Streamlit call
st.set_page_config(
    page_title="Vega – Cockpit",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Sidebar / Nav (robust against stale session state)
NAV_OPTIONS = ["Tradeability Meter", "Auto-Hedging Engine", "Macro Dashboard"]

# Initialize nav state safely
if "nav" not in st.session_state or st.session_state.get("nav") not in NAV_OPTIONS:
    st.session_state["nav"] = NAV_OPTIONS[0]

default_index = NAV_OPTIONS.index(st.session_state.get("nav", NAV_OPTIONS[0]))

st.sidebar.title("Vega Cockpit")
page = st.sidebar.radio("Modules", NAV_OPTIONS, index=default_index, key="nav")

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

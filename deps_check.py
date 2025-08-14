"""
Simple dependency check that lists missing modules in the Streamlit UI instead of crashing.
Add near the top of app.py:
    from src.utils.deps_check import show_missing
    show_missing()
"""
import importlib, streamlit as st

MODULES = [
    "pandas","numpy","requests","pytz","pyyaml",
    "gspread","google.auth","googleapiclient.discovery",
    "yfinance","matplotlib","plotly","ta","scipy","statsmodels","cachetools",
    "newsapi","polygon","ib_insync","eventkit"
]

def show_missing():
    missing = []
    for m in MODULES:
        try:
            importlib.import_module(m)
        except Exception:
            missing.append(m)
    if missing:
        st.warning("Missing optional modules: " + ", ".join(missing) + 
                   ". The app will still run, but some features may be disabled. " +
                   "Add them to requirements.txt if you need those features.")

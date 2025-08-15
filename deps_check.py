"""
Soft dependency checker for Vega.

Usage (near the top of app.py):
    from src.utils.deps_check import show_missing
    show_missing()

Notes:
- We intentionally do NOT check for the Polygon SDK because the app uses REST calls.
- The import name for PyYAML is 'yaml' (not 'pyyaml'), so we check 'yaml'.
- If Streamlit isn't available (e.g., running a quick script), we print to stdout.
"""

import importlib

# Modules to try importing (import names, not pip names)
TRY_IMPORTS = [
    # Core
    "pandas", "numpy", "requests", "pytz", "yaml",
    # Google Sheets stack
    "gspread", "google.auth", "googleapiclient.discovery", "cachetools",
    # Market data / plotting
    "yfinance", "matplotlib", "plotly", "ta", "scipy", "statsmodels",
    # Optional extras you may enable later
    "ib_insync", "eventkit",
]

__all__ = ["show_missing"]

def show_missing() -> None:
    """Warn (non-fatal) about optional packages that aren't installed."""
    missing = []
    for name in TRY_IMPORTS:
        try:
            importlib.import_module(name)
        except Exception:
            missing.append(name)

    if not missing:
        return

    msg = (
        "Missing optional modules: " + ", ".join(missing) +
        ". The app will still run, but some features may be disabled. "
        "Add them to requirements.txt if you need those features."
    )

    try:
        import streamlit as st
        st.warning(msg)
    except Exception:
        print("[Vega] " + msg)

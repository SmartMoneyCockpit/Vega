<<<<<<< HEAD

import streamlit as st
import importlib

# Title and Sidebar
st.set_page_config(page_title="Smart Money Cockpit", layout="wide")
st.sidebar.image("assets/cockpit_logo.png", use_container_width=True)
st.sidebar.title("Smart Money Cockpit")

# List of available modules
module_titles = {
    "trade_logger": "Trade Logger",
    "daily_briefing": "Daily Briefing",
    "etf_dashboard": "ETF Dashboard",
    "pdf_generator": "PDF Report Generator",
    "journal_logger": "Journal",
    "strategy_builder": "Strategy Builder",
    "health_tracker": "Health Tracker",
    "pattern_profiler": "AI Pattern Profiler",
    "guardrails": "Capital Guardrails",
    "ai_journal": "Auto-Journal Generator",
    "vagal_sync": "Vagal Sync",
    "auto_hedger": "Auto Hedger",
    "preferred_income_tracker": "Preferred Income Tracker",
    "spy_contra_tracker": "SPY Contra Tracker",
    "macro_micro_dashboard": "Macro+Micro Dashboard",
    "smart_money_logic": "Smart Money Logic",
    "training_tier": "Training Tier",
    "boi_playbook": "BoJ Rate Playbook",
    "bear_mode_tail_risk": "Bear Mode Tail Risk",
    "tariff_aware_screener": "Tariff-Aware Screener"
}

# Sidebar module selector
selected_module = st.sidebar.selectbox(
    "Choose a module", list(module_titles.keys()), format_func=lambda x: module_titles[x])

# Load and render selected module
try:
    module = importlib.import_module(f"modules.{selected_module}")
    if hasattr(module, "render"):
        module.render()
    else:
        st.warning(f"Module '{selected_module}' is missing a render() function.")
except Exception as e:
    st.error(f"Failed to load module '{selected_module}': {e}")

# Optional: Show module status
if st.sidebar.checkbox("Show module status"):
    st.sidebar.markdown("### Loaded Modules")
    for key, title in module_titles.items():
        st.sidebar.markdown(f"- {title}")
=======
"""
Smart Money Cockpit
===================

This Streamlit application serves as a hub for trading, health and research
activities.  Modules can be selected from the sidebar, and their status
indicators display the readiness of each feature.  The app is designed to be
deployed locally or on Streamlit Cloud.
"""

import streamlit as st
from pathlib import Path
import pandas as pd

from modules import (
    render_trade_logger,
    render_smart_money_logic,
    render_health_tracker,
    render_daily_briefing,
    render_journal_logger,
    render_strategy_builder,
    render_pdf_generator,
    render_training_tier,
    render_macro_micro_dashboard,
    render_bear_mode_tail_risk,
    render_etf_dashboard,
    render_boj_playbook,
    render_tariff_aware_screener,
    render_preferred_income_tracker,
    render_live_pnl_tracker,
    render_spy_contra_tracker,
)
from utils import google_sheets, ibkr


def get_module_statuses() -> pd.DataFrame:
    """Return a DataFrame indicating whether each module is ready.

    For now, all modules are marked as ready.  You can extend this function to
    perform health checks (e.g. Google Sheets availability, IBKR connectivity).
    """
    modules = [
        "Trade Logger",
        "Smart Money Logic",
        "Health Tracker",
        "Daily Morning Briefing",
        "Journal Logger",
        "Strategy Builder",
        "PDF Generator",
        "Training Tier",
        "Macro/Micro Dashboard",
        "Bear Mode / Tail‑Risk",
        "ETF Dashboard",
        "BoJ Rate Playbook",
        "Tariff‑Aware Screener",
        "Preferred Income Tracker",
        "Live PnL Tracker",
        "SPY & Contra Tracker",
    ]
    statuses = []
    # Check Google Sheets connectivity
    sheet_ok = google_sheets.get_sheet() is not None
    # Check IBKR connectivity
    ib_ok = ibkr.connect() is not None
    for m in modules:
        if m == "Live PnL Tracker":
            ready = ib_ok
        else:
            ready = True
        statuses.append({"Module": m, "Status": "Ready" if ready else "Offline"})
    return pd.DataFrame(statuses)


def load_image(image_name: str):
    img_path = Path(__file__).resolve().parent / "assets" / image_name
    if img_path.exists():
        return open(img_path, "rb").read()
    return None


def main() -> None:
    st.set_page_config(page_title="Smart Money Cockpit", layout="wide")
    # Sidebar branding
    coin_img = load_image("coin.png")
    if coin_img:
        st.sidebar.image(coin_img, use_column_width=True)
    st.sidebar.title("Smart Money Cockpit")
    # Module selection
    module_names = [
        "Trade Logger",
        "Smart Money Logic",
        "Health Tracker",
        "Daily Morning Briefing",
        "Journal Logger",
        "Strategy Builder",
        "PDF Generator",
        "Training Tier",
        "Macro/Micro Dashboard",
        "Bear Mode / Tail‑Risk",
        "ETF Dashboard",
        "BoJ Rate Playbook",
        "Tariff‑Aware Screener",
        "Preferred Income Tracker",
        "Live PnL Tracker",
        "SPY & Contra Tracker",
    ]
    choice = st.sidebar.selectbox("Choose a module", module_names)
    # Module status display
    if st.sidebar.checkbox("Show module status", value=False):
        status_df = get_module_statuses()
        st.sidebar.dataframe(status_df, height=300)
    # Main content
    if choice == "Trade Logger":
        render_trade_logger()
    elif choice == "Smart Money Logic":
        render_smart_money_logic()
    elif choice == "Health Tracker":
        render_health_tracker()
    elif choice == "Daily Morning Briefing":
        render_daily_briefing()
    elif choice == "Journal Logger":
        render_journal_logger()
    elif choice == "Strategy Builder":
        render_strategy_builder()
    elif choice == "PDF Generator":
        render_pdf_generator()
    elif choice == "Training Tier":
        render_training_tier()
    elif choice == "Macro/Micro Dashboard":
        render_macro_micro_dashboard()
    elif choice == "Bear Mode / Tail‑Risk":
        render_bear_mode_tail_risk()
    elif choice == "ETF Dashboard":
        render_etf_dashboard()
    elif choice == "BoJ Rate Playbook":
        render_boj_playbook()
    elif choice == "Tariff‑Aware Screener":
        render_tariff_aware_screener()
    elif choice == "Preferred Income Tracker":
        render_preferred_income_tracker()
    elif choice == "Live PnL Tracker":
        render_live_pnl_tracker()
    elif choice == "SPY & Contra Tracker":
        render_spy_contra_tracker()
    else:
        st.write("Please select a module from the sidebar.")


if __name__ == "__main__":
    main()
>>>>>>> 1d7947d895ee627f5b66a78bde632d8d795e9410

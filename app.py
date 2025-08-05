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
    "tariff_aware_screener": "Tariff-Aware Screener",
    "live_pnl_tracker": "Live PnL Tracker"
}

# Sidebar module selector
selected_module = st.sidebar.selectbox(
    "Choose a module", list(module_titles.keys()), format_func=lambda x: module_titles[x]
)

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
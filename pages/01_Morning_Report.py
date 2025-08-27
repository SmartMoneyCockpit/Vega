# pages/01_Morning_Report.py
from datetime import datetime
import streamlit as st

# Load centralized preferences (reads config/vega_prefs.yaml + version.json)
from utils.load_prefs import load_prefs

# Morning Report modules
from modules.morning_report import MorningReport
from modules.data_providers import DemoDataProvider

# --- Page setup ---
st.set_page_config(page_title="Vega Morning Report", layout="wide")
prefs = load_prefs()  # single source of truth for feature switches

# --- Sidebar controls ---
st.sidebar.title("Vega Morning Report")
session_date = st.sidebar.date_input("Session Date", datetime.now().date())
regions = st.sidebar.multiselect(
    "Regions",
    ["USA", "Canada", "Mexico", "LatAm"],
    default=["USA", "Canada", "Mexico", "LatAm"],
)

show_sections = st.sidebar.multiselect(
    "Sections",
    [
        "Status Banner",
        "Macro Header",
        "Benchmark & Breadth Matrix",
        "Options & Skews",
        "Catalyst Board",
        "Session Map",
        "VectorVest Alt Color Guard",
        "Economic Calendar",
        "Final Risk Overlay",
    ],
    default=[
        "Status Banner",
        "Macro Header",
        "Benchmark & Breadth Matrix",
        "Session Map",
        "VectorVest Alt Color Guard",
        "Economic Calendar",
        "Final Risk Overlay",
    ],
)

# --- Data provider & report object ---
provider = DemoDataProvider()  # swap later for live provider
report = MorningReport(provider=provider, regions=regions, session_date=session_date)

# --- Render sections (must satisfy BOTH: sidebar selection AND prefs flag) ---

# Status Banner (guardrails + color guard quicklights)
if ("Status Banner" in show_sections) and prefs.enabled("morning_report", "status_banner", default=True):
    report.render_status_banner()

# Macro Header
if ("Macro Header" in show_sections) and prefs.enabled("morning_report", "macro_header", default=True):
    report.render_macro_header()

# Benchmark & Breadth Matrix
if ("Benchmark & Breadth Matrix" in show_sections) and prefs.enabled(
    "morning_report", "benchmark_breadth_matrix", default=True
):
    report.render_benchmark_and_breadth_matrix()

# Options & Skews (tied to strategy module availability)
if ("Options & Skews" in show_sections) and prefs.enabled(
    "strategy_modules", "ai_trade_quality_scorecard", default=True
):
    report.render_options_and_skews()

# Catalyst Board (tied to intelligence screener)
if ("Catalyst Board" in show_sections) and prefs.enabled(
    "intelligence", "ai_trade_idea_screener", default=True
):
    report.render_catalyst_board()

# Session Map (Roadmap for Today)
if ("Session Map" in show_sections) and prefs.enabled("morning_report", "session_map", default=True):
    report.render_session_map()

# VectorVest Alt Color Guard (Alt)
if ("VectorVest Alt Color Guard" in show_sections) and prefs.enabled(
    "morning_report", "vectorvest_color_guard", default=True
):
    report.render_color_guard_alt()

# Economic Calendar (Next 7 Days)
if ("Economic Calendar" in show_sections) and prefs.enabled("morning_report", "econ_calendar", default=True):
    report.render_econ_calendar()

# Final Risk Overlay & Action Plan
if ("Final Risk Overlay" in show_sections) and prefs.enabled("morning_report", "final_risk_overlay", default=True):
    report.render_final_risk_overlay()

# --- Footer: version stamp & module credit ---
st.caption(f"Prefs v{prefs.version} • updated {prefs.last_updated}")
st.caption("© Vega — Morning Report Module")

# pages/01_Morning_Report.py
from datetime import datetime
import streamlit as st

# Load centralized preferences (reads config/vega_prefs.yaml + version.json)
from utils.load_prefs import load_prefs

# Morning Report modules
from modules.morning_report import MorningReport
from modules.data_providers import DemoDataProvider

# ---------- Helpers ----------
def call_first_available(obj, method_candidates, *, section_name: str):
    """
    Tries a list of possible method names on `obj` and calls the first one that exists.
    Shows a friendly note if none exist so the page never crashes.
    """
    for m in method_candidates:
        fn = getattr(obj, m, None)
        if callable(fn):
            return fn()
    st.warning(
        f"⚠️ Skipping **{section_name}** — "
        f"none of the expected methods exist on MorningReport: {', '.join(method_candidates)}"
    )

# ---------- Page setup ----------
st.set_page_config(page_title="Vega Morning Report", layout="wide")
prefs = load_prefs()  # single source of truth for feature switches

# ---------- Sidebar controls ----------
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

# ---------- Data provider & report object ----------
provider = DemoDataProvider()  # swap later for live provider
report = MorningReport(provider=provider, regions=regions, session_date=session_date)

# ---------- Render sections (must satisfy BOTH: sidebar selection AND prefs flag) ----------

# Status Banner (guardrails + color guard quicklights)
if ("Status Banner" in show_sections) and prefs.enabled("morning_report", "status_banner", default=True):
    call_first_available(
        report,
        ["render_status_banner", "status_banner", "draw_status_banner", "show_status_banner"],
        section_name="Status Banner",
    )

# Macro Header
if ("Macro Header" in show_sections) and prefs.enabled("morning_report", "macro_header", default=True):
    call_first_available(
        report,
        ["render_macro_header", "macro_header", "draw_macro_header", "show_macro_header"],
        section_name="Macro Header",
    )

# Benchmark & Breadth Matrix
if ("Benchmark & Breadth Matrix" in show_sections) and prefs.enabled(
    "morning_report", "benchmark_breadth_matrix", default=True
):
    call_first_available(
        report,
        [
            "render_benchmark_and_breadth_matrix",
            "render_benchmark_breadth_matrix",
            "benchmark_and_breadth_matrix",
            "show_benchmark_breadth_matrix",
        ],
        section_name="Benchmark & Breadth Matrix",
    )

# Options & Skews (tied to strategy module availability)
if ("Options & Skews" in show_sections) and prefs.enabled(
    "strategy_modules", "ai_trade_quality_scorecard", default=True
):
    call_first_available(
        report,
        ["render_options_and_skews", "options_and_skews", "show_options_skews"],
        section_name="Options & Skews",
    )

# Catalyst Board (tied to intelligence screener)
if ("Catalyst Board" in show_sections) and prefs.enabled(
    "intelligence", "ai_trade_idea_screener", default=True
):
    call_first_available(
        report,
        ["render_catalyst_board", "catalyst_board", "show_catalyst_board"],
        section_name="Catalyst Board",
    )

# Session Map (Roadmap for Today)
if ("Session Map" in show_sections) and prefs.enabled("morning_report", "session_map", default=True):
    call_first_available(
        report,
        ["render_session_map", "session_map", "show_session_map"],
        section_name="Session Map",
    )

# VectorVest Alt Color Guard (Alt)
if ("VectorVest Alt Color Guard" in show_sections) and prefs.enabled(
    "morning_report", "vectorvest_color_guard", default=True
):
    call_first_available(
        report,
        ["render_color_guard_alt", "color_guard_alt", "show_color_guard_alt"],
        section_name="VectorVest Alt Color Guard",
    )

# Economic Calendar (Next 7 Days)
if ("Economic Calendar" in show_sections) and prefs.enabled("morning_report", "econ_calendar", default=True):
    call_first_available(
        report,
        ["render_econ_calendar", "econ_calendar", "show_econ_calendar"],
        section_name="Economic Calendar",
    )

# Final Risk Overlay & Action Plan
if ("Final Risk Overlay" in show_sections) and prefs.enabled("morning_report", "final_risk_overlay", default=True):
    call_first_available(
        report,
        ["render_final_risk_overlay", "final_risk_overlay", "show_final_risk_overlay"],
        section_name="Final Risk Overlay",
    )

# ---------- Footer: version stamp & module credit ----------
def _prefs_version_and_updated(_prefs_obj):
    vdict = getattr(_prefs_obj, "_version", {}) or {}
    pdict = getattr(_prefs_obj, "_prefs", {}) or {}

    ver = (
        getattr(_prefs_obj, "version", None)
        or vdict.get("version")
        or vdict.get("tag")
        or vdict.get("semver")
        or vdict.get("name")
        or pdict.get("version")
        or "unknown"
    )
    upd = (
        getattr(_prefs_obj, "last_updated", None)
        or vdict.get("last_updated")
        or vdict.get("updated_at")
        or pdict.get("last_updated")
        or pdict.get("updated_at")
        or "n/a"
    )
    return str(ver), str(upd)

_ver, _upd = _prefs_version_and_updated(prefs)
st.caption(f"Prefs v{_ver} • updated {_upd}")
st.caption("© Vega — Morning Report Module")

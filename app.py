# app.py — Vega Cockpit (Final Build, clean sidebar with dev-only legacy runner)

import os, json
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st

# --- Optional legacy import (no crash if missing) ---
try:
    from utils.prefs_bootstrap import prefs  # optional
except Exception:
    prefs = None

# --- Config loader (reads app.dev_mode from config.yaml) ---
def _load_config():
    try:
        import yaml  # PyYAML
        p = Path("config.yaml")
        if p.exists():
            return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        pass
    return {}

CFG = _load_config()
DEV_MODE = bool(CFG.get("app", {}).get("dev_mode", False))

# --- Page Meta ---
st.set_page_config(page_title="Vega Cockpit — Final Build", layout="wide")

# --- Status Bar (Risk / Guardrails) ---
risk = os.path.exists("vault/cache/risk_off.flag")
guardrails_path = "vault/cache/guardrails.json"
guard_alerts = 0
if os.path.exists(guardrails_path):
    try:
        with open(guardrails_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            guard_alerts = len(data.get("alerts", []))
    except Exception:
        pass

st.markdown(
    "<div style='padding:8px;border-radius:10px;background:#111;border:1px solid #333;'>"
    + "Market Risk: <b>{}</b> | ".format("RISK-OFF" if risk else "Neutral/On")
    + "Hedge: <b>{}</b> | ".format("ON" if risk else "AUTO")
    + "Guardrails Alerts: <b>{}</b>".format(guard_alerts)
    + "</div>",
    unsafe_allow_html=True,
)

# --- Sidebar (CLEAN v2) ---
with st.sidebar:
    st.title("Vega — Final Build")

    # Dashboards (new)
    with st.expander("Dashboards", expanded=True):
        pick = st.radio(
            "Open panel",
            [
                "Breadth Panel",
                "VectorVest Screeners",
                "ETF Tactical",
                "Guardrails Gauges",
                "IBKR Charts",
                "APAC Dashboard",
                "One-Click Daily Report",
            ],
            index=0,
            label_visibility="collapsed",
        )

    # Trade Tools
    with st.expander("Trade Tools", expanded=False):
        tools_pick = st.radio(
            "Tools",
            [
                "Options Helper",
                "AI Trade Quality Scorecard",
                "Backtest Mode",
                "AI Pattern Profiler",
            ],
            index=0,
            label_visibility="collapsed",
        )

    # Region Filters
    with st.expander("Region Filters", expanded=False):
        region_pick = st.radio(
            "Region",
            [
                "Canada Filters",
            ],
            index=0,
            label_visibility="collapsed",
        )

    # --- DEV-ONLY: Legacy runner (hidden in production) ---
    if DEV_MODE:
        st.divider()
        st.subheader("Legacy (v1.x) — Dev Only")
        st.caption("Use the inline runner to open archived scripts under ./legacy/")
        legacy_options = _list_legacy_scripts()
        legacy_sel = st.selectbox(
            "Select a legacy UI script",
            legacy_options if legacy_options else ["<none found>"],
            index=0,
        )
        if st.button("Open legacy UI script", disabled=not legacy_options):
            st.session_state["__open_legacy__"] = legacy_sel
    else:
        # ensure no leftover state in prod
        st.session_state.pop("__open_legacy__", None)

    # Build stamp
    st.markdown("---")
    st.caption(
        "Build: FINAL+LEGACY | {} UTC".format(
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        )
    )

# --- Helpers for legacy runner ---
def _list_legacy_scripts():
    legacy_dir = Path("legacy")
    if not legacy_dir.exists():
        return []
    return [str(p.relative_to(legacy_dir)) for p in legacy_dir.rglob("*.py")]

def _run_legacy_script(rel_path: str):
    """Safe-ish inline exec for legacy pages in ./legacy"""
    try:
        target = Path("legacy") / rel_path
        code = target.read_text(encoding="utf-8")
        g = {"st": st, "__name__": "__main__"}
        l = {}
        exec(compile(code, str(target), "exec"), g, l)
    except Exception as e:
        st.error(f"Legacy script error: {e}")

# --- Module imports (your current panels/tools) ---
from modules import (
    breadth_panel,
    vectorvest_panel,
    etf_tactical_panel,
    guardrails_gauges,
    ibkr_charts,
    apac_dashboard,
    one_click_report,
)
from modules import (
    options_helper,
    trade_scorecard,
    backtest_mode,
    pattern_profiler,
    canada_filters,
)

# --- Main Router: Dashboards ---
if pick == "Breadth Panel":
    breadth_panel.render()
elif pick == "VectorVest Screeners":
    vectorvest_panel.render()
elif pick == "ETF Tactical":
    etf_tactical_panel.render()
elif pick == "Guardrails Gauges":
    guardrails_gauges.render()
elif pick == "IBKR Charts":
    ibkr_charts.render()
elif pick == "APAC Dashboard":
    apac_dashboard.render()
elif pick == "One-Click Daily Report":
    one_click_report.render()

# --- Tools ---
if tools_pick == "Options Helper":
    options_helper.render()
elif tools_pick == "AI Trade Quality Scorecard":
    trade_scorecard.render()
elif tools_pick == "Backtest Mode":
    backtest_mode.render()
elif tools_pick == "AI Pattern Profiler":
    pattern_profiler.render()

# --- Region ---
if region_pick == "Canada Filters":
    canada_filters.render()

# --- If dev_mode and a legacy script was chosen, run it at end ---
if DEV_MODE and st.session_state.get("__open_legacy__"):
    st.warning("Running legacy page (dev mode): " + st.session_state["__open_legacy__"])
    _run_legacy_script(st.session_state["__open_legacy__"])

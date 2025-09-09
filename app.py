from utils.prefs_bootstrap import prefs
import os, json
import streamlit as st
from datetime import datetime, timezone

st.set_page_config(page_title="Vega Cockpit — Final Build", layout="wide")

# Status bar
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

# Sidebar
with st.sidebar:
    st.title("Vega — Final Build")
    with st.expander("Dashboards", expanded=True):
        pick = st.radio("Open panel", [
            "Breadth Panel",
            "VectorVest Screeners",
            "ETF Tactical",
            "Guardrails Gauges",
            "IBKR Charts",
            "APAC Dashboard",
            "One-Click Daily Report"
        ], index=0)
    with st.expander("Trade Tools", expanded=False):
        tools_pick = st.radio("Tools", [
            "Options Helper",
            "AI Trade Quality Scorecard",
            "Backtest Mode",
            "AI Pattern Profiler"
        ], index=0)
    with st.expander("Region Filters", expanded=False):
        region_pick = st.radio("Region", [
            "Canada Filters"
        ], index=0)

from modules import breadth_panel, vectorvest_panel, etf_tactical_panel, guardrails_gauges, ibkr_charts, apac_dashboard, one_click_report
from modules import options_helper, trade_scorecard, backtest_mode, pattern_profiler, canada_filters

# Main router
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

# Tools
if tools_pick == "Options Helper":
    options_helper.render()
elif tools_pick == "AI Trade Quality Scorecard":
    trade_scorecard.render()
elif tools_pick == "Backtest Mode":
    backtest_mode.render()
elif tools_pick == "AI Pattern Profiler":
    pattern_profiler.render()

# Region
if region_pick == "Canada Filters":
    canada_filters.render()

st.sidebar.markdown("---")
st.sidebar.caption("Build: FINAL | {} UTC".format(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')))

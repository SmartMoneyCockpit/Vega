# src/pages/00_Home.py
import os, json, streamlit as st

st.set_page_config(page_title="Home — Vega Cockpit", layout="wide")
st.title("Home — Vega Cockpit")

# Last pipeline run (written by the workflow to reports/run_meta.json)
meta_path = "reports/run_meta.json"
if os.path.isfile(meta_path):
    try:
        meta = json.load(open(meta_path, "r", encoding="utf-8"))
        st.success(
            f"Last pipeline run: "
            f"[{meta.get('run_id','')}]({meta.get('run_url','')}) • "
            f"UTC: {meta.get('timestamp_utc','')}"
        )
    except Exception:
        st.info("Run metadata not available yet.")
else:
    st.info("Run metadata will appear here after the next All-in-One run.")

st.subheader("Dashboards")

# IMPORTANT: page paths are relative to the app root (src) and must live in the pages/ folder.
st.page_link("pages/01_NA_Text_Dashboard.py",  label="• North America — Text Dashboard")
st.page_link("pages/02_Europe_Text_Dashboard.py", label="• Europe — Text Dashboard")
st.page_link("pages/03_APAC_Text_Dashboard.py",  label="• APAC — Text Dashboard")
st.page_link("pages/04_Screener_Text.py",        label="• Screener — Text")

# Add more links if needed, always as pages/<file>.py
# st.page_link("pages/08_IBKR_Scanner.py", label="• IBKR Scanner")

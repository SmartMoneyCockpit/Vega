import json, os, streamlit as st

st.set_page_config(page_title="Home — Vega Cockpit", layout="wide")
st.title("Home — Vega Cockpit")

# Quick status from CI
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
    st.info("Run metadata will appear here after your next All-in-One run.")

# Navigation
st.subheader("Dashboards")
st.page_link("src/pages/01_NA_Text_Dashboard.py",  label="• North America — Text Dashboard")
st.page_link("src/pages/02_Europe_Text_Dashboard.py", label="• Europe — Text Dashboard")
st.page_link("src/pages/03_APAC_Text_Dashboard.py",  label="• APAC — Text Dashboard")
st.page_link("src/pages/04_Screener_Text.py",        label="• Screener — Text")

# Useful external links
repo = st.secrets.get("GITHUB_REPOSITORY", "") or os.getenv("GITHUB_REPOSITORY", "")
if repo:
    st.markdown(
        f"[Open All-in-One Workflow](https://github.com/{repo}/actions/workflows/all_in_one_reports.yml)"
    )

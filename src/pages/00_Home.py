# src/pages/00_Home.py
import os, json, streamlit as st

st.set_page_config(page_title="Home — Vega Cockpit", layout="wide")
st.title("Home — Vega Cockpit")

# --- Last pipeline run banner -------------------------------------------------
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

st.subheader("Dashboards")

# --- Safe link helper: try page_link first; if it fails, fall back to URL ----
def safe_page_link(relpath: str, label: str, url_fallback: str):
    try:
        # Works when the app's main script dir matches where 'pages/' lives
        st.page_link(relpath, label=label)
    except Exception:
        # Fallback to the known route slug (Streamlit builds these from filenames)
        st.markdown(f"[{label}]({url_fallback})")

# IMPORTANT: keep slugs in sync with your page filenames (Streamlit strips the numeric prefix)
safe_page_link("pages/01_NA_Text_Dashboard.py",  "• North America — Text Dashboard", "/North_America_Text_Dashboard")
safe_page_link("pages/02_Europe_Text_Dashboard.py", "• Europe — Text Dashboard",     "/Europe_Text_Dashboard")
safe_page_link("pages/03_APAC_Text_Dashboard.py",  "• APAC — Text Dashboard",       "/APAC_Text_Dashboard")
safe_page_link("pages/04_Screener_Text.py",        "• Screener — Text",             "/Screener_Text")

st.caption("If a link doesn’t open, use the sidebar on the left — same pages.")
st.page_link("pages/05_TradingView_Charts.py", label="• TradingView — Charts & Heatmap")

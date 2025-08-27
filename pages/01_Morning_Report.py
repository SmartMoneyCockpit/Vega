from utils.prefs_bootstrap import prefs
import streamlit as st
from datetime import datetime
from modules.morning_report import MorningReport
from modules.data_providers import DemoDataProvider

st.set_page_config(page_title="Vega Morning Report", layout="wide")

provider = DemoDataProvider()
session_date = st.sidebar.date_input("Session Date", datetime.now().date())
regions = st.sidebar.multiselect("Regions", ["USA","Canada","Mexico","LatAm"], default=["USA","Canada","Mexico","LatAm"])
sections = st.sidebar.multiselect(
    "Sections",
    ["Macro Header","Benchmark & Breadth Matrix","Options & Skews","Catalyst Board","Session Map","VectorVest Alt Color Guard","Final Risk Overlay"],
    default=["Macro Header","Benchmark & Breadth Matrix","Session Map","VectorVest Alt Color Guard","Final Risk Overlay"]
)

report = MorningReport(provider=provider, regions=regions, session_date=session_date)
if "Macro Header" in sections: report.render_macro_header()
if "Benchmark & Breadth Matrix" in sections: report.render_benchmark_and_breadth_matrix()
if "Options & Skews" in sections: report.render_options_and_skews()
if "Catalyst Board" in sections: report.render_catalyst_board()
if "Session Map" in sections: report.render_session_map()
if "VectorVest Alt Color Guard" in sections: report.render_color_guard_alt()
if "Final Risk Overlay" in sections: report.render_final_risk_overlay()

st.caption("© Vega — Morning Report Module")

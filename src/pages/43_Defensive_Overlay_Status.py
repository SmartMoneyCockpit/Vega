import os, sys, pathlib
import streamlit as st

_here = pathlib.Path(__file__).resolve()
sys.path.append(str(_here.parents[1]))

from modules.alerts.defensive_overlay import risk_off

st.set_page_config(page_title="Defensive Overlay", page_icon="🛡️", layout="centered")
st.title("🛡️ Defensive Overlay Status")

th = st.number_input("VIX threshold", value=20.0, step=0.5)
if st.button("Check"):
    status = risk_off(vix_threshold=th)
    st.success("Risk-OFF: Defensive overlays should trigger.") if status else st.info("Risk-ON/Neutral: No defensive overlay.")

import streamlit as st
st.set_page_config(page_title='Vega Cockpit', layout='wide')
st.title('Vega Cockpit')


# [VEGA: PANELS INJECTION]
import yaml
from modules.sector_heatmap import render as render_sector_heatmap, load_sector_data
from modules.alerts.sector_flip import render as render_sector_flips
from modules.emailing.aplus_digest import build_digest
try:
    with open("config/settings.yaml","r") as _f:
        SETTINGS = yaml.safe_load(_f) or {}
except Exception:
    SETTINGS = {}
st.markdown("## Stay Out / Get Back In")
s1, s2 = st.columns([3,2])
with s1:
    render_sector_heatmap(st, SETTINGS)
with s2:
    df = load_sector_data(mode=SETTINGS.get("tradingview",{}).get("mode","public"))
    render_sector_flips(st, df, SETTINGS)

import streamlit as st, json, os, subprocess, sys
from datetime import datetime

from app_auth import login_gate
if not login_gate(): pass

st.set_page_config(page_title='Sector Flip Alerts', layout='wide')
st.title('Sector Flip Alerts')

ALERTS_DIR = os.getenv('ALERTS_DIR','alerts')
path = os.path.join(ALERTS_DIR, 'sector_flips.json')

col1, col2 = st.columns([1,1])

with col1:
    if st.button('🔁 Scan Now (manual)'):
        # Run the scanner in-process
        try:
            import scripts.sector_flip_scan as scan
            scan.main()
            st.success('Scan complete.')
        except Exception as e:
            st.error(f'Error: {e}')

with col2:
    keep = st.selectbox('Show last results', ['Latest only'])

st.divider()

if os.path.exists(path):
    data = json.load(open(path))
    st.caption(f"Generated: {data.get('generated_at','')} | Threshold: {data.get('threshold')}")
    flips = data.get('flips', [])
    if flips:
        st.success(f"{len(flips)} sector flip(s) detected.")
        st.dataframe(flips, use_container_width=True)
    else:
        st.info('No flips detected at the moment.')
else:
    st.info('No alert file yet. Run a scan or wait for the cron job.')

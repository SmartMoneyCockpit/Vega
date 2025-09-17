import streamlit as st, pandas as pd
from pathlib import Path
from modules.utils.data_remote import load_csv_auto, raw_url, github_page_url
from modules.ui.focus_chart import render_focus
from modules.utils.tv_links import tv_symbol_url
def render_region(region:str):
    region=region.upper(); st.subheader(f"{region} Index Dashboard")
    rel=f'data/snapshots/{region.lower()}_indices.csv'
    c1,c2,c3=st.columns([4,2,2]);
    with c1: st.caption('Indices snapshot — Updated: unknown')
    if raw_url(rel):
        with c2: st.link_button('Open CSV (raw)', raw_url(rel), use_container_width=True)
    if github_page_url(rel):
        with c3: st.link_button('Open on GitHub', github_page_url(rel), use_container_width=True)
    df=load_csv_auto(rel)
    st.session_state.setdefault(f'focus_symbol_{region}','SPY' if region=='NA' else 'VGK' if region=='EU' else 'EWJ')
    render_focus(st.session_state[f'focus_symbol_{region}'])
    if df.empty: st.info('No snapshot data yet. The hourly pipeline will populate CSVs.'); return
    st.write('### Index Scorecard')
    for _,r in df.iterrows():
        sym=str(r.get('symbol',''))
        a=st.columns([2,1,1,1,2,2])
        a[0].markdown(f"[**{sym}** ↗]({tv_symbol_url(sym)})", unsafe_allow_html=True)
        a[1].write(r.get('price','—'))
        a[2].write(r.get('chg_1d','—'))
        a[3].write('▲' if (r.get('rs',0) or 0)>0 else '▼' if (r.get('rs',0) or 0)<0 else '•')
        a[4].write('—')
        a[5].write(r.get('decision','🟡 Wait'))

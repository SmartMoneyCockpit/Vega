import streamlit as st, pandas as pd
from app_auth import login_gate
if not login_gate(): pass
import db_adapter as db

st.set_page_config(page_title='Admin: Data Entry', layout='wide')
st.title('Admin — Data Entry (SQLite)')
st.caption('Data persists to VEGA_DB_PATH (or data/vega.db).')

tabs = st.tabs(['Positions','Signals','Breadth','Relative Strength'])
with tabs[0]:
    df=db.load_positions(); edited=st.data_editor(df, num_rows='dynamic', use_container_width=True)
    if st.button('Save Positions'): db.upsert_positions(edited.reindex(columns=['Ticker','Qty','Avg Cost','Last']).fillna(0)); st.success('Positions saved.')
with tabs[1]:
    df=db.load_signals(); edited=st.data_editor(df, num_rows='dynamic', use_container_width=True)
    if st.button('Save Signals'): db.upsert_signals(edited.reindex(columns=['Ticker','Setup','Reason','Country']).fillna('')); st.success('Signals saved.')
with tabs[2]:
    df=db.load_breadth(); edited=st.data_editor(df, num_rows='dynamic', use_container_width=True)
    if st.button('Save Breadth'): db.upsert_breadth(edited.reindex(columns=['Metric','Value','Status']).fillna('')); st.success('Breadth saved.')
with tabs[3]:
    df=db.load_rs(); edited=st.data_editor(df, num_rows='dynamic', use_container_width=True)
    if st.button('Save RS'): db.upsert_rs(edited.reindex(columns=['Bucket','RS Trend']).fillna('')); st.success('RS saved.')

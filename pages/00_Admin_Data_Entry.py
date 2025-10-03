import streamlit as st
import pandas as pd
from app_auth import login_gate
if not login_gate(): pass

st.set_page_config(page_title="Admin: Data Entry", layout="wide")
st.title("Admin — Data Entry (SQLite)")
st.caption("Edit tables below and click Save. Data persists to a local SQLite file (VEGA_DB_PATH or data/vega.db).")

import db_adapter as db

tabs = st.tabs(["Positions", "Signals", "Breadth", "Relative Strength"])

with tabs[0]:
    st.subheader("Positions (Ticker, Qty, Avg Cost, Last)")
    df = db.load_positions()
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Save Positions"):
        try:
            # Normalize column names
            need = ["Ticker","Qty","Avg Cost","Last"]
            edited = edited.reindex(columns=need)
            db.upsert_positions(edited.fillna(0))
            st.success("Positions saved.")
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[1]:
    st.subheader("Signals (Ticker, Setup, Reason, Country)")
    df = db.load_signals()
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Save Signals"):
        try:
            need = ["Ticker","Setup","Reason","Country"]
            edited = edited.reindex(columns=need)
            db.upsert_signals(edited.fillna(""))
            st.success("Signals saved.")
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[2]:
    st.subheader("Breadth (Metric, Value, Status)")
    df = db.load_breadth()
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Save Breadth"):
        try:
            need = ["Metric","Value","Status"]
            edited = edited.reindex(columns=need)
            db.upsert_breadth(edited.fillna(""))
            st.success("Breadth saved.")
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[3]:
    st.subheader("Relative Strength (Bucket, RS Trend)")
    df = db.load_rs()
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Save RS"):
        try:
            need = ["Bucket","RS Trend"]
            edited = edited.reindex(columns=need)
            db.upsert_rs(edited.fillna(""))
            st.success("RS saved.")
        except Exception as e:
            st.error(f"Error: {e}")

# macro_dashboard.py — Lightweight calendar with in-app editor & download
import os
import io
import pandas as pd
import streamlit as st
from datetime import datetime

DATA_DIR = "data"
CAL_FILE = os.path.join(DATA_DIR, "macro_calendar.csv")

TEMPLATE_ROWS = [
    ["2025-08-11","US","CPI (MoM/YoY)","High","US"],
    ["2025-08-12","US","Initial Jobless Claims","Med","US"],
    ["2025-08-13","CA","BoC Speech / Minutes","High","CA"],
    ["2025-08-14","MX","Banxico Decision","High","MX"],
    ["2025-08-15","US","Michigan Sentiment (Prelim)","Med","US"],
]

def ensure_template():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CAL_FILE):
        df = pd.DataFrame(TEMPLATE_ROWS, columns=["date","country","event","importance","session"])
        df.to_csv(CAL_FILE, index=False)

def load_calendar():
    ensure_template()
    try:
        df = pd.read_csv(CAL_FILE, dtype=str)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")
        return df
    except Exception:
        return pd.DataFrame(columns=["date","country","event","importance","session"])

def upcoming(df, days=14):
    if df.empty:
        return df
    today = pd.Timestamp.today().normalize()
    end = today + pd.Timedelta(days=days)
    return df[(df["date"] >= today) & (df["date"] <= end)]

def run():
    st.header("Macro Dashboard")
    st.caption("Upcoming events for US / Canada / Mexico. Uses a local CSV you can edit in-app.")
    df = load_calendar()
    st.subheader("Next 14 days")
    nxt = upcoming(df, 14).copy()
    if not nxt.empty:
        nxt["date"] = nxt["date"].dt.date
        st.dataframe(nxt, use_container_width=True)
    else:
        st.info("No upcoming events in the next 14 days.")
    st.divider()
    st.subheader("Edit Calendar")
    edit_df = df.copy()
    if not edit_df.empty and "date" in edit_df.columns:
        edit_df["date"] = edit_df["date"].dt.strftime("%Y-%m-%d")
    edited = st.data_editor(edit_df, num_rows="dynamic", use_container_width=True)
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Save calendar"):
            os.makedirs(DATA_DIR, exist_ok=True)
            pd.DataFrame(edited).to_csv(CAL_FILE, index=False)
            st.success("Saved")
    with colB:
        buff = io.StringIO()
        pd.DataFrame(edited).to_csv(buff, index=False)
        st.download_button("Download CSV", buff.getvalue(), file_name="macro_calendar.csv", mime="text/csv")

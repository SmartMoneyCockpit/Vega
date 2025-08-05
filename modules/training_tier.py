"""
Training Tier Module
-------------------

Maintain a list of educational materials, backtests and practice exercises.  Each
training item includes a title, description, status (Not Started / In
Progress / Completed) and optional notes.  Items are stored in `training.csv`
and synchronised to the `COCKPIT` Google Sheet (worksheet `Training`).
"""

from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

from utils import google_sheets


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
TRAINING_CSV = DATA_DIR / "training.csv"


def save_training(row: List) -> None:
    if TRAINING_CSV.exists():
        df = pd.read_csv(TRAINING_CSV)
        df.loc[len(df)] = row
    else:
        df = pd.DataFrame([row], columns=["Title", "Description", "Status", "Notes"])
    df.to_csv(TRAINING_CSV, index=False)
    try:
        google_sheets.append_row(row, sheet_name="COCKPIT", worksheet_name="Training")
    except Exception:
        pass


def render() -> None:
    st.subheader("📚 Training Tier")
    st.write("Track your educational materials, backtests and practice exercises.")
    with st.form("training_form"):
        title = st.text_input("Title", "Watch webinar on risk management")
        description = st.text_area("Description", "A detailed webinar on position sizing and stop placement.")
        status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
        notes = st.text_area("Notes", "")
        submitted = st.form_submit_button("Save Training Item")
        if submitted:
            row = [title, description, status, notes]
            save_training(row)
            st.success(f"Training item '{title}' saved.")
    if TRAINING_CSV.exists():
        st.markdown("### Your Training Items")
        df = pd.read_csv(TRAINING_CSV)
        st.dataframe(df)

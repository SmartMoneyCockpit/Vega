"""
Journal Logger Module
--------------------

Stores and displays entries that consolidate trades, health logs, briefings and
other notes.  Each journal entry is a dictionary with at least the keys
`Date`, `Type` and `Content`.  The module writes entries to a local CSV
(`journal.csv`) and attempts to synchronise them with the `COCKPIT` Google Sheet
(worksheet `Journal`).
"""

import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

from utils import google_sheets


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
JOURNAL_CSV = DATA_DIR / "journal.csv"


def save_journal_entry(entry: Dict[str, str]) -> None:
    """Append a journal entry to the local CSV and Google Sheet."""
    df = pd.DataFrame([entry])
    if JOURNAL_CSV.exists():
        existing = pd.read_csv(JOURNAL_CSV)
        combined = pd.concat([existing, df], ignore_index=True)
        combined.to_csv(JOURNAL_CSV, index=False)
    else:
        df.to_csv(JOURNAL_CSV, index=False)
    try:
        google_sheets.append_row([entry.get("Date"), entry.get("Type"), entry.get("Content")], sheet_name="COCKPIT", worksheet_name="Journal")
    except Exception:
        pass


def render() -> None:
    st.subheader("📔 Journal Logger")
    st.write("View and add journal entries.  Entries from other modules (trades, health, briefings) are stored here as well.")
    # Form to manually add a journal entry
    with st.form("journal_form"):
        date = st.date_input("Date", datetime.date.today())
        entry_type = st.text_input("Entry type", "Note")
        content = st.text_area("Content")
        submitted = st.form_submit_button("Save Journal Entry")
        if submitted:
            entry = {
                "Date": date.strftime("%Y-%m-%d"),
                "Type": entry_type,
                "Content": content
            }
            save_journal_entry(entry)
            st.success("Journal entry saved.")
    # Display recent entries
    if JOURNAL_CSV.exists():
        df = pd.read_csv(JOURNAL_CSV)
        df = df.sort_values(by="Date", ascending=False)
        st.markdown("### Recent Journal Entries")
        st.dataframe(df.head(20))
    else:
        st.info("No journal entries yet.")

# 🧠
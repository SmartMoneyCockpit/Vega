"""
Health Tracker Module
--------------------

This module allows users to log daily wellness metrics such as sleep duration,
exercise minutes, resting heart rate and mood.  It provides simple vagal tone
suggestions based on workout intensity.  Records are saved locally and
synchronised to the `COCKPIT` Google Sheet (worksheet `Health`) when
available.
"""

import datetime
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

from utils import google_sheets


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
HEALTH_CSV = DATA_DIR / "health.csv"


def save_health(row: List) -> None:
    if HEALTH_CSV.exists():
        df = pd.read_csv(HEALTH_CSV)
        df.loc[len(df)] = row
    else:
        df = pd.DataFrame([row], columns=["Date", "SleepHours", "WorkoutMinutes", "RestingHR", "Mood", "Notes"])
    df.to_csv(HEALTH_CSV, index=False)
    try:
        google_sheets.append_row(row, sheet_name="COCKPIT", worksheet_name="Health")
    except Exception:
        pass


def suggest_vagal_exercises(workout_minutes: int) -> str:
    """Return a simple vagal tone suggestion based on workout duration."""
    if workout_minutes == 0:
        return "Consider a light walk or stretching to stimulate the vagus nerve."
    elif workout_minutes < 30:
        return "Great job! Add 5 minutes of deep breathing to enhance recovery."
    elif workout_minutes < 60:
        return "Excellent session! Follow up with cold exposure or humming exercises."
    else:
        return "Intense workout! Practice extended exhalations and meditation for vagal balance."


def render() -> None:
    st.subheader("💓 Health Tracker")
    st.write("Log your daily health metrics and get vagal tone suggestions after workouts.")
    with st.form("health_form"):
        date = st.date_input("Date", datetime.date.today())
        sleep_hours = st.number_input("Sleep duration (hours)", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
        workout_minutes = st.number_input("Workout duration (minutes)", min_value=0, max_value=300, value=0, step=5)
        resting_hr = st.number_input("Resting heart rate (bpm)", min_value=30, max_value=200, value=60, step=1)
        mood = st.slider("Mood (1=low, 5=high)", min_value=1, max_value=5, value=3)
        notes = st.text_area("Notes", "")
        submitted = st.form_submit_button("Save Health Entry")
        if submitted:
            row = [date.strftime("%Y-%m-%d"), float(sleep_hours), int(workout_minutes), int(resting_hr), int(mood), notes]
            save_health(row)
            suggestion = suggest_vagal_exercises(int(workout_minutes))
            st.success("Health entry saved.")
            st.info(f"Vagal suggestion: {suggestion}")
    if HEALTH_CSV.exists():
        st.markdown("### Recent Health Entries")
        df = pd.read_csv(HEALTH_CSV)
        st.dataframe(df.tail(10))

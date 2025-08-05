"""
Strategy Builder Module
----------------------

Define and store custom trading strategies.  Each strategy includes a name,
timeframe, description, list of indicators, risk management rules and entry/exit
criteria.  Saved strategies are written to a local CSV and synchronised to
Google Sheets (worksheet `Strategies`).
"""

from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

from utils import google_sheets


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
STRATEGIES_CSV = DATA_DIR / "strategies.csv"


def save_strategy(row: List) -> None:
    if STRATEGIES_CSV.exists():
        df = pd.read_csv(STRATEGIES_CSV)
        df.loc[len(df)] = row
    else:
        df = pd.DataFrame([row], columns=["Name", "Timeframe", "Indicators", "RiskRules", "EntryCriteria", "ExitCriteria", "Notes"])
    df.to_csv(STRATEGIES_CSV, index=False)
    try:
        google_sheets.append_row(row, sheet_name="COCKPIT", worksheet_name="Strategies")
    except Exception:
        pass


def render() -> None:
    st.subheader("🧠 Strategy Builder")
    st.write("Create and manage your trading strategies.")
    with st.form("strategy_form"):
        name = st.text_input("Strategy name", "My Strategy")
        timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d", "1w"])
        indicators = st.text_area("Indicators (comma separated)", "EMA20, EMA50, RSI")
        risk_rules = st.text_area("Risk management rules", "Risk 1% per trade, stop loss at ATR")
        entry_criteria = st.text_area("Entry criteria", "Price crosses above EMA20 and RSI < 30")
        exit_criteria = st.text_area("Exit criteria", "Take profit at 2:1 risk/reward ratio or trailing stop")
        notes = st.text_area("Additional notes", "")
        submitted = st.form_submit_button("Save Strategy")
        if submitted:
            row = [name, timeframe, indicators, risk_rules, entry_criteria, exit_criteria, notes]
            save_strategy(row)
            st.success(f"Strategy '{name}' saved.")
    if STRATEGIES_CSV.exists():
        st.markdown("### Saved Strategies")
        df = pd.read_csv(STRATEGIES_CSV)
        st.dataframe(df)

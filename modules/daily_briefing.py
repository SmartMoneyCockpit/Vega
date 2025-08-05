"""
Daily Morning Briefing Module
----------------------------

Generates a simple morning briefing summarising overnight moves in major equity
indices and highlighting upcoming macro events.  The module uses `yfinance`
to pull the latest close prices for key benchmarks.  Macro events are
placeholder items that can be replaced by actual calendar data.
"""

import datetime
from typing import Dict, List

import pandas as pd
import streamlit as st
import yfinance as yf


KEY_INDICES = {
    "S&P 500": "^GSPC",
    "NASDAQ 100": "^NDX",
    "Dow Jones": "^DJI",
    "Nikkei 225": "^N225",
    "DAX": "^GDAXI",
    "FTSE 100": "^FTSE"
}


def fetch_index_changes() -> pd.DataFrame:
    """Fetch the previous close and current price for key indices."""
    rows = []
    for name, ticker in KEY_INDICES.items():
        try:
            data = yf.download(ticker, period="5d", interval="1d")
            if data.empty:
                continue
            close_yesterday = data["Close"].iloc[-2]
            close_last = data["Close"].iloc[-1]
            change = close_last - close_yesterday
            pct_change = (change / close_yesterday) * 100
            rows.append({
                "Index": name,
                "Prev Close": round(close_yesterday, 2),
                "Last": round(close_last, 2),
                "Change": round(change, 2),
                "%Change": round(pct_change, 2)
            })
        except Exception:
            rows.append({
                "Index": name,
                "Prev Close": None,
                "Last": None,
                "Change": None,
                "%Change": None
            })
    return pd.DataFrame(rows)


def get_macro_events(date: datetime.date) -> List[str]:
    """Return a list of macro events for the given date.

    This is a placeholder implementation.  Users can replace this function with
    one that queries an actual economic calendar API.
    """
    # Example placeholder events
    weekday = date.weekday()
    if weekday == 0:
        return ["US Durable Goods Orders", "Japan Industrial Production"]
    elif weekday == 1:
        return ["Eurozone CPI", "China PMI"]
    elif weekday == 2:
        return ["FOMC Minutes", "US Crude Oil Inventories"]
    elif weekday == 3:
        return ["ECB Rate Decision", "Australia Unemployment Rate"]
    elif weekday == 4:
        return ["US Non‑Farm Payrolls", "Canada Employment Change"]
    else:
        return []


def render() -> None:
    st.subheader("🌅 Daily Morning Briefing")
    today = datetime.date.today()
    st.write(f"Date: {today.strftime('%Y-%m-%d')}")
    st.markdown("#### Overnight Market Moves")
    changes_df = fetch_index_changes()
    st.table(changes_df)
    st.markdown("#### Today's Macro Events")
    events = get_macro_events(today)
    if events:
        for event in events:
            st.markdown(f"- {event}")
    else:
        st.write("No scheduled major events today.")
    st.markdown("#### Briefing Notes")
    notes = st.text_area("Add your own notes to the briefing", "")
    if st.button("Save Briefing to Journal"):
        from journal_logger import save_journal_entry
        from .journal_logger import save_journal_entry
        entry = {
            "Date": today.strftime("%Y-%m-%d"),
            "Type": "Morning Briefing",
            "Content": f"Index Moves:\n{changes_df.to_string(index=False)}\n\nEvents:\n" + "\n".join(events) + ("\n\nNotes:\n" + notes if notes else "")
        }
        save_journal_entry(entry)
        st.success("Briefing saved to journal.")
        st.success("Briefing saved to journal.")

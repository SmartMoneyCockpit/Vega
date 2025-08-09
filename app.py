
import os
import time
import streamlit as st

from sheets_client import get_sheet, append_row, read_range

st.set_page_config(page_title="Vega Cockpit — MVP", layout="wide")

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
SHEET_MAIN_TAB = os.getenv("GOOGLE_SHEET_MAIN_TAB", "COCKPIT")

st.title("Vega Cockpit — Day‑1 MVP")

with st.sidebar:
    st.toggle("Auto-refresh (every 60s)", value=False, key="auto_refresh")
    st.caption("Env check")
    if SHEET_ID:
        st.code(f"SHEET_ID={SHEET_ID[:6]}…{SHEET_ID[-4:]}")
    else:
        st.error("Missing GOOGLE_SHEET_ID")

if not SHEET_ID:
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["Morning Report", "Watchlist", "Journal/Health Log", "Logs"])

with tab1:
    st.subheader("Morning Report (MVP)")
    st.markdown(
        "- Session: North America\n"
        "- Macro calendar: **from sheet (next pass)**\n"
        "- ETFs/Stocks: **from sheet (next pass)**"
    )

with tab2:
    st.subheader("Watchlist (Sheet-driven)")
    st.caption("Reads A2:D50 from the main tab: Ticker | Strategy | Entry | Stop")
    try:
        values = read_range(SHEET_ID, f"{SHEET_MAIN_TAB}!A2:D50") or []
        if not values:
            st.info("No rows found in A2:D50. Add some tickers to your sheet.")
        else:
            for row in values:
                cols = st.columns(4)
                tkr = row[0] if len(row) > 0 else "—"
                strat = row[1] if len(row) > 1 else "—"
                entry = row[2] if len(row) > 2 else "—"
                stop = row[3] if len(row) > 3 else "—"
                cols[0].metric("Ticker", tkr)
                cols[1].write("**Strategy**"); cols[1].write(strat)
                cols[2].write("**Entry**"); cols[2].write(entry)
                cols[3].write("**Stop**"); cols[3].write(stop)
                st.divider()
    except Exception as e:
        st.error(f"Watchlist load error: {e}")

with tab3:
    st.subheader("Quick Log → Google Sheet")
    with st.form("quicklog"):
        col1, col2 = st.columns(2)
        with col1:
            kind = st.selectbox("Type", ["Journal", "Health", "Note"], index=0)
            symbol = st.text_input("Symbol (optional)")
        with col2:
            status = st.selectbox("Status", ["Open", "Closed", "Info"], index=0)
        notes = st.text_area("Notes", placeholder="What changed, why it matters, next action…")
        submitted = st.form_submit_button("Append Row")
        if submitted:
            try:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                append_row(SHEET_ID, SHEET_MAIN_TAB, [ts, kind, symbol, status, notes])
                st.success("Row appended to Google Sheet.")
            except Exception as e:
                st.error(f"Append failed: {e}")

with tab4:
    st.subheader("Recent Log Rows (last 10)")
    try:
        values = read_range(SHEET_ID, f"{SHEET_MAIN_TAB}!A1:E200") or []
        header = values[0] if values else []
        body = values[1:][-10:] if len(values) > 1 else []
        if header and body:
            import pandas as pd
            df = pd.DataFrame(body, columns=header)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No log rows yet.")
    except Exception as e:
        st.error(f"Log view error: {e}")

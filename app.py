
import os
import time
import math
import requests
import streamlit as st

from sheets_client import append_row, read_range

st.set_page_config(page_title="Vega Cockpit — MVP", layout="wide")

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
WATCHLIST_TAB = os.getenv("GOOGLE_SHEET_WATCHLIST_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "Watch List"))
LOG_TAB = os.getenv("GOOGLE_SHEET_LOG_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "TradeLog"))
POLYGON_KEY = os.getenv("POLYGON_KEY", "")
RR_TARGET = float(os.getenv("RR_TARGET", "2.0"))  # desired risk:reward target

def get_price(symbol: str):
    if "." in symbol or not POLYGON_KEY:
        return None
    try:
        url = f"https://api.polygon.io/v2/last/trade/{symbol.upper()}?apiKey={POLYGON_KEY}"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        if isinstance(data, dict):
            if "results" in data and isinstance(data["results"], dict):
                p = data["results"].get("p")
                return float(p) if p is not None else None
            if "price" in data:
                return float(data["price"])
        return None
    except Exception:
        return None

def compute_rr(entry, stop, target):
    try:
        e = float(entry); s = float(stop); t = float(target)
        risk = abs(e - s)
        reward = abs(t - e)
        return round(reward / risk, 2) if risk > 0 else None
    except Exception:
        return None

def signal_from_price(price, entry, stop):
    # returns ('text', 'color')
    try:
        e = float(entry) if entry not in (None, "", "—") else None
        s = float(stop) if stop not in (None, "", "—") else None
        p = float(price) if price not in (None, "", "—") else None
    except Exception:
        return ("—", "gray")

    if p is None or (e is None and s is None):
        return ("—", "gray")

    if e is not None and p >= e and (s is None or p > s):
        return ("Entry hit", "green")

    if s is not None and p <= s:
        return ("At/under stop", "red")

    if e is not None:
        # distance to entry
        dist = ((e - p) / e) * 100.0
        if dist > 0:
            return (f"{dist:.1f}% to entry", "orange")
    return ("Watching", "blue")

with st.sidebar:
    st.toggle("Auto-refresh (every 60s)", value=False, key="auto_refresh")
    st.caption("Env check")
    if SHEET_ID:
        st.code(f"SHEET_ID={SHEET_ID[:6]}…{SHEET_ID[-4:]}")
        st.code(f"WATCHLIST_TAB={WATCHLIST_TAB}")
        st.code(f"LOG_TAB={LOG_TAB}")
        st.code(f"POLYGON_KEY={'set' if POLYGON_KEY else 'missing'}")
        st.code(f"RR_TARGET={RR_TARGET}")
    else:
        st.error("Missing GOOGLE_SHEET_ID")

st.title("Vega Cockpit — Day-1 MVP")

if not SHEET_ID:
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["Morning Report", "Watchlist (Signals)", "Journal/Health Log", "Logs"]) 

with tab1:
    st.subheader("Morning Report (MVP)")
    st.markdown("- Session: North America\n- Macro & tickers: sheet-driven (next pass)")

with tab2:
    st.subheader("Watchlist — signals, live price, R/R")
    st.caption(f"Reads {WATCHLIST_TAB}!A2:D50 → Ticker | Strategy | Entry | Stop")
    try:
        rows = read_range(SHEET_ID, f"{WATCHLIST_TAB}!A2:D50") or []
        if not rows:
            st.info("No rows found. Add tickers to your Watch List sheet.")
        else:
            for idx, row in enumerate(rows):
                tkr = row[0].strip().upper() if len(row) > 0 and row[0] else "—"
                strat = row[1] if len(row) > 1 else "—"
                entry = row[2] if len(row) > 2 else "—"
                stop = row[3] if len(row) > 3 else "—"
                if tkr == "—" or not tkr:
                    continue
                price = get_price(tkr)
                # heuristic target = entry + RR_TARGET * (entry - stop)
                target = None
                rr = None
                try:
                    if entry not in (None, "", "—") and stop not in (None, "", "—"):
                        e = float(entry); s = float(stop)
                        target = e + RR_TARGET * (e - s)
                        rr = compute_rr(e, s, target)
                except Exception:
                    pass
                # signal
                sig_text, sig_color = signal_from_price(price, entry, stop)

                cols = st.columns([1.1, 2.0, 1, 1, 1, 1.2])
                cols[0].metric("Ticker", tkr)
                cols[1].write(f"**Strategy**\n{str(strat)}")
                cols[2].metric("Entry", entry if entry else "—")
                cols[3].metric("Stop", stop if stop else "—")
                cols[4].metric("Price", f"{price:.2f}" if price is not None else "—")
                # signal pill
                with cols[5]:
                    st.write("**Signal**")
                    st.markdown(f"<div style='display:inline-block;padding:6px 10px;border-radius:999px;background:{sig_color};color:white'>{sig_text}</div>", unsafe_allow_html=True)
                # quick log form per row
                with st.expander(f"Quick note for {tkr}"):
                    with st.form(f"logform_{idx}"):
                        note = st.text_input("Note", key=f"note_{idx}")
                        submit = st.form_submit_button("Append to TradeLog")
                        if submit:
                            ts = time.strftime("%Y-%m-%d %H:%M:%S")
                            try:
                                append_row(SHEET_ID, LOG_TAB, [ts, "Note", tkr, "Info", note])
                                st.success("Logged.")
                            except Exception as e:
                                st.error(f"Append failed: {e}")
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
        submitted = st.form_submit_button(f"Append Row to '{LOG_TAB}'")
        if submitted:
            try:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                append_row(SHEET_ID, LOG_TAB, [ts, kind, symbol, status, notes])
                st.success(f"Row appended to {LOG_TAB}.")
            except Exception as e:
                st.error(f"Append failed: {e}")

with tab4:
    st.subheader(f"Recent Log Rows from '{LOG_TAB}' (last 10)")
    try:
        values = read_range(SHEET_ID, f"{LOG_TAB}!A1:E200") or []
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


import os
import time
import requests
import streamlit as st

from sheets_client import append_row, read_range

st.set_page_config(page_title="Vega Cockpit — MVP", layout="wide")

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
WATCHLIST_TAB = os.getenv("GOOGLE_SHEET_WATCHLIST_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "Watch List"))
LOG_TAB = os.getenv("GOOGLE_SHEET_LOG_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "TradeLog"))
POLYGON_KEY = os.getenv("POLYGON_KEY", "")

def get_price(symbol: str):
    # US equities only. If not, return None.
    if "." in symbol:  # crude non-US/ETF suffix filter
        return None
    if not POLYGON_KEY:
        return None
    try:
        # Polygon last trade endpoint (aggregated real-time / snapshot alt)
        url = f"https://api.polygon.io/v2/last/trade/{symbol.upper()}?apiKey={POLYGON_KEY}"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        # fallbacks against different shapes
        if isinstance(data, dict):
            if "results" in data and isinstance(data["results"], dict):
                return float(data["results"].get("p")) if data["results"].get("p") is not None else None
            if "price" in data:
                return float(data["price"])
        return None
    except Exception:
        return None

with st.sidebar:
    st.toggle("Auto-refresh (every 60s)", value=False, key="auto_refresh")
    st.caption("Env check")
    if SHEET_ID:
        st.code(f"SHEET_ID={SHEET_ID[:6]}…{SHEET_ID[-4:]}")
        st.code(f"WATCHLIST_TAB={WATCHLIST_TAB}")
        st.code(f"LOG_TAB={LOG_TAB}")
        st.code(f"POLYGON_KEY={'set' if POLYGON_KEY else 'missing'}")
    else:
        st.error("Missing GOOGLE_SHEET_ID")

st.title("Vega Cockpit — Day-1 MVP")

if not SHEET_ID:
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["Morning Report", "Watchlist (Live)", "Journal/Health Log", "Logs"])

with tab1:
    st.subheader("Morning Report (MVP)")
    st.markdown("- Session: North America\n- Macro & tickers: sheet-driven (next pass)")

with tab2:
    st.subheader("Watchlist — with live price (Polygon)")
    st.caption(f"Reads {WATCHLIST_TAB}!A2:D50 → Ticker | Strategy | Entry | Stop")
    try:
        rows = read_range(SHEET_ID, f"{WATCHLIST_TAB}!A2:D50") or []
        if not rows:
            st.info("No rows found. Add tickers to your Watch List sheet.")
        else:
            for row in rows:
                tkr = row[0].strip().upper() if len(row) > 0 and row[0] else "—"
                strat = row[1] if len(row) > 1 else "—"
                entry = row[2] if len(row) > 2 else "—"
                stop = row[3] if len(row) > 3 else "—"
                if tkr == "—" or not tkr:
                    continue
                price = get_price(tkr)
                cols = st.columns([1.2, 2, 1, 1, 1])
                cols[0].metric("Ticker", tkr, None)
                cols[1].write(f"**Strategy**\n{strat}")
                cols[2].metric("Entry", entry if entry else "—")
                cols[3].metric("Stop", stop if stop else "—")
                cols[4].metric("Price", f"{price:.2f}" if price else "—")
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

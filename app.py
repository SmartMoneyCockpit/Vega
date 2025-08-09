
import os
import time
from datetime import datetime
import requests
import streamlit as st
import pandas as pd

from sheets_client import append_row, read_range, get_sheet

st.set_page_config(page_title="Vega Cockpit — MVP", layout="wide")

# ----- Config from env
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
WATCHLIST_TAB = os.getenv("GOOGLE_SHEET_WATCHLIST_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "Watch List"))
LOG_TAB = os.getenv("GOOGLE_SHEET_LOG_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "TradeLog"))
POLYGON_KEY = os.getenv("POLYGON_KEY", "")
RR_TARGET = float(os.getenv("RR_TARGET", "2.0"))
ALERT_PCT = float(os.getenv("ALERT_PCT", "1.5"))   # % distance to entry considered 'near'
REFRESH_SECS = int(os.getenv("REFRESH_SECS", "60"))

# ----- Helpers
@st.cache_data(show_spinner=False, ttl=15)
def quote(symbol: str, api_key: str):
    if "." in symbol or not api_key:
        return None
    try:
        url = f"https://api.polygon.io/v2/last/trade/{symbol.upper()}?apiKey={api_key}"
        r = requests.get(url, timeout=6)
        if r.status_code != 200:
            return None
        data = r.json()
        if isinstance(data, dict) and isinstance(data.get("results"), dict):
            p = data["results"].get("p")
            return float(p) if p is not None else None
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

def target_from_rr(entry, stop, rr=2.0):
    try:
        e = float(entry); s = float(stop)
        return round(e + rr * (e - s), 2)
    except Exception:
        return None

def distance_pct(a, b):
    try:
        a = float(a); b = float(b)
        return round(100 * (a - b) / a, 2)
    except Exception:
        return None

# ----- Sidebar
with st.sidebar:
    auto = st.toggle(f"Auto-refresh (every {REFRESH_SECS}s)", value=False, key="auto_refresh")
    st.caption("Env check")
    if SHEET_ID:
        st.code(f"SHEET_ID={SHEET_ID[:6]}…{SHEET_ID[-4:]}")
        st.code(f"WATCHLIST_TAB={WATCHLIST_TAB}")
        st.code(f"LOG_TAB={LOG_TAB}")
        st.code(f"POLYGON_KEY={'set' if POLYGON_KEY else 'missing'}")
        st.code(f"RR_TARGET={RR_TARGET} ALERT_PCT={ALERT_PCT}%")
    else:
        st.error("Missing GOOGLE_SHEET_ID")

if auto:
    st.experimental_rerun()

st.title("Vega Cockpit — Day-1 MVP")

if not SHEET_ID:
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Health", "Watchlist (Live)", "Journal/Health Log", "Logs", "Settings"])

# ----- Health
with tab1:
    st.subheader("Health checks")
    ok = True
    try:
        ws = get_sheet(SHEET_ID, WATCHLIST_TAB)
        st.success(f"✅ Connected to Watchlist tab: {WATCHLIST_TAB}")
    except Exception as e:
        ok = False
        st.error(f"❌ Watchlist access failed: {e}")
    try:
        ws2 = get_sheet(SHEET_ID, LOG_TAB)
        st.success(f"✅ Connected to Log tab: {LOG_TAB}")
    except Exception as e:
        ok = False
        st.error(f"❌ Log access failed: {e}")
    st.write("—")
    st.write(f"Polygon key: {'✅ set' if POLYGON_KEY else '⚠️ missing'}")
    st.caption(datetime.utcnow().strftime("Checked at %Y-%m-%d %H:%M UTC"))
    if not ok:
        st.stop()

# ----- Watchlist
def badge(text, color):
    st.markdown(f"<span style='background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:12px'>{text}</span>", unsafe_allow_html=True)

with tab2:
    st.subheader("Watchlist — live with alerts")
    st.caption(f"Reads {WATCHLIST_TAB}!A2:D50 → Ticker | Strategy | Entry | Stop")
    rows = read_range(SHEET_ID, f"{WATCHLIST_TAB}!A2:D50") or []
    if not rows:
        st.info("No rows found. Add tickers to your Watch List sheet.")
    else:
        for row in rows:
            tkr = (row[0] if len(row) > 0 else "").strip().upper()
            if not tkr:
                continue
            strat = row[1] if len(row) > 1 else ""
            entry = row[2] if len(row) > 2 else ""
            stopv = row[3] if len(row) > 3 else ""

            price = quote(tkr, POLYGON_KEY)
            target = target_from_rr(entry, stopv, RR_TARGET) if entry and stopv else None
            rr = compute_rr(entry, stopv, target) if target else None

            cols = st.columns([1.2, 2.5, 1, 1, 1.2, 1.6])
            cols[0].metric("Ticker", tkr)
            cols[1].write(f"**Strategy**\n{strat or '—'}")
            cols[2].metric("Entry", entry or "—")
            cols[3].metric("Stop", stopv or "—")
            cols[4].metric("Price", f"{price:.2f}" if price is not None else "—")
            cols[5].metric("R/R→Target", rr if rr is not None else "—")

            # signals
            if price is not None:
                s = None
                try:
                    e = float(entry) if entry else None
                    sstop = float(stopv) if stopv else None
                except Exception:
                    e = sstop = None
                alert_shown = False
                if e is not None:
                    dist = distance_pct(e, price)  # % above/below entry
                    if dist is not None and abs(dist) <= ALERT_PCT:
                        badge(f"{abs(dist)}% to entry", "#EAB308")  # amber
                        alert_shown = True
                    if price >= e:
                        badge("Entry hit", "#22C55E"); alert_shown = True
                if sstop is not None and price <= sstop:
                    badge("At/under stop", "#EF4444"); alert_shown = True
                if not alert_shown:
                    badge("Watching", "#3B82F6")

            # quick log
            with st.expander("Quick log"):
                kind = st.selectbox("Type", ["Journal", "Health", "Note"], key=f"k_{tkr}")
                status = st.selectbox("Status", ["Open", "Closed", "Info"], key=f"s_{tkr}")
                note = st.text_input("Notes", value=f"{tkr}: {strat}")
                if st.button(f"Append to {LOG_TAB}", key=f"btn_{tkr}"):
                    ts = time.strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        append_row(SHEET_ID, LOG_TAB, [ts, kind, tkr, status, note])
                        st.success("Logged.")
                    except Exception as e:
                        st.error(f"Append failed: {e}")
            st.divider()

# ----- Journal/Health form
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

# ----- Logs (worksheet path only to avoid 404)
with tab4:
    st.subheader(f"Recent Log Rows from '{LOG_TAB}' (last 10)")
    try:
        ws = get_sheet(SHEET_ID, LOG_TAB)
        values = ws.get("A1:E200") or []
        header = values[0] if values else []
        body = values[1:][-10:] if len(values) > 1 else []
        if header and body:
            df = pd.DataFrame(body, columns=header)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No log rows yet.")
    except Exception as e:
        st.error(f"Log view error: {e}")

# ----- Settings reference
with tab5:
    st.subheader("Runtime settings")
    st.write({
        "GOOGLE_SHEET_ID": SHEET_ID[:6] + "…" + SHEET_ID[-4:] if SHEET_ID else "",
        "WATCHLIST_TAB": WATCHLIST_TAB,
        "LOG_TAB": LOG_TAB,
        "RR_TARGET": RR_TARGET,
        "ALERT_PCT": ALERT_PCT,
        "REFRESH_SECS": REFRESH_SECS,
        "POLYGON_KEY_SET": bool(POLYGON_KEY),
    })

# app.py — Vega Cockpit MVP (enhanced batch)
import os
import time
from datetime import datetime
from datetime import datetime as dt
import requests
import streamlit as st
import pandas as pd

# Sheets client (private access via service account, already wired)
from sheets_client import append_row, read_range, get_sheet

# ---------- App config ----------
st.set_page_config(page_title="Vega Cockpit — MVP", layout="wide")

# ---------- Env / runtime settings ----------
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
WATCHLIST_TAB = os.getenv("GOOGLE_SHEET_WATCHLIST_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "Watch List"))
LOG_TAB = os.getenv("GOOGLE_SHEET_LOG_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "TradeLog"))
POLYGON_KEY = os.getenv("POLYGON_KEY", "")

# Session-scoped tunables (UI adjustable; not persisted to env)
if "RR_TARGET" not in st.session_state:
    st.session_state.RR_TARGET = float(os.getenv("RR_TARGET", "2.0"))
if "ALERT_PCT" not in st.session_state:
    st.session_state.ALERT_PCT = float(os.getenv("ALERT_PCT", "1.5"))
if "REFRESH_SECS" not in st.session_state:
    st.session_state.REFRESH_SECS = int(os.getenv("REFRESH_SECS", "60"))

RR_TARGET = st.session_state.RR_TARGET
ALERT_PCT = st.session_state.ALERT_PCT
REFRESH_SECS = st.session_state.REFRESH_SECS

# ---------- Helpers ----------
def provider_quote_polygon(symbol: str, api_key: str):
    """Polygon last trade. Return None on any issue (safe)."""
    if "." in symbol or not api_key:
        return None
    try:
        url = f"https://api.polygon.io/v2/last/trade/{symbol.upper()}?apiKey={api_key}"
        r = requests.get(url, timeout=6)
        if r.status_code != 200:
            return None
        data = r.json()
        p = (data or {}).get("results", {}).get("p")
        return float(p) if p is not None else None
    except Exception:
        return None

def quote(symbol: str):
    """Pluggable price source — today: Polygon."""
    return provider_quote_polygon(symbol, POLYGON_KEY)

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

def badge(text, color):
    st.markdown(
        f"<span style='background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:12px'>{text}</span>",
        unsafe_allow_html=True
    )

LOG_HEADERS = ["Timestamp", "Type", "Symbol", "Status", "Notes"]

def ensure_log_headers(ws):
    """Ensure A1:E1 matches LOG_HEADERS. Offer one-click repair if not."""
    try:
        first = ws.get("A1:E1") or []
        current = first[0] if first else []
        if [c.strip() for c in current] != LOG_HEADERS:
            st.warning("TradeLog headers differ from expected. Click to repair.")
            if st.button("Repair TradeLog headers (A1:E1)"):
                try:
                    # Overwrite header row safely
                    ws.update("A1", [LOG_HEADERS])
                    st.success("Headers repaired.")
                except Exception as e:
                    st.error(f"Header repair failed: {e}")
            return False
        return True
    except Exception as e:
        st.error(f"Header check failed: {e}")
        return False

def get_log_df_last(ws, limit=10):
    """Fetch A1:E, normalize rows to header length, return last N as DataFrame."""
    values = ws.get("A1:E1000") or []
    if not values:
        return pd.DataFrame(columns=LOG_HEADERS)
    header = values[0]
    body = values[1:]
    norm = []
    for r in body:
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        elif len(r) > len(header):
            r = r[:len(header)]
        norm.append(r)
    if not norm:
        return pd.DataFrame(columns=header)
    df = pd.DataFrame(norm, columns=header)
    return df.tail(limit)

def parse_ts(s: str):
    # Accept "YYYY-MM-DD HH:MM:SS" optionally with " UTC"
    try:
        s = s.replace(" UTC", "")
        return dt.strptime(s, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def append_log_row_safe(symbol="", kind="Journal", status="Open", notes=""):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        append_row(SHEET_ID, LOG_TAB, [ts, kind, symbol, status, notes])
        return True, None
    except Exception as e:
        return False, str(e)

# ---------- Sidebar ----------
with st.sidebar:
    auto = st.toggle(f"Auto-refresh (every {REFRESH_SECS}s)", value=False, key="auto_refresh")
    st.caption("Env check")
    if SHEET_ID:
        st.code(f"SHEET_ID={SHEET_ID[:6]}…{SHEET_ID[-4:]}")
        st.code(f"WATCHLIST_TAB={WATCHLIST_TAB}")
        st.code(f"LOG_TAB={LOG_TAB}")
        st.code(f"POLYGON_KEY={'set' if POLYGON_KEY else 'missing'}")
    else:
        st.error("Missing GOOGLE_SHEET_ID")

    st.divider()
    st.caption("Session tuning (not persisted)")
    st.session_state.RR_TARGET = st.number_input("RR_TARGET", 0.5, 10.0, st.session_state.RR_TARGET, 0.1)
    st.session_state.ALERT_PCT = st.number_input("ALERT_PCT (%)", 0.1, 10.0, st.session_state.ALERT_PCT, 0.1)
    st.session_state.REFRESH_SECS = st.number_input("Auto-Refresh (s)", 5, 300, st.session_state.REFRESH_SECS, 5)

if auto:
    st.experimental_rerun()

# ---------- Title ----------
st.title("Vega Cockpit — Day-1 MVP")
if not SHEET_ID:
    st.stop()

# ---------- Tabs ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Health", "Watchlist (Live)", "Journal/Health Log", "Logs", "Settings"]
)

# ---------- Health ----------
with tab1:
    st.subheader("Health checks")
    ok = True
    try:
        ws_watch = get_sheet(SHEET_ID, WATCHLIST_TAB)
        st.success(f"✅ Connected to Watchlist tab: {WATCHLIST_TAB}")
    except Exception as e:
        ok = False
        st.error(f"❌ Watchlist access failed: {e}")
        with st.expander("Details"):
            st.exception(e)
    try:
        ws_log = get_sheet(SHEET_ID, LOG_TAB)
        st.success(f"✅ Connected to Log tab: {LOG_TAB}")
        # Show active gid if available
        try:
            gid = getattr(ws_log, "id", None)
            if gid:
                st.caption(f"Log gid: {gid}")
        except Exception:
            pass
    except Exception as e:
        ok = False
        st.error(f"❌ Log access failed: {e}")
        with st.expander("Details"):
            st.exception(e)

    st.write("—")
    st.write(f"Polygon key: {'✅ set' if POLYGON_KEY else '⚠️ missing'}")
    st.caption(datetime.utcnow().strftime("Checked at %Y-%m-%d %H:%M UTC"))
    if not ok:
        st.stop()

# ---------- Watchlist (live) ----------
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

            price  = quote(tkr)
            target = target_from_rr(entry, stopv, st.session_state.RR_TARGET) if entry and stopv else None
            rr     = compute_rr(entry, stopv, target) if target else None

            cols = st.columns([1.2, 2.5, 1, 1, 1.2, 1.6])
            cols[0].metric("Ticker", tkr)
            cols[1].write(f"**Strategy**\n{strat or '—'}")
            cols[2].metric("Entry", entry or "—")
            cols[3].metric("Stop",  stopv or "—")
            cols[4].metric("Price", f"{price:.2f}" if price is not None else "—")
            cols[5].metric("R/R→Target", rr if rr is not None else "—")

            # Signals + quick actions
            template_note = ""
            flagged = False
            if price is not None:
                try:
                    e_val = float(entry) if entry else None
                    s_val = float(stopv) if stopv else None
                except Exception:
                    e_val = s_val = None

                if e_val is not None:
                    dist = distance_pct(e_val, price)  # % above/below entry
                    if dist is not None and abs(dist) <= st.session_state.ALERT_PCT:
                        badge(f"{abs(dist)}% to entry", "#EAB308"); flagged = True
                        template_note = "Near entry"
                    if price >= e_val:
                        badge("Entry hit", "#22C55E"); flagged = True
                        template_note = "Entry hit"
                if s_val is not None and price <= s_val:
                    badge("At/under stop", "#EF4444"); flagged = True
                    template_note = "At/under stop"
            if not flagged:
                badge("Watching", "#3B82F6")

            # Quick log and quick actions
            with st.expander("Quick log / actions"):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    if st.button("Open", key=f"open_{tkr}"):
                        ok_, err = append_log_row_safe(symbol=tkr, kind="Trade", status="Open", notes=template_note or "Opened")
                        st.success("Logged Open.") if ok_ else st.error(err or "Append failed")
                with c2:
                    if st.button("Closed", key=f"closed_{tkr}"):
                        ok_, err = append_log_row_safe(symbol=tkr, kind="Trade", status="Closed", notes=template_note or "Closed")
                        st.success("Logged Closed.") if ok_ else st.error(err or "Append failed")
                with c3:
                    if st.button("Entry hit", key=f"hit_{tkr}"):
                        ok_, err = append_log_row_safe(symbol=tkr, kind="Trade", status="Info", notes="Entry hit")
                        st.success("Logged Entry hit.") if ok_ else st.error(err or "Append failed")
                with c4:
                    if st.button("Near entry", key=f"near_{tkr}"):
                        ok_, err = append_log_row_safe(symbol=tkr, kind="Trade", status="Info", notes="Near entry")
                        st.success("Logged Near entry.") if ok_ else st.error(err or "Append failed")

                kind   = st.selectbox("Type",   ["Journal", "Health", "Trade", "Note"], key=f"k_{tkr}")
                status = st.selectbox("Status", ["Open", "Closed", "Info", "Alert"],   key=f"s_{tkr}")
                note   = st.text_input("Notes", value=f"{template_note or (tkr + ': ' + (strat or ''))}")
                if st.button(f"Append to {LOG_TAB}", key=f"btn_{tkr}"):
                    ok_, err = append_log_row_safe(symbol=tkr, kind=kind, status=status, notes=note)
                    st.success("Logged.") if ok_ else st.error(err or "Append failed")
            st.divider()

# ---------- Journal / Health Log ----------
with tab3:
    st.subheader("Quick Log → Google Sheet")
    with st.form("quicklog"):
        col1, col2 = st.columns(2)
        with col1:
            kind   = st.selectbox("Type",   ["Journal", "Health", "Trade", "Note"], index=0)
            symbol = st.text_input("Symbol (optional)")
        with col2:
            status = st.selectbox("Status", ["Open", "Closed", "Info", "Alert"], index=0)
        notes = st.text_area("Notes", placeholder="What changed, why it matters, next action…", height=140)

        left, right = st.columns([1, 2])
        with left:
            submitted = st.form_submit_button(f"Append Row to '{LOG_TAB}'")
        with right:
            if st.form_submit_button("➕ Add Test Log Row"):
                ok_, err = append_log_row_safe(symbol="SPY", kind="Journal", status="Info", notes="Smoke test")
                st.success("Inserted a test row.") if ok_ else st.error(err or "Append failed")

        if submitted:
            ok_, err = append_log_row_safe(symbol=symbol.strip(), kind=kind, status=status, notes=notes.strip())
            st.success(f"Row appended to {LOG_TAB}.") if ok_ else st.error(err or "Append failed")

# ---------- Logs (filters, search, export, header guard) ----------
with tab4:
    st.subheader(f"Recent Log Rows from '{LOG_TAB}' (filterable)")

    try:
        ws = get_sheet(SHEET_ID, LOG_TAB)

        # Header guard + optional repair
        ensure_log_headers(ws)

        # Base DataFrame (up to 1000 rows, normalized)
        df_all = get_log_df_last(ws, limit=1000)

        # Parse timestamps for filtering
        if "Timestamp" in df_all.columns:
            df_all["__ts"] = df_all["Timestamp"].apply(parse_ts)
        else:
            df_all["__ts"] = None

        # Controls: date range, type, status, symbol, search
        c1, c2, c3, c4, c5 = st.columns([1.4, 1.4, 1.2, 1.2, 2.8])
        with c1:
            date_from = st.date_input("From", value=None)
        with c2:
            date_to = st.date_input("To", value=None)
        with c3:
            type_filter = st.multiselect("Type", sorted([x for x in df_all["Type"].dropna().unique() if x]), default=[])
        with c4:
            status_filter = st.multiselect("Status", sorted([x for x in df_all["Status"].dropna().unique() if x]), default=[])
        with c5:
            sym_filter = st.text_input("Symbol filter", value="").strip().upper()
        search = st.text_input("Search text", value="").strip()

        df = df_all.copy()

        # Date range filter
        if date_from:
            df = df[(df["__ts"].notna()) & (df["__ts"] >= dt.combine(date_from, dt.min.time()))]
        if date_to:
            df = df[(df["__ts"].notna()) & (df["__ts"] <= dt.combine(date_to, dt.max.time()))]

        # Type / Status filters
        if type_filter:
            df = df[df["Type"].isin(type_filter)]
        if status_filter:
            df = df[df["Status"].isin(status_filter)]

        # Symbol filter
        if sym_filter:
            df = df[df["Symbol"].fillna("").str.upper().str.contains(sym_filter)]

        # Text search across columns
        if search:
            mask = (
                df["Notes"].fillna("").str.contains(search, case=False, na=False) |
                df["Symbol"].fillna("").str.contains(search, case=False, na=False) |
                df["Type"].fillna("").str.contains(search, case=False, na=False) |
                df["Status"].fillna("").str.contains(search, case=False, na=False)
            )
            df = df[mask]

        # Final display (last 10 by timestamp desc if available)
        if df.empty:
            st.info("No matching rows.")
        else:
            if df["__ts"].notna().any():
                df = df.sort_values("__ts").tail(10)
            else:
                df = df.tail(10)
            view = df[LOG_HEADERS]
            st.dataframe(view, use_container_width=True, hide_index=True)

        # Export last 100 (post-filter) to CSV
        exp_df = df_all.copy()
        if exp_df["__ts"].notna().any():
            exp_df = exp_df.sort_values("__ts").tail(100)
        else:
            exp_df = exp_df.tail(100)
        exp_csv = exp_df[LOG_HEADERS].to_csv(index=False).encode("utf-8")
        st.download_button("Download last 100 as CSV", exp_csv, file_name="tradelog_last_100.csv")

    except Exception as e:
        st.error(f"Log view error: {e}")
        with st.expander("Details"):
            st.exception(e)

# ---------- Settings ----------
with tab5:
    st.subheader("Runtime settings")
    st.write({
        "GOOGLE_SHEET_ID": (SHEET_ID[:6] + "…" + SHEET_ID[-4:]) if SHEET_ID else "",
        "WATCHLIST_TAB": WATCHLIST_TAB,
        "LOG_TAB": LOG_TAB,
        "RR_TARGET (session)": st.session_state.RR_TARGET,
        "ALERT_PCT (session)": st.session_state.ALERT_PCT,
        "REFRESH_SECS (session)": st.session_state.REFRESH_SECS,
        "POLYGON_KEY_SET": bool(POLYGON_KEY),
    })

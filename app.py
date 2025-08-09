# app.py — Vega Cockpit (compact + persistence + backup/import + styling)
import os, time, io, requests, pandas as pd
from datetime import datetime as dt
import streamlit as st
from sheets_client import append_row, read_range, get_sheet
from config_client import get_config_dict, set_config_value

st.set_page_config(page_title="Vega Cockpit — MVP", layout="wide")

# --- Inline CSS: dark-friendly & compact spacing ---
st.markdown("""
<style>
body, .stApp { font-family: ui-sans-serif, system-ui, -apple-system; }
.block-container { padding-top: 1rem; padding-bottom: 3rem; }
[data-testid="stMetricValue"] { font-size: 1.1rem; }
[data-testid="stMetricDelta"] { font-size: 0.9rem; }
table { font-size: 0.92rem; }
</style>
""", unsafe_allow_html=True)

# --- Env ---
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
WATCHLIST_TAB = os.getenv("GOOGLE_SHEET_WATCHLIST_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "Watch List"))
LOG_TAB = os.getenv("GOOGLE_SHEET_LOG_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "TradeLog"))
POLYGON_KEY = os.getenv("POLYGON_KEY", "")

# --- Persistent settings (from sheet) with session defaults ---
_cfg = {}
try:
    _cfg = get_config_dict()
except Exception as e:
    st.sidebar.warning(f"Config read failed (using env defaults): {e}")

def _cfg_float(key, default):
    try: return float(_cfg.get(key, os.getenv(key, default)))
    except: return float(default)

def _cfg_int(key, default):
    try: return int(float(_cfg.get(key, os.getenv(key, default))))
    except: return int(default)

for k, v in dict(
    RR_TARGET=_cfg_float("RR_TARGET", "2.0"),
    ALERT_PCT=_cfg_float("ALERT_PCT", "1.5"),
    REFRESH_SECS=_cfg_int("REFRESH_SECS", "60"),
).items():
    st.session_state.setdefault(k, v)

LOG_HEADERS = ["Timestamp", "Type", "Symbol", "Status", "Notes"]

# --- Small helpers ---
def badge(text, color): st.markdown(f"<span style='background:{color};color:#fff;padding:2px 8px;border-radius:12px;font-size:12px'>{text}</span>", unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=15)
def quote(symbol, key):
    if "." in symbol or not key: return None
    try:
        r = requests.get(f"https://api.polygon.io/v2/last/trade/{symbol.upper()}?apiKey={key}", timeout=6)
        p = (r.json() or {}).get("results",{}).get("p") if r.status_code==200 else None
        return float(p) if p is not None else None
    except: return None

def target_from_rr(entry, stop, rr):
    try: e, s = float(entry), float(stop); return round(e + rr*(e-s), 2)
    except: return None

def compute_rr(entry, stop, target):
    try: e,s,t = float(entry),float(stop),float(target); r=abs(e-s); return round(abs(t-e)/r,2) if r>0 else None
    except: return None

def append_log(symbol="", kind="Journal", status="Open", notes=""):
    ts = dt.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    append_row(SHEET_ID, LOG_TAB, [ts, kind, symbol, status, notes])

def ensure_headers(ws):
    cur = [c.strip() for c in ((ws.get("A1:E1") or [[]])[0])]
    if cur != LOG_HEADERS: ws.update("A1", [LOG_HEADERS])

def fetch_log_df(ws, limit=1000):
    vals = ws.get("A1:E100000") or []
    if not vals: return pd.DataFrame(columns=LOG_HEADERS)
    hdr, rows = vals[0], vals[1:]
    norm = [(r + [""]*(len(hdr)-len(r)))[:len(hdr)] for r in rows]
    df = pd.DataFrame(norm, columns=hdr)
    return df.tail(limit)

def parse_ts(s): 
    try: return dt.strptime(s.replace(" UTC",""), "%Y-%m-%d %H:%M:%S")
    except: return None

# --- Sidebar ---
with st.sidebar:
    auto = st.toggle(f"Auto-refresh (every {st.session_state.REFRESH_SECS}s)", False)
    st.caption("Env / Config")
    st.code(f"SHEET_ID={SHEET_ID[:6]}…{SHEET_ID[-4:]}" if SHEET_ID else "Missing GOOGLE_SHEET_ID")
    st.code(f"WATCHLIST_TAB={WATCHLIST_TAB}"); st.code(f"LOG_TAB={LOG_TAB}")
    st.code(f"POLYGON_KEY={'set' if POLYGON_KEY else 'missing'}")
    st.divider(); st.caption("Session tuning (persist to Config)")
    rrt = st.number_input("RR_TARGET", 0.5, 10.0, st.session_state.RR_TARGET, 0.1)
    alp = st.number_input("ALERT_PCT (%)", 0.1, 10.0, st.session_state.ALERT_PCT, 0.1)
    ars = st.number_input("Auto-Refresh (s)", 5, 300, st.session_state.REFRESH_SECS, 5)
    if st.button("Save to Config"):
        try:
            set_config_value("RR_TARGET", str(rrt)); set_config_value("ALERT_PCT", str(alp)); set_config_value("REFRESH_SECS", str(ars))
            st.session_state.RR_TARGET, st.session_state.ALERT_PCT, st.session_state.REFRESH_SECS = rrt, alp, ars
            st.success("Saved to Config ✅")
        except Exception as e:
            st.error(f"Save failed: {e}")

if auto: st.experimental_rerun()

st.title("Vega Cockpit — Day-1 MVP")
if not SHEET_ID: st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Health","Watchlist (Live)","Journal/Health Log","Logs","Settings"])

# --- Health ---
with tab1:
    ok=True
    try: ws_watch = get_sheet(SHEET_ID, WATCHLIST_TAB); st.success(f"✅ Watchlist: {WATCHLIST_TAB}")
    except Exception as e: st.error(f"❌ Watchlist: {e}"); ok=False; st.expander("Details").exception(e)
    try:
        ws_log = get_sheet(SHEET_ID, LOG_TAB); st.success(f"✅ Log: {LOG_TAB}")
        gid = getattr(ws_log,"id",None); 
        if gid: st.caption(f"Log gid: {gid}")
    except Exception as e: st.error(f"❌ Log: {e}"); ok=False; st.expander("Details").exception(e)
    st.write("—"); st.write(f"Polygon key: {'✅ set' if POLYGON_KEY else '⚠️ missing'}")
    st.caption(dt.utcnow().strftime("Checked at %Y-%m-%d %H:%M UTC"))
    if not ok: st.stop()

# --- Watchlist row renderer ---
def render_watch_row(row):
    tkr = (row[0] if len(row)>0 else "").strip().upper()
    if not tkr: return
    strat = row[1] if len(row)>1 else ""; entry = row[2] if len(row)>2 else ""; stopv = row[3] if len(row)>3 else ""
    price = quote(tkr, POLYGON_KEY); tgt = target_from_rr(entry, stopv, st.session_state.RR_TARGET) if entry and stopv else None
    rr = compute_rr(entry, stopv, tgt) if tgt else None
    c = st.columns([1.2,2.5,1,1,1.2,1.6])
    c[0].metric("Ticker",tkr); c[1].write(f"**Strategy**\n{strat or '—'}")
    c[2].metric("Entry",entry or "—"); c[3].metric("Stop",stopv or "—")
    c[4].metric("Price", f"{price:.2f}" if price is not None else "—"); c[5].metric("R/R→Target", rr if rr is not None else "—")

    # signals + template
    tpl=""; flagged=False
    try: e_val = float(entry) if entry else None; s_val = float(stopv) if stopv else None
    except: e_val=s_val=None
    if price is not None:
        if e_val is not None:
            dist = round(100*(e_val-price)/e_val,2)
            if abs(dist) <= st.session_state.ALERT_PCT: badge(f"{abs(dist)}% to entry","#EAB308"); flagged=True; tpl="Near entry"
            if price >= e_val: badge("Entry hit","#22C55E"); flagged=True; tpl="Entry hit"
        if s_val is not None and price <= s_val: badge("At/under stop","#EF4444"); flagged=True; tpl="At/under stop"
    if not flagged: badge("Watching","#3B82F6")

    with st.expander("Quick log / actions"):
        cols = st.columns(4)
        for lbl,kind,status,notes,key in [
            ("Open","Trade","Open", tpl or "Opened","open"),
            ("Closed","Trade","Closed",tpl or "Closed","closed"),
            ("Entry hit","Trade","Info","Entry hit","hit"),
            ("Near entry","Trade","Info","Near entry","near"),
        ]:
            if cols[["open","closed","hit","near"].index(key)].button(lbl,key=f"{key}_{tkr}"):
                try: append_log(tkr, kind, status, notes); st.success(f"Logged {lbl}.")
                except Exception as e: st.error(f"Append failed: {e}")
        kind = st.selectbox("Type",["Journal","Health","Trade","Note"],key=f"k_{tkr}")
        status = st.selectbox("Status",["Open","Closed","Info","Alert"],key=f"s_{tkr}")
        note = st.text_input("Notes", value=tpl or f"{tkr}: {strat}")
        if st.button(f"Append to {LOG_TAB}", key=f"btn_{tkr}"):
            try: append_log(tkr, kind, status, note); st.success("Logged.")
            except Exception as e: st.error(f"Append failed: {e}")
    st.divider()

# --- Watchlist (Live) ---
with tab2:
    st.subheader("Watchlist — live with alerts")
    st.caption(f"Reads {WATCHLIST_TAB}!A2:D50 → Ticker | Strategy | Entry | Stop")
    rows = read_range(SHEET_ID, f"{WATCHLIST_TAB}!A2:D50") or []
    if not rows: st.info("No rows found. Add tickers to your Watch List sheet.")
    else:
        for r in rows: render_watch_row(r)

# --- Journal / Health Log ---
with tab3:
    st.subheader("Quick Log → Google Sheet")
    with st.form("quicklog"):
        c1,c2 = st.columns(2)
        kind = c1.selectbox("Type",["Journal","Health","Trade","Note"],0)
        symbol = c1.text_input("Symbol (optional)")
        status = c2.selectbox("Status",["Open","Closed","Info","Alert"],0)
        notes = st.text_area("Notes", height=140, placeholder="What changed, why it matters, next action…")
        left,right = st.columns([1,2])
        sub = left.form_submit_button(f"Append Row to '{LOG_TAB}'")
        test = right.form_submit_button("➕ Add Test Log Row")
        try:
            if sub: append_log(symbol.strip(), kind, status, notes.strip()); st.success(f"Row appended to {LOG_TAB}.")
            if test: append_log("SPY","Journal","Info","Smoke test"); st.success("Inserted test row.")
        except Exception as e: st.error(f"Append failed: {e}")

# --- Logs (filters, search, export, backup/import) ---
with tab4:
    st.subheader(f"Recent Log Rows from '{LOG_TAB}' (filterable)")
    try:
        ws = get_sheet(SHEET_ID, LOG_TAB); ensure_headers(ws)
        df_all = fetch_log_df(ws, 5000)
        df_all["__ts"] = df_all["Timestamp"].apply(parse_ts) if "Timestamp" in df_all.columns else None

        c1,c2,c3,c4,c5 = st.columns([1.4,1.4,1.2,1.2,2.8])
        date_from = c1.date_input("From", value=None); date_to   = c2.date_input("To", value=None)
        f_type    = c3.multiselect("Type",   sorted(x for x in df_all["Type"].dropna().unique()), [])
        f_status  = c4.multiselect("Status", sorted(x for x in df_all["Status"].dropna().unique()), [])
        f_symbol  = c5.text_input("Symbol filter", "").strip().upper()
        f_text    = st.text_input("Search text", "").strip()

        df = df_all.copy()
        if date_from: df = df[(df["__ts"].notna()) & (df["__ts"] >= dt.combine(date_from, dt.min.time()))]
        if date_to:   df = df[(df["__ts"].notna()) & (df["__ts"] <= dt.combine(date_to, dt.max.time()))]
        if f_type:    df = df[df["Type"].isin(f_type)]
        if f_status:  df = df[df["Status"].isin(f_status)]
        if f_symbol:  df = df[df["Symbol"].fillna("").str.upper().str.contains(f_symbol)]
        if f_text:
            mask = (df["Notes"].fillna("").str.contains(f_text, case=False) |
                    df["Symbol"].fillna("").str.contains(f_text, case=False) |
                    df["Type"].fillna("").str.contains(f_text, case=False) |
                    df["Status"].fillna("").str.contains(f_text, case=False))
            df = df[mask]

        if df.empty: st.info("No matching rows.")
        else:
            df = df.sort_values("__ts").tail(10) if df["__ts"].notna().any() else df.tail(10)
            st.dataframe(df[LOG_HEADERS], use_container_width=True, hide_index=True)

        # Export last 100 & Full backup (CSV)
        exp = (df_all.sort_values("__ts").tail(100) if df_all["__ts"].notna().any() else df_all.tail(100))[LOG_HEADERS]
        st.download_button("Download last 100 as CSV", exp.to_csv(index=False).encode("utf-8"), "tradelog_last_100.csv")
        full_csv = df_all[LOG_HEADERS].to_csv(index=False).encode("utf-8")
        st.download_button("Download FULL log (CSV)", full_csv, "tradelog_full.csv")

        # Backup to a new sheet tab (suffix date)
        if st.button("Backup TradeLog to new tab"):
            try:
                sh = ws.spreadsheet
                bname = f"{LOG_TAB}_Backup_{dt.utcnow():%Y%m%d}"
                new_ws = sh.add_worksheet(title=bname, rows=len(df_all)+5, cols=5)
                new_ws.update("A1", [LOG_HEADERS])
                if not df_all.empty:
                    new_ws.update("A2", df_all[LOG_HEADERS].values.tolist())
                st.success(f"Backup created: {bname}")
            except Exception as e:
                st.error(f"Backup failed: {e}")

        # Import (append) from CSV
        up = st.file_uploader("Import CSV to append (Timestamp,Type,Symbol,Status,Notes)", type=["csv"])
        if up:
            try:
                imp = pd.read_csv(up).fillna("")
                missing_cols = [c for c in LOG_HEADERS if c not in imp.columns]
                if missing_cols:
                    st.error(f"CSV missing columns: {missing_cols}")
                else:
                    rows = imp[LOG_HEADERS].values.tolist()
                    # chunk append to avoid API limits
                    for i in range(0, len(rows), 200):
                        ws.append_rows(rows[i:i+200], value_input_option="USER_ENTERED")
                    st.success(f"Imported {len(rows)} rows.")
            except Exception as e:
                st.error(f"Import failed: {e}")

    except Exception as e:
        st.error(f"Log view error: {e}"); st.expander("Details").exception(e)

# --- Settings ---
with tab5:
    st.subheader("Runtime settings")
    st.write({
        "GOOGLE_SHEET_ID": (SHEET_ID[:6]+"…"+SHEET_ID[-4:]) if SHEET_ID else "",
        "WATCHLIST_TAB": WATCHLIST_TAB, "LOG_TAB": LOG_TAB,
        "RR_TARGET (session)": st.session_state.RR_TARGET,
        "ALERT_PCT (session)": st.session_state.ALERT_PCT,
        "REFRESH_SECS (session)": st.session_state.REFRESH_SECS,
        "POLYGON_KEY_SET": bool(POLYGON_KEY),
    })

# app.py — Vega Cockpit (compact + persistence + backup/import + styling)
import os, time, io, requests, pandas as pd
from datetime import datetime as dt
import streamlit as st
from sheets_client import append_row, read_range, get_sheet
from config_client import get_config_dict, set_config_value

st.set_page_config(page_title="Vega Cockpit — MVP", layout="wide")

st.markdown("""
<style>
body, .stApp { font-family: ui-sans-serif, system-ui, -apple-system; }
.block-container { padding-top: 1rem; padding-bottom: 3rem; }
[data-testid="stMetricValue"] { font-size: 1.1rem; }
[data-testid="stMetricDelta"] { font-size: 0.9rem; }
table { font-size: 0.92rem; }
</style>
""", unsafe_allow_html=True)

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
WATCHLIST_TAB = os.getenv("GOOGLE_SHEET_WATCHLIST_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "Watch List"))
LOG_TAB = os.getenv("GOOGLE_SHEET_LOG_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "TradeLog"))
POLYGON_KEY = os.getenv("POLYGON_KEY", "")

_cfg = {}
try: _cfg = get_config_dict()
except Exception as e: st.sidebar.warning(f"Config read failed (env defaults): {e}")

def _cfg_float(k, d): 
    try: return float(_cfg.get(k, os.getenv(k, d)))
    except: return float(d)
def _cfg_int(k, d):
    try: return int(float(_cfg.get(k, os.getenv(k, d))))
    except: return int(d)

for k, v in dict(
    RR_TARGET=_cfg_float("RR_TARGET", "2.0"),
    ALERT_PCT=_cfg_float("ALERT_PCT", "1.5"),
    REFRESH_SECS=_cfg_int("REFRESH_SECS", "60"),
).items(): st.session_state.setdefault(k, v)

LOG_HEADERS = ["Timestamp", "Type", "Symbol", "Status", "Notes"]

def badge(t, c): st.markdown(f"<span style='background:{c};color:#fff;padding:2px 8px;border-radius:12px;font-size:12px'>{t}</span>", unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=15)
def quote(symbol, key):
    if "." in symbol or not key: return None
    try:
        r = requests.get(f"https://api.polygon.io/v2/last/trade/{symbol.upper()}?apiKey={key}", timeout=6)
        p = (r.json() or {}).get("results",{}).get("p") if r.status_code==200 else None
        return float(p) if p is not None else None
    except: return None

def target_from_rr(e, s, rr):
    try: e, s = float(e), float(s); return round(e + rr*(e-s), 2)
    except: return None
def compute_rr(e, s, t):
    try: e,s,t = float(e),float(s),float(t); r=abs(e-s); return round(abs(t-e)/r,2) if r>0 else None
    except: return None

def append_log(sym="", kind="Journal", status="Open", notes=""):
    ts = dt.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    append_row(SHEET_ID, LOG_TAB, [ts, kind, sym, status, notes])

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
        except Exception as e: st.error(f"Save failed: {e}")
if auto: st.experimental_rerun()

st.title("Vega Cockpit — MVP")
if not SHEET_ID: st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Health","Watchlist (Live)","Journal/Health Log","Logs","Settings"])

with tab1:
    ok=True
    try: ws_watch = get_sheet(SHEET_ID, WATCHLIST_TAB); st.success(f"✅ Watchlist: {WATCHLIST_TAB}")
    except Exception as e: st.error(f"❌ Watchlist: {e}"); ok=False; st.expander("Details").exception(e)
    try: ws_log = get_sheet(SHEET_ID, LOG_TAB); st.success(f"✅ Log: {LOG_TAB}")
    except Exception as e: st.error(f"❌ Log: {e}"); ok=False; st.expander("Details").exception(e)
    st.write("—"); st.write(f"Polygon key: {'✅ set' if POLYGON_KEY else '⚠️ missing'}")
    st.caption(dt.utcnow().strftime("Checked at %Y-%m-%d %H:%M UTC"))
    if not ok: st.stop()

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

with tab2:
    st.subheader("Watchlist — live")
    rows = read_range(SHEET_ID, f"{WATCHLIST_TAB}!A2:D50") or []
    if not rows: st.info("No rows found.")
    else:
        for r in rows: render_watch_row(r)

with tab3:
    st.subheader("Quick Log")
    with st.form("quicklog"):
        c1,c2 = st.columns(2)
        kind = c1.selectbox("Type",["Journal","Health","Trade","Note"],0)
        symbol = c1.text_input("Symbol (optional)")
        status = c2.selectbox("Status",["Open","Closed","Info","Alert"],0)
        notes = st.text_area("Notes", height=140)
        left,right = st.columns([1,2])
        sub = left.form_submit_button(f"Append Row to '{LOG_TAB}'")
        test = right.form_submit_button("➕ Add Test Log Row")
        if sub: append_log(symbol.strip(), kind, status, notes.strip()); st.success(f"Row appended to {LOG_TAB}.")
        if test: append_log("SPY","Journal","Info","Smoke test"); st.success("Inserted test row.")

with tab4:
    st.subheader(f"Recent Log Rows from '{LOG_TAB}' (filterable)")
    try:
        ws = get_sheet(SHEET_ID, LOG_TAB); ensure_headers(ws)
        df_all = fetch_log_df(ws, 5000)
        df_all["__ts"] = df_all["Timestamp"].apply(parse_ts)
        st.dataframe(df_all.tail(10)[LOG_HEADERS], use_container_width=True, hide_index=True)
    except Exception as e: st.error(f"Log view error: {e}"); st.expander("Details").exception(e)

with tab5:
    st.subheader("Runtime settings")
    st.write({
        "GOOGLE_SHEET_ID": (SHEET_ID[:6]+"…"+SHEET_ID[-4:]) if SHEET_ID else "",
        "WATCHLIST_TAB": WATCHLIST_TAB, "LOG_TAB": LOG_TAB,
        "RR_TARGET": st.session_state.RR_TARGET,
        "ALERT_PCT": st.session_state.ALERT_PCT,
        "REFRESH_SECS": st.session_state.REFRESH_SECS,
        "POLYGON_KEY_SET": bool(POLYGON_KEY),
    })

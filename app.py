# app.py — Vega Cockpit (with softer dark mode fix)
import os, io, pandas as pd
from datetime import datetime as dt
import streamlit as st
from sheets_client import append_row, read_range, get_sheet, write_range, clear_range
from config_client import get_config_dict, set_config_value
from price_client import get_price

st.set_page_config(page_title="Vega Cockpit — MVP", layout="wide")

# --- Theme CSS ---
THEMES = {
    "Light": """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
    }
    [data-testid="stMetricValue"] { font-size: 1.05rem }
    table { font-size: .92rem }
    </style>
    """,
    "Dark": """
    <style>
    html, body, .stApp {
        background: #1e1e1e;   /* Softer dark grey */
        color: #e5e7eb;
    }
    section div { color: inherit; }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
    }
    [data-testid="stMetricValue"] { font-size: 1.05rem }
    table { font-size: .92rem }
    /* Make alert boxes visible in dark mode */
    .stAlert {
        background-color: #2b2b2b !important;
        border: 1px solid #4caf50 !important;
        color: #e5e7eb !important;
    }
    </style>
    """
}
st.session_state.setdefault("THEME", "Dark")
st.markdown(THEMES[st.session_state.THEME], unsafe_allow_html=True)

# --- Env + persisted config ---
SHEET_ID      = os.getenv("GOOGLE_SHEET_ID", "")
WATCHLIST_TAB = os.getenv("GOOGLE_SHEET_WATCHLIST_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "Watch List"))
LOG_TAB       = os.getenv("GOOGLE_SHEET_LOG_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "TradeLog"))

_cfg = {}
try:
    _cfg = get_config_dict()
except Exception as e:
    st.sidebar.warning(f"Config read failed: {e}")

def _cfgf(k, d): 
    try: return float(_cfg.get(k, os.getenv(k, d)))
    except: return float(d)
def _cfgi(k, d):
    try: return int(float(_cfg.get(k, os.getenv(k, d))))
    except: return int(d)

for k, v in dict(RR_TARGET=_cfgf("RR_TARGET","2.0"),
                 ALERT_PCT=_cfgf("ALERT_PCT","1.5"),
                 REFRESH_SECS=_cfgi("REFRESH_SECS","60")).items():
    st.session_state.setdefault(k, v)

PINNED = set(x.strip().upper() for x in _cfg.get("PINNED","").split(",") if x.strip())
LOG_HEADERS = ["Timestamp","Type","Symbol","Status","Notes"]

# --- Helpers ---
def badge(t,c): st.markdown(f"<span style='background:{c};color:#fff;padding:2px 8px;border-radius:12px;font-size:12px'>{t}</span>", unsafe_allow_html=True)
def tgt_rr(e,s,rr):
    try: e,s=float(e),float(s); return round(e+rr*(e-s),2)
    except: return None
def rr_val(e,s,t):
    try: e,s,t=float(e),float(s),float(t); r=abs(e-s); return round(abs(t-e)/r,2) if r>0 else None
    except: return None
def append_log(sym="",kind="Journal",status="Open",notes=""):
    ts = dt.utcnow().strftime("%Y-%m-%d %H:%M:%S"); append_row(SHEET_ID, LOG_TAB, [ts,kind,sym,status,notes])
def ensure_headers(ws):
    cur = [c.strip() for c in ((ws.get("A1:E1") or [[]])[0])]
    if cur != LOG_HEADERS: ws.update("A1", [LOG_HEADERS])
def fetch_log_df(ws, limit=5000):
    vals = ws.get("A1:E100000") or []
    if not vals: return pd.DataFrame(columns=LOG_HEADERS)
    hdr, rows = vals[0], vals[1:]
    norm = [(r+[""]*(len(hdr)-len(r)))[:len(hdr)] for r in rows]
    return pd.DataFrame(norm, columns=hdr).tail(limit)
def parse_ts(s):
    try: return dt.strptime(s.replace(" UTC",""), "%Y-%m-%d %H:%M:%S")
    except: return None

# --- Sidebar ---
with st.sidebar:
    st.selectbox("Theme", list(THEMES), index=(0 if st.session_state.THEME=="Light" else 1), key="THEME")
    auto = st.toggle(f"Auto-refresh ({int(st.session_state.REFRESH_SECS)}s)", False)
    st.caption("Env / Config")
    st.code(f"SHEET_ID={SHEET_ID[:6]}…{SHEET_ID[-4:]}" if SHEET_ID else "Missing GOOGLE_SHEET_ID")
    st.code(f"WATCHLIST_TAB={WATCHLIST_TAB}"); st.code(f"LOG_TAB={LOG_TAB}")
    st.divider(); st.caption("Session tuning → Persist to Config")
    rrt  = st.number_input("RR_TARGET", .5, 10.0, float(st.session_state.RR_TARGET), .1)
    alp  = st.number_input("ALERT_PCT (%)", .1, 10.0, float(st.session_state.ALERT_PCT), .1)
    ars  = st.number_input("Auto-Refresh (s)", 5, 300, int(st.session_state.REFRESH_SECS), 5)
    pins = st.text_input("Pinned tickers (comma-separated)", ", ".join(sorted(PINNED)))
    if st.button("Save to Config"):
        try:
            set_config_value("RR_TARGET", str(rrt)); set_config_value("ALERT_PCT", str(alp))
            set_config_value("REFRESH_SECS", str(ars)); set_config_value("PINNED", pins)
            st.session_state.RR_TARGET, st.session_state.ALERT_PCT, st.session_state.REFRESH_SECS = rrt, alp, ars
            st.success("Saved ✅")
        except Exception as e: st.error(f"Save failed: {e}")
if auto: st.experimental_rerun()

st.title("Vega Cockpit — MVP")
if not SHEET_ID: st.stop()
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Health","Watchlist (Live)","Journal/Health Log","Logs","Settings"])

# --- Health ---
with tab1:
    ok=True
    try: ws_w = get_sheet(SHEET_ID, WATCHLIST_TAB); st.success(f"✅ Watchlist: {WATCHLIST_TAB}")
    except Exception as e: ok=False; st.error(f"❌ Watchlist: {e}"); st.expander("Details").exception(e)
    try: ws_l = get_sheet(SHEET_ID, LOG_TAB); ensure_headers(ws_l); st.success(f"✅ Log: {LOG_TAB}")
    except Exception as e: ok=False; st.error(f"❌ Log: {e}"); st.expander("Details").exception(e)
    if not ok: st.stop()
    st.caption(dt.utcnow().strftime("Checked at %Y-%m-%d %H:%M UTC"))

# --- Watchlist helpers ---
def watch_row_flags(price, entry, stop):
    tpl=""; near=hit=atstop=False
    try: e=float(entry) if entry else None; s=float(stop) if stop else None
    except: e=s=None
    if price is not None:
        if e is not None:
            dist = round(100*(e-price)/e,2)
            if abs(dist) <= float(st.session_state.ALERT_PCT): near=True; tpl="Near entry"
            if price >= e: hit=True; tpl="Entry hit"
        if s is not None and price <= s: atstop=True; tpl="At/under stop"
    return tpl, near, hit, atstop

# --- Watchlist (Live) ---
with tab2:
    st.subheader("Watchlist — live")
    rows = read_range(SHEET_ID, f"{WATCHLIST_TAB}!A2:D200") or []
    if not rows: st.info("No rows in Watch List.")
    else:
        rows = [r for r in rows if any(x.strip() for x in r)]
        rows.sort(key=lambda r: (0 if (len(r)>0 and r[0].strip().upper() in PINNED) else 1, r[0] if r else ""))
        for r in rows:
            tkr   = (r[0] if len(r)>0 else "").strip().upper()
            strat =  r[1] if len(r)>1 else ""
            entry =  r[2] if len(r)>2 else ""
            stopv =  r[3] if len(r)>3 else ""
            if not tkr: continue
            price = get_price(tkr)
            tgt   = tgt_rr(entry, stopv, float(st.session_state.RR_TARGET)) if entry and stopv else None
            rv    = rr_val(entry, stopv, tgt) if tgt else None
            tpl, near, hit, atstop = watch_row_flags(price, entry, stopv)

            cols = st.columns([1.2,2.5,1,1,1.2,1.6])
            cols[0].metric("Ticker", tkr); cols[1].write(f"**Strategy**\n{strat or '—'}")
            cols[2].metric("Entry", entry or "—"); cols[3].metric("Stop",  stopv or "—")
            cols[4].metric("Price", f"{price:.2f}" if price is not None else "—"); cols[5].metric("R/R→Target", rv if rv is not None else "—")
            if near: badge("Near entry","#EAB308")
            if hit: badge("Entry hit","#22C55E")
            if atstop: badge("At/under stop","#EF4444")
            if not (near or hit or atstop): badge("Watching","#3B82F6")

# --- Journal / Health Log ---
with tab3:
    st.subheader("Quick Log")
    with st.form("quicklog"):
        c1,c2 = st.columns(2)
        kind   = c1.selectbox("Type",["Journal","Health","Trade","Note"],0)
        symbol = c1.text_input("Symbol (optional)")
        status = c2.selectbox("Status",["Open","Closed","Info","Alert"],0)
        notes  = st.text_area("Notes", height=140)
        left,right = st.columns([1,2])
        sub  = left.form_submit_button(f"Append Row to '{LOG_TAB}'")
        test = right.form_submit_button("➕ Add Test Log Row")
        if sub:  append_log(symbol.strip(), kind, status, notes.strip()); st.success(f"Row appended to {LOG_TAB}.")
        if test: append_log("SPY","Journal","Info","Smoke test"); st.success("Inserted test row.")

# --- Logs ---
with tab4:
    st.subheader(f"Recent Log Rows from '{LOG_TAB}' (enriched)")
    try:
        ws = get_sheet(SHEET_ID, LOG_TAB); ensure_headers(ws)
        df_all = fetch_log_df(ws, 2000); df_all["__ts"] = df_all["Timestamp"].apply(parse_ts)
        wl = read_range(SHEET_ID, f"{WATCHLIST_TAB}!A2:D200") or []
        wl_map = { (r[0] if len(r)>0 else "").strip().upper(): (r[2] if len(r)>2 else "") for r in wl if r and r[0] }
        df = df_all.sort_values("__ts").tail(10).copy()
        prices, deltas = [], []
        for _, row in df.iterrows():
            sym = (row.get("Symbol") or "").strip().upper()
            price = get_price(sym) if sym else None
            entry = wl_map.get(sym)
            try:
                delta = round(100*(float(price)-float(entry))/float(entry),2) if (price is not None and entry) else None
            except: delta = None
            prices.append(price if price is not None else "")
            deltas.append(f"{delta:+.2f}%" if delta is not None else "")
        df["Price"] = prices; df["Δ% vs entry"] = deltas
        st.dataframe(df[LOG_HEADERS+["Price","Δ% vs entry"]], use_container_width=True, hide_index=True)
    except Exception as e:
        st.error("Log view error."); st.expander("Details").exception(e)

with tab5:
    st.subheader("Runtime settings")
    st.write({
        "GOOGLE_SHEET_ID": (SHEET_ID[:6]+"…"+SHEET_ID[-4:]) if SHEET_ID else "",
        "WATCHLIST_TAB": WATCHLIST_TAB, "LOG_TAB": LOG_TAB,
        "RR_TARGET": float(st.session_state.RR_TARGET),
        "ALERT_PCT": float(st.session_state.ALERT_PCT),
        "REFRESH_SECS": int(st.session_state.REFRESH_SECS),
        "THEME": st.session_state.THEME
    })

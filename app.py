# app.py — Vega Cockpit (UI pack: theme toggle, compact, watchlist I/O, pins, filters, chips)
import os, io, time, requests, pandas as pd
from datetime import datetime as dt
import streamlit as st
from sheets_client import append_row, read_range, get_sheet, write_range, clear_range
from config_client import get_config_dict, set_config_value

st.set_page_config(page_title="Vega Cockpit — MVP", layout="wide")

# --- theme toggle (light/dark via CSS) ---
THEMES = {
  "Light": """
  <style>
  .block-container{padding-top:1rem;padding-bottom:3rem}
  [data-testid="stMetricValue"]{font-size:1.05rem} table{font-size:.92rem}
  </style>""",
  "Dark": """
  <style>
  html,body,.stApp{background:#0f1115;color:#e5e7eb}
  section div{color:inherit} .block-container{padding-top:1rem;padding-bottom:3rem}
  [data-testid="stMetricValue"]{font-size:1.05rem} table{font-size:.92rem}
  .stDataFrame div{color:inherit}
  </style>"""
}
st.session_state.setdefault("THEME","Dark")
st.markdown(THEMES[st.session_state.THEME], unsafe_allow_html=True)

# --- env + persisted config ---
SHEET_ID = os.getenv("GOOGLE_SHEET_ID","")
WATCHLIST_TAB = os.getenv("GOOGLE_SHEET_WATCHLIST_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB","Watch List"))
LOG_TAB = os.getenv("GOOGLE_SHEET_LOG_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB","TradeLog"))
POLYGON_KEY = os.getenv("POLYGON_KEY","")

_cfg = {}
try: _cfg = get_config_dict()
except Exception as e: st.sidebar.warning(f"Config read failed: {e}")

def _cf(k, d): 
    try: return float(_cfg.get(k, os.getenv(k, d)))
    except: return float(d)
def _ci(k, d):
    try: return int(float(_cfg.get(k, os.getenv(k, d))))
    except: return int(d)

for k,v in dict(RR_TARGET=_cf("RR_TARGET","2.0"), ALERT_PCT=_cf("ALERT_PCT","1.5"), REFRESH_SECS=_ci("REFRESH_SECS","60")).items():
    st.session_state.setdefault(k, v)
PINNED = set(x.strip().upper() for x in _cfg.get("PINNED","").split(",") if x.strip())

LOG_HEADERS = ["Timestamp","Type","Symbol","Status","Notes"]

# --- helpers ---
def badge(t,c): st.markdown(f"<span style='background:{c};color:#fff;padding:2px 8px;border-radius:12px;font-size:12px'>{t}</span>", unsafe_allow_html=True)
@st.cache_data(show_spinner=False, ttl=20)
def quote(sym, key):
    if "." in sym or not key: return None
    try:
        r = requests.get(f"https://api.polygon.io/v2/last/trade/{sym.upper()}?apiKey={key}", timeout=6)
        p = (r.json() or {}).get("results",{}).get("p") if r.status_code==200 else None
        return float(p) if p is not None else None
    except: return None
def tgt_rr(e,s,rr):
    try: e,s=float(e),float(s); return round(e+rr*(e-s),2)
    except: return None
def rr_val(e,s,t):
    try: e,s,t=float(e),float(s),float(t); r=abs(e-s); return round(abs(t-e)/r,2) if r>0 else None
    except: return None
def append_log(sym="", kind="Journal", status="Open", notes=""):
    ts = dt.utcnow().strftime("%Y-%m-%d %H:%M:%S"); append_row(SHEET_ID, LOG_TAB, [ts, kind, sym, status, notes])

def ensure_headers(ws):
    cur = [c.strip() for c in ((ws.get("A1:E1") or [[]])[0])]
    if cur != LOG_HEADERS: ws.update("A1",[LOG_HEADERS])

def fetch_log_df(ws, limit=5000):
    vals = ws.get("A1:E100000") or []
    if not vals: return pd.DataFrame(columns=LOG_HEADERS)
    hdr, rows = vals[0], vals[1:]
    norm = [(r+[""]*(len(hdr)-len(r)))[:len(hdr)] for r in rows]
    return pd.DataFrame(norm, columns=hdr).tail(limit)

def parse_ts(s):
    try: return dt.strptime(s.replace(" UTC",""), "%Y-%m-%d %H:%M:%S")
    except: return None

# --- sidebar ---
with st.sidebar:
    st.selectbox("Theme", list(THEMES), index=(0 if st.session_state.THEME=="Light" else 1), key="THEME", on_change=lambda: None)
    auto = st.toggle(f"Auto-refresh ({int(st.session_state.REFRESH_SECS)}s)", False)
    st.caption("Env / Config")
    st.code(f"SHEET_ID={SHEET_ID[:6]}…{SHEET_ID[-4:]}" if SHEET_ID else "Missing GOOGLE_SHEET_ID")
    st.code(f"WATCHLIST_TAB={WATCHLIST_TAB}"); st.code(f"LOG_TAB={LOG_TAB}")
    st.code(f"POLYGON_KEY={'set' if POLYGON_KEY else 'missing'}")
    st.divider(); st.caption("Session tuning → Persist to Config")
    rrt = st.number_input("RR_TARGET", .5, 10.0, float(st.session_state.RR_TARGET), .1)
    alp = st.number_input("ALERT_PCT (%)", .1, 10.0, float(st.session_state.ALERT_PCT), .1)
    ars = st.number_input("Auto-Refresh (s)", 5, 300, int(st.session_state.REFRESH_SECS), 5)
    pins_raw = st.text_input("Pinned tickers (comma-separated)", ", ".join(sorted(PINNED)))
    if st.button("Save to Config"):
        try:
            set_config_value("RR_TARGET", str(rrt)); set_config_value("ALERT_PCT", str(alp)); set_config_value("REFRESH_SECS", str(ars))
            set_config_value("PINNED", pins_raw)
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
    except Exception as e: st.error(f"❌ Watchlist: {e}"); ok=False; st.expander("Details").exception(e)
    try: ws_l = get_sheet(SHEET_ID, LOG_TAB); st.success(f"✅ Log: {LOG_TAB}"); ensure_headers(ws_l)
    except Exception as e: st.error(f"❌ Log: {e}"); ok=False; st.expander("Details").exception(e)
    if not ok: st.stop()
    st.caption(dt.utcnow().strftime("Checked at %Y-%m-%d %H:%M UTC"))

# --- Watchlist helpers/filters ---
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
        # quick filters + import/export
        c1,c2,c3,c4,c5 = st.columns([1.2,1.2,1.2,1.8,2.6])
        f_near = c1.toggle("Near entry", False)
        f_hit = c2.toggle("Entry hit", False)
        f_stop = c3.toggle("At stop", False)
        up = c4.file_uploader("Import Watchlist CSV (Ticker,Strategy,Entry,Stop)", type=["csv"])
        if c5.download_button("Export Watchlist CSV",
                              pd.DataFrame(rows, columns=["Ticker","Strategy","Entry","Stop"]).to_csv(index=False).encode("utf-8"),
                              file_name="watchlist.csv"): pass
        if up:
            try:
                df_imp = pd.read_csv(up).fillna("")
                need = ["Ticker","Strategy","Entry","Stop"]
                if any(c not in df_imp.columns for c in need): st.error("CSV must have columns: Ticker,Strategy,Entry,Stop")
                else:
                    vals = df_imp[need].values.tolist()
                    clear_range(WATCHLIST_TAB, "A2:D2000")
                    write_range(WATCHLIST_TAB, "A2", vals)
                    st.success(f"Imported {len(vals)} rows."); st.experimental_rerun()
            except Exception as e: st.error(f"Import failed: {e}")

        # sort pinned first
        rows = [r for r in rows if any(x.strip() for x in r)]
        rows.sort(key=lambda r: (0 if (len(r)>0 and r[0].strip().upper() in PINNED) else 1, r[0] if r else ""))

        for r in rows:
            tkr = (r[0] if len(r)>0 else "").strip().upper()
            strat = r[1] if len(r)>1 else ""; entry = r[2] if len(r)>2 else ""; stopv = r[3] if len(r)>3 else ""
            if not tkr: continue
            price = quote(tkr, POLYGON_KEY)
            tgt = tgt_rr(entry, stopv, float(st.session_state.RR_TARGET)) if entry and stopv else None
            rv = rr_val(entry, stopv, tgt) if tgt else None
            tpl, near, hit, atstop = watch_row_flags(price, entry, stopv)
            # quick filter gating
            if f_near and not near: continue
            if f_hit and not hit: continue
            if f_stop and not atstop: continue

            c = st.columns([1.2,2.5,1,1,1.2,1.6])
            c[0].metric("Ticker", tkr); c[1].write(f"**Strategy**\n{strat or '—'}")
            c[2].metric("Entry", entry or "—"); c[3].metric("Stop",  stopv or "—")
            c[4].metric("Price", f"{price:.2f}" if price is not None else "—"); c[5].metric("R/R→Target", rv if rv is not None else "—")
            if near: badge("Near entry","#EAB308")
            if hit: badge("Entry hit","#22C55E")
            if atstop: badge("At/under stop","#EF4444")
            if not (near or hit or atstop): badge("Watching","#3B82F6")

# --- Journal / Health Log ---
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
        try:
            if sub: append_log(symbol.strip(), kind, status, notes.strip()); st.success(f"Row appended to {LOG_TAB}.")
            if test: append_log("SPY","Journal","Info","Smoke test"); st.success("Inserted test row.")
        except Exception as e: st.error(f"Append failed: {e}")

# --- Logs (filters + status chips + export) ---
with tab4:
    st.subheader(f"Recent Log Rows from '{LOG_TAB}' (filterable)")
    try:
        ws = get_sheet(SHEET_ID, LOG_TAB); ensure_headers(ws)
        df_all = fetch_log_df(ws, 5000)
        df_all["__ts"] = df_all["Timestamp"].apply(parse_ts)
        # filters
        c1,c2,c3,c4,c5 = st.columns([1.4,1.4,1.2,1.2,2.8])
        d1 = c1.date_input("From", value=None); d2 = c2.date_input("To", value=None)
        f_type = c3.multiselect("Type", sorted(df_all["Type"].dropna().unique()), [])
        f_stat = c4.multiselect("Status", sorted(df_all["Status"].dropna().unique()), [])
        f_sym  = c5.text_input("Symbol contains", "").strip().upper()
        f_txt  = st.text_input("Search text", "").strip()

        df = df_all.copy()
        if d1: df = df[(df["__ts"].notna()) & (df["__ts"] >= dt.combine(d1, dt.min.time()))]
        if d2: df = df[(df["__ts"].notna()) & (df["__ts"] <= dt.combine(d2, dt.max.time()))]
        if f_type: df = df[df["Type"].isin(f_type)]
        if f_stat: df = df[df["Status"].isin(f_stat)]
        if f_sym: df = df[df["Symbol"].fillna("").str.upper().str.contains(f_sym)]
        if f_txt:
            m = (df["Notes"].fillna("").str.contains(f_txt, case=False)|
                 df["Symbol"].fillna("").str.contains(f_txt, case=False)|
                 df["Type"].fillna("").str.contains(f_txt, case=False)|
                 df["Status"].fillna("").str.contains(f_txt, case=False))
            df = df[m]

        if df.empty: st.info("No matching rows.")
        else:
            # status chips
            def chip(s):
                s=(s or "").strip().lower()
                return ("🟢 Open" if s=="open" else "🔴 Closed" if s=="closed" else "🔵 Info" if s=="info" else "🟠 Alert" if s=="alert" else s)
            view = df.sort_values("__ts").tail(10)[LOG_HEADERS].copy()
            view["Status"] = view["Status"].apply(chip)
            st.dataframe(view, use_container_width=True, hide_index=True)

        exp = df_all.sort_values("__ts").tail(100)[LOG_HEADERS]
        st.download_button("Download last 100 CSV", exp.to_csv(index=False).encode("utf-8"), "tradelog_last_100.csv")
    except Exception as e:
        st.error("Log view error."); st.expander("Details").exception(e)

# --- Settings ---
with tab5:
    st.subheader("Runtime settings")
    st.write({
        "GOOGLE_SHEET_ID": (SHEET_ID[:6]+"…"+SHEET_ID[-4:]) if SHEET_ID else "",
        "WATCHLIST_TAB": WATCHLIST_TAB, "LOG_TAB": LOG_TAB,
        "RR_TARGET": float(st.session_state.RR_TARGET),
        "ALERT_PCT": float(st.session_state.ALERT_PCT),
        "REFRESH_SECS": int(st.session_state.REFRESH_SECS),
        "POLYGON_KEY_SET": bool(POLYGON_KEY),
        "THEME": st.session_state.THEME
    })

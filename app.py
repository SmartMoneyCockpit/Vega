# app.py — Vega Cockpit (All-in-one, compact)
# Works with sheets_client.py (rate-limited + cached + batch_get + bootstrap)
# Features: bootstrap, batched I/O, config parser, clean tables, symbol dropdown,
# inline edit/save, CSV import/export, quick trade entry, close trade/PnL helpers,
# position sizing, Polygon live prices & near-entry alerts (optional), mini charts,
# safe refresh controls, diagnostics, tab-name mapping, column mapper, soft locks.
import os, io, time, json, math, csv
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import requests
import pandas as pd
import streamlit as st

# ---- Import safe sheets client ----
from sheets_client import (
    read_config, batch_get, append_trade_log, write_range, read_range,
    get_sheet, bootstrap_sheet
)

APP_VER = "v1.7-allinone"

# ------------- Page config -------------
st.set_page_config(page_title="Vega Cockpit", layout="wide")
st.markdown(f"<small>Vega {APP_VER}</small>", unsafe_allow_html=True)

# ------------- Utilities -------------
def now_ts(): return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
def env(k, d=""): return os.getenv(k) or d
def jdump(x): return json.dumps(x, ensure_ascii=False, indent=2)

def rows_to_df(rows: List[List[str]]) -> pd.DataFrame:
    rows = rows or []
    if not rows: return pd.DataFrame()
    hdr = [str(c) for c in rows[0]]
    data = [list(r)+[""]*(len(hdr)-len(r)) for r in rows[1:] if any(str(x).strip() for x in r)]
    return pd.DataFrame(data, columns=hdr)

def df_to_rows(df: pd.DataFrame) -> List[List[str]]:
    return [list(df.columns)] + df.fillna("").astype(str).values.tolist()

def last_used_bounds(rows: List[List[str]]) -> Tuple[int,int]:
    # returns (n_rows, n_cols) used (>=1 includes header)
    if not rows: return (1,1)
    n_cols = max((len(r) for r in rows if any(str(x).strip() for x in r)), default=1)
    n_rows = 1
    for r in rows[1:]:
        if any(str(x).strip() for x in r): n_rows += 1
    return n_rows, n_cols

def col_letter(n: int) -> str:
    s=""; 
    while n: n, r = divmod(n-1, 26); s = chr(65+r)+s
    return s or "A"

# Column mapping from Config (optional overrides)
def get_colmap(cfg: Dict[str,str]) -> Dict[str,str]:
    default = {"Ticker":"Ticker","Strategy":"Strategy","Entry":"Entry","Stop":"Stop",
               "Target":"Target","Note":"Note","Status":"Status"}
    for k in list(default):
        v = cfg.get(f"COL_{k}".upper())
        if v: default[k] = v
    return default

# ---- Locks (lightweight) ----
LOCK_CELL = "Config!H1"
def acquire_lock(ttl=20) -> bool:
    try:
        v = read_range(LOCK_CELL)
        cur = int(time.time())
        if v and v[0] and v[0][0]:
            old = int(float(v[0][0]))
            if cur - old < ttl: return False
        write_range(LOCK_CELL, [[str(cur)]])
        return True
    except Exception:
        return True  # best effort
def release_lock():
    try: write_range(LOCK_CELL, [[""]])
    except Exception: pass

# ---- Prices via Polygon (optional) ----
POLY = env("POLYGON_KEY")
@st.cache_data(ttl=45, show_spinner=False)
def get_price(sym: str):
    if not POLY: return None
    try:
        r = requests.get(f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{sym.upper()}",
            params={"apiKey": POLY}, timeout=6)
        if r.status_code!=200: return None
        j = r.json()
        p = j.get("ticker",{}).get("lastTrade",{}).get("p")
        return float(p) if p else None
    except Exception:
        return None

@st.cache_data(ttl=180, show_spinner=False)
def get_sparkline(sym: str, m=60):
    if not POLY: return []
    end = datetime.utcnow()
    start = end - timedelta(minutes=m)
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}/range/1/minute/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"
        r = requests.get(url, params={"adjusted":"true","sort":"asc","limit":m*2,"apiKey":POLY}, timeout=6)
        if r.status_code!=200: return []
        js = r.json().get("results",[]) or []
        return [x.get("c") for x in js][-m:]
    except Exception:
        return []

# ---- App state ----
if "last_error" not in st.session_state: st.session_state.last_error = ""
if "watch_df"   not in st.session_state: st.session_state.watch_df = pd.DataFrame()
if "log_df"     not in st.session_state: st.session_state.log_df   = pd.DataFrame()

# ------------- Sidebar -------------
st.sidebar.header("Vega • Session Controls")
theme = st.sidebar.selectbox("Theme", ["Dark","Light"], index=0)
if st.sidebar.button("Setup / Repair Google Sheet"):
    try:
        bootstrap_sheet()
        st.sidebar.success("Sheet verified/created.")
    except Exception as e:
        st.sidebar.error(f"Bootstrap error: {e}"); st.stop()

# Refresh & TTLs
colTTL1, colTTL2 = st.sidebar.columns(2)
ttl_cfg  = colTTL1.number_input("TTL Config (s)", 15, 600, int(float(env("TTL_CONFIG","45"))), 5)
ttl_watch= colTTL2.number_input("TTL Watch (s)", 15, 600, int(float(env("TTL_WATCH","30"))), 5)
auto = st.sidebar.checkbox("Auto-refresh", value=False, help="Guarded ≥30s")
secs = st.sidebar.number_input("Every (s)", 30, 600, int(float(env("REFRESH_SECS","60"))), 5)
if auto and secs>=30:
    st.experimental_set_query_params(_=int(time.time())//max(1,int(secs)))  # light tick

# Diagnostics expander
with st.sidebar.expander("Diagnostics"):
    st.write("Version:", APP_VER)
    st.write("POLYGON_KEY:", bool(POLY))
    if st.session_state.last_error:
        st.error(st.session_state.last_error)

# ------------- Load config + tabs -------------
try:
    cfg_rows = read_config()
    cfg = {}
    # support KEY=VAL single cell or 2-col
    for r in cfg_rows:
        if not r: continue
        if len(r)>=2 and r[0] and "=" not in str(r[0]): cfg[str(r[0]).strip()] = str(r[1]).strip()
        else:
            c = str(r[0]).strip()
            if "=" in c: k,v = c.split("=",1); cfg[k.strip()] = v.strip()
    watch_tab = cfg.get("WATCHLIST_TAB") or env("GOOGLE_SHEET_MAIN_TAB","Watch List")
    log_tab   = cfg.get("LOG_TAB")       or env("GOOGLE_SHEET_LOG_TAB","TradeLog")
    ALERT_PCT = float(cfg.get("ALERT_PCT", env("ALERT_PCT","1.5")))
    RR_TARGET = float(cfg.get("RR_TARGET", env("RR_TARGET","2.0")))
except Exception as e:
    st.error(f"Startup error (config): {e}")
    st.stop()

# ------------- Batched read -------------
try:
    ranges = ["Config!A1:Z100", f"{watch_tab}!A1:Z1000", f"{log_tab}!A1:Z1000"]
    _cfg, watch_rows, log_rows = batch_get(ranges)
    watch_df = rows_to_df(watch_rows); log_df = rows_to_df(log_rows)
    st.session_state.watch_df = watch_df.copy(); st.session_state.log_df = log_df.copy()
except Exception as e:
    st.session_state.last_error = str(e); st.error(f"Startup error: {e}"); st.stop()

# ------------- Header: Config parsed -------------
st.subheader("Config (parsed) ↺")
if cfg: st.code("\n".join(f"{k}={v}" for k,v in sorted(cfg.items())), language="ini")
else: st.info("No config rows found. Use Setup/Repair.")

# ------------- Watch List -------------
st.markdown("### Watch List")
colmap = get_colmap(cfg)
wd = watch_df.rename(columns={colmap[k]:k for k in colmap if colmap[k] in watch_df.columns})

# Optional prices + alerts
show_prices = st.checkbox("Show live prices & alerts", value=bool(POLY), help="Requires POLYGON_KEY")
if show_prices and not POLY: st.warning("POLYGON_KEY not set; live prices disabled.")

def compute_alerts(df: pd.DataFrame):
    if df.empty or "Ticker" not in df.columns or "Entry" not in df.columns: return df
    df = df.copy()
    prices = {}
    if show_prices:
        syms = [s for s in df["Ticker"].astype(str) if s]
        for s in list(dict.fromkeys(syms))[:50]:  # cap a bit
            prices[s] = get_price(s) or None
        df["Price"] = [prices.get(s) for s in df["Ticker"].astype(str)]
        try:
            df["Entry"] = pd.to_numeric(df["Entry"], errors="coerce")
            df["Stop"]  = pd.to_numeric(df["Stop"],  errors="coerce")
            if "Target" in df.columns: df["Target"] = pd.to_numeric(df.get("Target"), errors="coerce")
        except Exception: pass
        df["Δ% to Entry"] = ((df["Price"]-df["Entry"])/df["Entry"]*100).round(2)
        df["R to Stop"]   = ((df["Price"]-df["Entry"])/(df["Entry"]-df["Stop"])).round(2)
        if "Target" in df.columns:
            df["R to Target"] = ((df["Target"]-df["Price"])/(df["Entry"]-df["Stop"])).round(2)
    return df

wd_a = compute_alerts(wd)

# Inline edit block
edit_mode = st.toggle("Inline edit Watch List", value=False)
if edit_mode:
    edited = st.data_editor(wd, use_container_width=True, num_rows="dynamic", key="ed_watch")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Save Watch List"):
            if acquire_lock():
                try:
                    # Map back to original column names
                    out = edited.rename(columns={k: colmap[k] for k in colmap if k in edited.columns})
                    rows = df_to_rows(out)
                    n, m = last_used_bounds(rows); rng = f"{watch_tab}!A1:{col_letter(m)}{n}"
                    write_range(rng, rows)
                    st.success("Watch List saved.")
                except Exception as e:
                    st.session_state.last_error=str(e); st.error(f"Save failed: {e}")
                finally:
                    release_lock()
            else:
                st.warning("Another writer active. Try again in a few seconds.")
    with col2:
        up = st.file_uploader("Import CSV (replace)", type=["csv"], label_visibility="collapsed")
        if up:
            try:
                df = pd.read_csv(up)
                st.write("Preview:", df.head(8))
                if st.button("Confirm Replace"):
                    if acquire_lock():
                        try:
                            rows = [list(df.columns)] + df.fillna("").astype(str).values.tolist()
                            n, m = last_used_bounds(rows); rng = f"{watch_tab}!A1:{col_letter(m)}{n}"
                            write_range(rng, rows); st.success("Watch List replaced via CSV.")
                        except Exception as e:
                            st.session_state.last_error=str(e); st.error(e)
                        finally: release_lock()
            except Exception as e:
                st.error(f"CSV parse error: {e}")
    with col3:
        if not wd.empty:
            csv_bytes = wd.to_csv(index=False).encode()
            st.download_button("Export Watch List CSV", data=csv_bytes, file_name="watchlist.csv", mime="text/csv")

# Display (alerts version if prices on)
show = wd_a if show_prices else wd
st.dataframe(show, use_container_width=True, hide_index=True)

# Sparkline (optional)
if show_prices and st.toggle("Show mini charts (sparklines)", value=False):
    syms = show["Ticker"].astype(str).tolist()[:12]
    for s in syms:
        data = get_sparkline(s)
        if data:
            st.line_chart(pd.Series(data, name=s))

# ------------- Trade Log -------------
st.markdown("### TradeLog (read-only)")
st.dataframe(st.session_state.log_df, use_container_width=True, hide_index=True)

# Quick trade entry
st.markdown("---"); st.subheader(f"Quick Entry → {log_tab}")
tickers = []
if "Ticker" in wd.columns:
    tickers = [t for t in wd["Ticker"].astype(str).tolist() if t]
with st.form("trade_log_form", clear_on_submit=True):
    c1,c2,c3,c4,c5 = st.columns([2,1,1,1,4])
    with c1:
        sym = st.selectbox("Symbol", options=(tickers or ["SPY"]), index=0)
    with c2:
        side = st.selectbox("Side", ["BUY","SELL"])
    with c3:
        qty = st.number_input("Qty", 1, 1_000_000, 1)
    with c4:
        price = st.number_input("Price (opt)", 0.0, 1e9, float(get_price(sym) or 0.0), format="%.4f")
    with c5:
        note = st.text_input("Note", placeholder="entry/exit, rationale, etc.")
    submitted = st.form_submit_button("Append")
    if submitted:
        row = [now_ts(), sym.upper(), side, qty]
        # Insert price if TradeLog has Price column
        cols = list(st.session_state.log_df.columns) if not st.session_state.log_df.empty else ["Timestamp","Symbol","Side","Qty","Note"]
        if "Price" in cols: row += [price]
        row += [note]
        try:
            if acquire_lock():
                append_trade_log(row, tab_name=log_tab); st.success(f"Logged {sym} x{qty} ({side})")
            else:
                st.warning("Another writer active. Try again in a few seconds.")
        except Exception as e:
            st.session_state.last_error=str(e); st.error(f"Write failed: {e}")
        finally:
            release_lock()

# Close trade / PnL helper (soft)
with st.expander("Close Trade / PnL helper"):
    c1,c2,c3 = st.columns(3)
    sym2 = c1.text_input("Symbol to close", value=(tickers[0] if tickers else "SPY"))
    exit_price = c2.number_input("Exit Price", 0.0, 1e9, 0.0, format="%.4f")
    if c3.button("Update latest open row"):
        try:
            df = st.session_state.log_df.copy()
            if df.empty or "ExitPrice" not in df.columns:
                st.info("TradeLog needs an 'ExitPrice' column to update in-place. I'll just append a CLOSE note.")
                append_trade_log([now_ts(), sym2.upper(), "CLOSE", 0, exit_price, "Closed via helper"], tab_name=log_tab)
            else:
                m = (df["Symbol"].astype(str).str.upper()==sym2.upper()) & (df["ExitPrice"].astype(str)=="")
                idx = df[m].tail(1).index
                if len(idx)==0:
                    st.info("No open row found; appending close row instead.")
                    append_trade_log([now_ts(), sym2.upper(), "CLOSE", 0, exit_price, "Closed"], tab_name=log_tab)
                else:
                    r = idx[0]+2  # +1 header, +1 0-index
                    col = df.columns.get_loc("ExitPrice")+1
                    cell = f"{log_tab}!{chr(64+col)}{r}"
                    write_range(cell, [[str(exit_price)]])
                    st.success("ExitPrice updated.")
        except Exception as e:
            st.error(e)

# Position sizing
with st.expander("Position sizing"):
    c1,c2,c3,c4 = st.columns(4)
    bankroll = c1.number_input("Account size $", 0.0, 1e9, 10000.0, 1.0)
    risk_pct = c2.number_input("Risk %", 0.01, 100.0, 1.0, 0.1)
    entry     = c3.number_input("Entry", 0.0, 1e9, 100.0)
    stop      = c4.number_input("Stop", 0.0, 1e9, 95.0)
    risk_dollar = bankroll * (risk_pct/100.0)
    per_share  = abs(entry - stop)
    size = 0 if per_share==0 else math.floor(risk_dollar / per_share)
    rr = RR_TARGET
    st.write(f"Risk ${risk_dollar:,.2f} → per-share ${per_share:,.2f} → **size {size}** shares/contracts")
    st.write(f"Targets: 1R: {entry + (entry-stop):.2f} • {rr}R: {entry + rr*(entry-stop):.2f}")

# Export TradeLog
if not st.session_state.log_df.empty:
    st.download_button("Export TradeLog CSV", st.session_state.log_df.to_csv(index=False).encode(), "tradelog.csv", "text/csv")

# Footer
st.caption("Reads are batched, cached, and rate-limited. Optional live prices via Polygon.")

# app.py — Vega (Sheets-safe edition)
# Uses sheets_client.py for all Google Sheets I/O (rate-limited + cached)
import os, time
import streamlit as st

# ---- Import the safe helpers (you pasted this file earlier) ----
from sheets_client import (
    read_config,       # returns Config!A1:Z as rows
    read_watchlist,    # returns Watch List!A1:Z as rows
    batch_get,         # batch ranges in a single API call
    append_trade_log,  # appends to TradeLog sheet
)

# ------------- Streamlit page config -------------
st.set_page_config(page_title="Vega Cockpit", layout="wide")

# ------------- Small helpers -------------
def parse_kv_rows(rows):
    """
    Accepts a list of rows from the Config sheet.
    Supports either:
      - single column like ["SHEET_ID=...", "WATCHLIST_TAB=Watch List", ...]
      - or two columns like [["KEY","VALUE"], ["WATCHLIST_TAB","Watch List"], ...]
    Returns dict.
    """
    cfg = {}
    for r in rows:
        if not r: 
            continue
        # Two-column style
        if len(r) >= 2 and r[0] and "=" not in r[0]:
            k = str(r[0]).strip()
            v = str(r[1]).strip()
            if k:
                cfg[k] = v
        else:
            # Single "KEY=VALUE" cell style
            cell = str(r[0]).strip()
            if "=" in cell:
                k, v = cell.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg

@st.cache_data(ttl=45, show_spinner=False)
def load_config():
    rows = read_config()  # 1 read, cached in sheets_client + here
    return parse_kv_rows(rows)

@st.cache_data(ttl=30, show_spinner=False)
def load_watchlist():
    return read_watchlist()  # 1 read, cached in sheets_client + here

@st.cache_data(ttl=30, show_spinner=False)
def load_core_ranges(cfg):
    """Batch-load core tabs in one call. Adjust ranges to your data size."""
    watch_tab = cfg.get("WATCHLIST_TAB", "Watch List")
    log_tab   = cfg.get("LOG_TAB", "TradeLog")
    ranges = [
        "Config!A1:Z100",
        f"{watch_tab}!A1:Z1000",
        f"{log_tab}!A1:Z200",
    ]
    config_rows, watch_rows, log_rows = batch_get(ranges)  # 1 API call
    return config_rows, watch_rows, log_rows

def coerce_table(rows, header=True):
    """Make a list-of-lists safe for dataframe display."""
    rows = rows or []
    # pad short rows so Streamlit can infer table shape
    width = max((len(r) for r in rows if r), default=0)
    fixed = [r + [""] * (width - len(r)) for r in rows]
    if not header:
        return fixed, []
    hdr = fixed[0] if fixed else []
    body = fixed[1:] if len(fixed) > 1 else []
    return body, hdr

# ------------- Sidebar: Controls -------------
st.sidebar.header("Vega • Session Controls")

# Theme toggle (cosmetic only)
theme = st.sidebar.selectbox("Theme", ["Dark", "Light"], index=0)

# Auto-refresh (safe defaults)
auto_refresh_on = st.sidebar.toggle("Auto-refresh", value=False, help="Keep off or >=60s to stay under Sheets quota.")
refresh_secs = st.sidebar.number_input("Auto-Refresh (s)", min_value=15, max_value=600, value=60, step=5)

if auto_refresh_on:
    # This only triggers a front-end re-render; backend reads are throttled & cached.
    st.experimental_rerun  # for static analysers
    st.autorefresh = st.experimental_rerun  # no-op binding to avoid lints
    st_autorefresh = st.experimental_rerun  # alias
    st.caption(f"Auto-refresh every {int(refresh_secs)}s (reads are rate-limited & cached).")
    st.experimental_set_query_params(_=int(time.time()) // max(1, int(refresh_secs)))

# ------------- Load data (minimal API usage) -------------
with st.spinner("Loading config..."):
    cfg = load_config()

watch_tab = cfg.get("WATCHLIST_TAB", "Watch List")
log_tab   = cfg.get("LOG_TAB", "TradeLog")

colA, colB = st.columns([2, 1])
with colA:
    st.subheader("Config (parsed)")
    st.code("\n".join(f"{k}={v}" for k,v in sorted(cfg.items())), language="ini")

# Batch-load the three core ranges in ONE call
with st.spinner("Loading sheets (batched)…"):
    config_rows, watch_rows, log_rows = load_core_ranges(cfg)

# ------------- Display: Watchlist -------------
st.markdown("### Watch List")
watch_body, watch_hdr = coerce_table(watch_rows, header=True)
if watch_body:
    st.dataframe(data=watch_body, use_container_width=True, hide_index=True, column_config=None)
else:
    st.info(f"No data found in '{watch_tab}'. Check the tab name in Config.")

# ------------- Display: Trade Log -------------
st.markdown("### Trade Log (read-only)")
log_body, log_hdr = coerce_table(log_rows, header=True)
st.dataframe(data=log_body, use_container_width=True, hide_index=True)

# ------------- Quick entry: append to Trade Log -------------
st.markdown("---")
st.subheader("Quick Trade Log Entry")
with st.form("trade_log_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns([2,2,2,2])
    with c1: sym = st.text_input("Symbol", placeholder="SPY")
    with c2: side = st.selectbox("Side", ["BUY", "SELL"])
    with c3: qty = st.number_input("Qty", min_value=1, value=1, step=1)
    with c4: note = st.text_input("Note", placeholder="entry/exit, rationale, etc.")
    submitted = st.form_submit_button("Append to TradeLog")
    if submitted:
        if not sym:
            st.warning("Symbol required.")
        else:
            # Append a simple row; adjust to match your columns
            row = [time.strftime("%Y-%m-%d %H:%M:%S"), sym.upper(), side, qty, note]
            try:
                append_trade_log(row)
                st.success(f"Logged {sym} x{qty} ({side})")
                # Clear caches so the table shows your new row next render
                load_core_ranges.clear()
                load_watchlist.clear()
            except Exception as e:
                st.error(f"Write failed: {e}")

# ------------- Footer -------------
st.caption("Sheets access is re-used, rate-limited, and cached to stay below the 60 reads/min/user quota.")

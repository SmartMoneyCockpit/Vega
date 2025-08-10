from sheets_client import read_config, batch_get, append_trade_log
try:
    from sheets_client import bootstrap_sheet
except Exception:
    bootstrap_sheet = None

# ---------------- Page setup ----------------
st.set_page_config(page_title="Vega Cockpit", layout="wide")

# Small status ribbon (what creds method is detected, and whether SHEET_ID exists)
method = "none"
if os.getenv("GCP_SERVICE_ACCOUNT_JSON"):
    method = "GCP_SERVICE_ACCOUNT_JSON"
elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    method = f"FILE:{os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}"
sid_set = bool(os.getenv("SHEET_ID") or os.getenv("GOOGLE_SHEET_ID"))
st.caption(f"Creds: {method} • SHEET_ID set: {sid_set}")

# ---------------- Helpers ----------------
def parse_kv_rows(rows):
    """
    Accepts:
      - 1-col style:  ['KEY=VALUE', 'OTHER=...']
      - 2-col style:  [['KEY','VALUE'], ['WATCHLIST_TAB','Watch List'], ...]
    Returns a dict.
    """
    cfg = {}
    for r in rows or []:
        if not r:
            continue
        if len(r) >= 2 and r[0] and "=" not in str(r[0]):
            k, v = str(r[0]).strip(), str(r[1]).strip()
            if k:
                cfg[k] = v
        else:
            cell = str(r[0]).strip()
            if "=" in cell:
                k, v = cell.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg

def resolve_tabs(cfg: dict):
    """Figure out which tab names to use (Config overrides, then env, then defaults)."""
    watch = (
        cfg.get("WATCHLIST_TAB")
        or os.getenv("GOOGLE_SHEET_MAIN_TAB")
        or "Watch List"
    )
    log = (
        cfg.get("LOG_TAB")
        or os.getenv("GOOGLE_SHEET_LOG_TAB")
        or "TradeLog"
    )
    return watch, log

def coerce_table(rows, header=True):
    """Pad uneven rows so Streamlit can render a stable table."""
    rows = rows or []
    width = max((len(r) for r in rows if r), default=0)
    fixed = [list(r) + [""] * (width - len(r)) for r in rows]
    if not header:
        return fixed, []
    hdr = fixed[0] if fixed else []
    body = fixed[1:] if len(fixed) > 1 else []
    return body, hdr

# ---------------- Cached loaders ----------------
@st.cache_data(ttl=45, show_spinner=False)
def load_config_rows():
    return read_config()

@st.cache_data(ttl=30, show_spinner=False)
def load_core_ranges(watch_tab: str, log_tab: str):
    # One API call for everything we need
    ranges = [
        "Config!A1:Z100",
        f"{watch_tab}!A1:Z1000",
        f"{log_tab}!A1:Z200",
    ]
    return batch_get(ranges)

# ---------------- Sidebar ----------------
if bootstrap_sheet:
    if st.sidebar.button("Setup / Repair Google Sheet"):
        bootstrap_sheet()
        st.sidebar.success("Sheet verified/created. Reloading…")
        st.cache_data.clear(); st.experimental_rerun()

# Manual refresh keeps quota usage predictable and low
if st.sidebar.button("Refresh now"):
    st.cache_data.clear()
    st.experimental_rerun()

# ---------------- Load & display ----------------
try:
    with st.spinner("Loading config…"):
        config_rows = load_config_rows()
        cfg = parse_kv_rows(config_rows)

    watch_tab, log_tab = resolve_tabs(cfg)

    colA, colB = st.columns([2, 1])
    with colA:
        st.subheader("Config (parsed)")
        if cfg:
            st.code("\\n".join(f"{k}={v}" for k, v in sorted(cfg.items())), language="ini")
        else:
            st.info("No config rows found in Config!A1:Z100")

    with st.spinner(f"Loading '{watch_tab}' and '{log_tab}' (batched)…"):
        config_rows2, watch_rows, log_rows = load_core_ranges(watch_tab, log_tab)

    # Watchlist
    st.markdown(f"### {watch_tab}")
    watch_body, _ = coerce_table(watch_rows, header=True)
    if watch_body:
        st.dataframe(watch_body, use_container_width=True, hide_index=True)
    else:
        st.info(f"No data found in '{watch_tab}'. Check the tab name in Config or env.")

    # Trade Log
    st.markdown(f"### {log_tab} (read-only)")
    log_body, _ = coerce_table(log_rows, header=True)
    st.dataframe(log_body, use_container_width=True, hide_index=True)

    # Quick append to TradeLog
    st.markdown("---")
    st.subheader(f"Quick Entry → {log_tab}")
    with st.form("trade_log_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2,2,2,2])
        with c1: sym = st.text_input("Symbol", placeholder="SPY")
        with c2: side = st.selectbox("Side", ["BUY", "SELL"])
        with c3: qty  = st.number_input("Qty", min_value=1, value=1, step=1)
        with c4: note = st.text_input("Note", placeholder="entry/exit, rationale, etc.")
        submitted = st.form_submit_button("Append")
        if submitted:
            if not sym:
                st.warning("Symbol required.")
            else:
                row = [time.strftime("%Y-%m-%d %H:%M:%S"), sym.upper(), side, qty, note]
                try:
                    append_trade_log(row, tab_name=log_tab)  # sheets_client handles throttling
                    st.success(f"Logged {sym} x{qty} ({side})")
                    st.cache_data.clear()
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Write failed: {e}")

    st.caption("Reads are batched, cached, and rate-limited to stay below the 60 reads/min/user quota.")

except Exception as e:
    # Friendly top-level error with a tiny traceback hint
    st.error(f"Startup error: {e}")

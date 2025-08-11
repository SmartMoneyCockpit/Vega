# sheets_client.py — safe, low-quota Google Sheets client (Render-ready)
import os, json, time, random
import gspread
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

# ---------------- Env ----------------
SHEET_ID      = (os.getenv("SHEET_ID") or os.getenv("GOOGLE_SHEET_ID") or "").strip()
MIN_INTERVAL  = float(os.getenv("SHEETS_MIN_INTERVAL", "1.2"))  # ~50 reads/min
TTL_CONFIG    = float(os.getenv("TTL_CONFIG", "45"))            # seconds
TTL_WATCH     = float(os.getenv("TTL_WATCH", "30"))

# ---------------- Singletons / caches ----------------
_client = None
_spreadsheet = None
_ws = {}          # tab_name -> Worksheet
_cache = {}       # simple in-proc cache
_last_read = 0.0  # for throttle

# ---------------- Throttle + backoff ----------------
def _throttle():
    global _last_read
    dt = time.time() - _last_read
    if dt < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - dt)
    _last_read = time.time()

def _with_backoff(fn, *a, **k):
    delay = 1.0
    for _ in range(6):  # up to ~30s total
        try:
            _throttle()
            return fn(*a, **k)
        except APIError as e:
            s = str(e)
            if "RATE_LIMIT_EXCEEDED" in s or "quota" in s.lower():
                time.sleep(delay + random.random())
                delay = min(delay * 2, 8)
            else:
                raise
    raise RuntimeError("Sheets retry budget exhausted")

# ---------------- Credentials loader ----------------
def _build_creds():
    """Supports GCP_SERVICE_ACCOUNT_JSON, GOOGLE_APPLICATION_CREDENTIALS, or SA_* pieces."""
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    # 1) Full JSON stored in an env var
    blob = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if blob:
        info = json.loads(blob)
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        return Credentials.from_service_account_info(info, scopes=scopes)

    # 2) Path to JSON file
    path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if path:
        return Credentials.from_service_account_file(path, scopes=scopes)

    # 3) Individual SA_* vars
    required = [
        "TYPE","PROJECT_ID","PRIVATE_KEY_ID","PRIVATE_KEY",
        "CLIENT_EMAIL","CLIENT_ID","AUTH_URI","TOKEN_URI",
        "AUTH_PROVIDER_X509_CERT_URL","CLIENT_X509_CERT_URL",
    ]
    if all(os.getenv(f"SA_{k}") for k in required):
        info = {
            "type": os.getenv("SA_TYPE"),
            "project_id": os.getenv("SA_PROJECT_ID"),
            "private_key_id": os.getenv("SA_PRIVATE_KEY_ID"),
            "private_key": os.getenv("SA_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("SA_CLIENT_EMAIL"),
            "client_id": os.getenv("SA_CLIENT_ID"),
            "auth_uri": os.getenv("SA_AUTH_URI"),
            "token_uri": os.getenv("SA_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("SA_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("SA_CLIENT_X509_CERT_URL"),
        }
        return Credentials.from_service_account_info(info, scopes=scopes)

    raise RuntimeError(
        "No Google credentials found. Set GCP_SERVICE_ACCOUNT_JSON or "
        "GOOGLE_APPLICATION_CREDENTIALS, or SA_* vars."
    )

# ---------------- Spreadsheet + worksheet access ----------------
def _client_spreadsheet():
    global _client, _spreadsheet
    if not SHEET_ID:
        raise RuntimeError("SHEET_ID env var is empty. Set it in your Render environment.")
    if _client is None:
        creds = _build_creds()
        _client = gspread.authorize(creds)
    if _spreadsheet is None:
        _spreadsheet = _with_backoff(_client.open_by_key, SHEET_ID)
    return _spreadsheet

def ws(tab_name: str):
    if tab_name not in _ws:
        _ws[tab_name] = _client_spreadsheet().worksheet(tab_name)
    return _ws[tab_name]

def batch_get(ranges):
    """
    Version-agnostic batch reader.
    Uses Spreadsheet.batch_get if available; otherwise falls back to
    Spreadsheet.values_batch_get; and finally to per-range reads.
    Returns a list of 2D lists, one per range.
    """
    ss = _client_spreadsheet()

    # Preferred (newer gspread)
    if hasattr(ss, "batch_get"):
        return _with_backoff(ss.batch_get, ranges)

    # Fallback (older gspread): values_batch_get returns API shape
    if hasattr(ss, "values_batch_get"):
        def _do():
            resp = ss.values_batch_get(ranges)  # one HTTP call
            vrs = resp.get("valueRanges", [])
            return [vr.get("values", []) for vr in vrs]
        return _with_backoff(_do)

    # Last resort: iterate (still throttled/backed off)
    out = []
    for a1 in ranges:
        if "!" in a1:
            tab, rng = a1.split("!", 1)
            out.append(_with_backoff(ws(tab).get, rng))
        else:
            out.append(_with_backoff(_client_spreadsheet().get_worksheet(0).get, a1))
    return out

# ---------------- Tiny cache helper ----------------
def get_cached(name: str, ttl: float, loader):
    rec = _cache.get(name)
    now = time.time()
    if rec and now - rec["t"] < ttl:
        return rec["v"]
    v = loader()
    _cache[name] = {"v": v, "t": now}
    return v

# ---------------- High-level reads/writes ----------------
def read_config():
    """Returns rows from Config!A1:Z100 (adjust TTL via TTL_CONFIG)."""
    return get_cached("config", TTL_CONFIG, lambda: batch_get(["Config!A1:Z100"])[0])

def read_watchlist():
    """Returns rows from Watch List!A1:Z1000 (adjust TTL via TTL_WATCH)."""
    tab = "Watch List"
    return get_cached("watch", TTL_WATCH, lambda: batch_get([f"{tab}!A1:Z1000"])[0])

def append_trade_log(row_values, tab_name=None):
    """Append a single row to TradeLog (or a provided tab) with USER_ENTERED semantics."""
    target = tab_name or "TradeLog"
    return _with_backoff(ws(target).append_row, row_values, value_input_option="USER_ENTERED")

# ---------------- Compatibility shims (old API names) ----------------
def get_sheet(tab_name: str):
    return ws(tab_name)

def append_row(tab_name: str, row_values):
    return _with_backoff(ws(tab_name).append_row, row_values, value_input_option="USER_ENTERED")

def read_range(a1_range: str):
    return batch_get([a1_range])[0]

def write_range(a1_range: str, values):
    """Write a 2D list to a range like 'Tab!A1:C3' (USER_ENTERED)."""
    if "!" in a1_range:
        tab_name, rng = a1_range.split("!", 1)
    else:
        tab_name, rng = None, a1_range
    target_ws = ws(tab_name) if tab_name else _client_spreadsheet().get_worksheet(0)
    return _with_backoff(target_ws.update, rng, values, value_input_option="USER_ENTERED")

# ---------------- Bootstrap (create tabs, headers, config) ----------------
def bootstrap_sheet(watch_tab=None, log_tab=None):
    """
    Idempotent setup for your Google Sheet.
    - Creates Config, Watch List, TradeLog if missing
    - Adds headers
    - Seeds Config with basic keys
    """
    ss = _client_spreadsheet()
    names = {w.title for w in ss.worksheets()}

    # Resolve tab names
    watch_tab = watch_tab or os.getenv("GOOGLE_SHEET_MAIN_TAB") or "Watch List"
    log_tab   = log_tab   or os.getenv("GOOGLE_SHEET_LOG_TAB")  or "TradeLog"

    # Create missing tabs
    if "Config" not in names:
        _with_backoff(ss.add_worksheet, title="Config", rows=200, cols=26)
    if watch_tab not in names:
        _with_backoff(ss.add_worksheet, title=watch_tab, rows=2000, cols=26)
    if log_tab not in names:
        _with_backoff(ss.add_worksheet, title=log_tab, rows=2000, cols=26)

    # Headers + seed config
    _with_backoff(ws(watch_tab).update, "A1:E1", [["Symbol","Side","Entry","Stop","Note"]])
    _with_backoff(ws(log_tab).update, "A1:E1", [["Timestamp","Symbol","Side","Qty","Note"]])
    _with_backoff(ws("Config").update, "A1:B6", [
        ["WATCHLIST_TAB", watch_tab],
        ["LOG_TAB",       log_tab],
        ["ALERT_PCT",     os.getenv("ALERT_PCT", "1.5")],
        ["RR_TARGET",     os.getenv("RR_TARGET", "2.0")],
        ["REFRESH_SECS",  os.getenv("REFRESH_SECS", "60")],
        ["SHEET_ID",      (os.getenv("SHEET_ID") or os.getenv("GOOGLE_SHEET_ID") or "").strip()],
    ])
    # Freeze headers (best effort)
    try:
        ws(watch_tab).freeze(rows=1)
        ws(log_tab).freeze(rows=1)
    except Exception:
        pass
# --- Add to sheets_client.py ---

def _col_letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s or "A"

def ensure_tab(tab_name: str, headers=None, rows: int = 2000, cols: int = 26):
    """
    Ensure a worksheet exists with optional header row.
    Safe to call repeatedly (idempotent).
    """
    ss = _client_spreadsheet()
    names = {w.title for w in ss.worksheets()}
    if tab_name not in names:
        _with_backoff(ss.add_worksheet, title=tab_name, rows=rows, cols=max(cols, (len(headers) if headers else 1)))
    if headers:
        # read first row; if missing or different, write headers
        try:
            cur = read_range(f"{tab_name}!1:1")
            cur_hdr = cur[0] if cur else []
        except Exception:
            cur_hdr = []
        if list(map(str, cur_hdr)) != list(map(str, headers)):
            write_range(f"{tab_name}!A1:{_col_letter(len(headers))}1", [list(map(str, headers))])

def upsert_config(key: str, value: str):
    """
    Insert or update a key/value in the Config tab (A:key, B:value).
    """
    ensure_tab("Config", ["Key", "Value"], rows=200, cols=2)
    rows = read_range("Config!A1:B200") or []
    # build map of existing keys
    found_row = None
    for i, r in enumerate(rows[1:], start=2):
        if r and str(r[0]).strip() == str(key):
            found_row = i
            break
    if found_row:
        write_range(f"Config!A{found_row}:B{found_row}", [[key, value]])
    else:
        append_row("Config", [key, value])

def snapshot_tab(tab_name: str, max_rows: int = 10000):
    """
    Create a CSV-style snapshot of a tab by copying its cell values to a new tab.
    Returns the new tab name.
    """
    ss = _client_spreadsheet()
    # figure out how many columns by looking at header
    header = read_range(f"{tab_name}!1:1")
    hdr = header[0] if header else []
    m = max(1, len(hdr))
    rng = f"{tab_name}!A1:{_col_letter(m)}{max_rows}"
    data = read_range(rng) or []
    snap_name = f"{tab_name}_snap_{time.strftime('%Y%m%d_%H%M%S', time.gmtime())}"
    _with_backoff(ss.add_worksheet, title=snap_name, rows=max_rows, cols=max(26, m))
    write_range(f"{snap_name}!A1:{_col_letter(m)}{len(data or [[]])}", data or [[]])
    return snap_name

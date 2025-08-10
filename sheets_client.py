
# sheets_client.py — safe, low-quota Google Sheets client (Render-ready)
import os, json, time, random
import gspread
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

# ---------------- Env ----------------
SHEET_ID = os.getenv("SHEET_ID", "").strip()
MIN_INTERVAL = float(os.getenv("SHEETS_MIN_INTERVAL", "1.2"))  # ~50 reads/min
TTL_CONFIG   = float(os.getenv("TTL_CONFIG", "45"))            # seconds
TTL_WATCH    = float(os.getenv("TTL_WATCH", "30"))

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
            "private_key": os.getenv("SA_PRIVATE_KEY").replace("\\n","\n"),
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
    """Batch-read multiple A1 ranges in a single API call."""
    ss = _client_spreadsheet()
    return _with_backoff(ss.batch_get, ranges)

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
    # We can't read the tab name from Config until we can open the sheet, so we default here.
    tab = "Watch List"
    return get_cached("watch", TTL_WATCH, lambda: batch_get([f"{tab}!A1:Z1000"])[0])

def append_trade_log(row_values):
    """Append a single row to TradeLog (USER_ENTERED)."""
    return _with_backoff(ws("TradeLog").append_row, row_values, value_input_option="USER_ENTERED")

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

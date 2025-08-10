# sheets_client.py — safe, low-quota Google Sheets client
import os, time, random
import gspread
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

# --- env ---
SHEET_ID = os.getenv("SHEET_ID", "").strip()
MIN_INTERVAL = float(os.getenv("SHEETS_MIN_INTERVAL", "1.2"))  # ~50 rpm cap
# Optional small caches (seconds)
TTL_CONFIG   = float(os.getenv("TTL_CONFIG", "45"))
TTL_WATCH    = float(os.getenv("TTL_WATCH", "30"))

# --- singletons / caches ---
_client = None
_spreadsheet = None
_ws = {}
_cache = {}
_last_read = 0.0

def _throttle():
    global _last_read
    dt = time.time() - _last_read
    if dt < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - dt)
    _last_read = time.time()

def _with_backoff(fn, *a, **k):
    delay = 1.0
    for _ in range(6):  # up to ~30s
        try:
            _throttle()
            return fn(*a, **k)
        except APIError as e:
            if "RATE_LIMIT_EXCEEDED" in str(e) or "quota" in str(e).lower():
                time.sleep(delay + random.random())
                delay = min(delay * 2, 8)
            else:
                raise
    raise RuntimeError("Sheets retry budget exhausted")

def _client_spreadsheet():
    global _client, _spreadsheet
    if _client is None:
        # Assumes service-account creds via GOOGLE_APPLICATION_CREDENTIALS or explicit fields
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
            scopes=scopes
        )
        _client = gspread.authorize(creds)
    if _spreadsheet is None:
        _spreadsheet = _with_backoff(_client.open_by_key, SHEET_ID)
    return _spreadsheet

def ws(tab_name: str):
    if tab_name not in _ws:
        _ws[tab_name] = _client_spreadsheet().worksheet(tab_name)
    return _ws[tab_name]

def batch_get(ranges):
    # ranges like ["Config!A1:D50","Watch List!A1:G500"]
    ss = _client_spreadsheet()
    return _with_backoff(ss.batch_get, ranges)

def get_cached(name: str, ttl: float, loader):
    rec = _cache.get(name)
    now = time.time()
    if rec and now - rec["t"] < ttl:
        return rec["v"]
    v = loader()
    _cache[name] = {"v": v, "t": now}
    return v

# Convenience helpers you can call from app.py
def read_config():
    return get_cached("config", TTL_CONFIG,
        lambda: batch_get(["Config!A1:Z100"])[0])

def read_watchlist():
    return get_cached("watch", TTL_WATCH,
        lambda: batch_get(["Watch List!A1:Z1000"])[0])

def append_trade_log(row_values):
    # one write (writes are not the issue, but still throttle for safety)
    return _with_backoff(ws("TradeLog").append_row, row_values, value_input_option="USER_ENTERED")

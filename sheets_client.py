"""
sheets_client.py — Google Sheets helper for Vega

Auth sources (priority):
1) GOOGLE_SHEETS_CREDENTIALS_JSON -> absolute path to service-account JSON (e.g. /etc/secrets/credentials.json)
2) GCP_SERVICE_ACCOUNT_JSON        -> full JSON blob (string)
3) ./Json/credentials.json or ./credentials.json (fallback for local dev)

Sheet ID env: VEGA_SHEET_ID (or SHEET_ID / GOOGLE_SHEET_ID)

Environment tuning (optional):
- SHEETS_MIN_INTERVAL   : minimum seconds between API calls (default 2.5)
- VEGA_SHEETS_TTL_SEC   : Spreadsheet client cache TTL seconds (default 300)
- VEGA_SHEETS_RPM_SOFT  : soft limit (not enforced strictly; informational)
- VEGA_SHEETS_RPS_SOFT  : soft limit (not enforced strictly; informational)
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import List

import gspread
from gspread.exceptions import APIError, WorksheetNotFound

# ---------------------- Tuning / Throttle ----------------------

_MIN_INTERVAL = float(os.getenv("SHEETS_MIN_INTERVAL", "2.5"))
_TTL_SEC     = int(os.getenv("VEGA_SHEETS_TTL_SEC", "300"))

# Module-level throttle state
_last_call_ts: float = 0.0

def _throttle() -> None:
    """Ensure at least _MIN_INTERVAL seconds between live API calls."""
    global _last_call_ts
    now = time.time()
    wait = _MIN_INTERVAL - (now - _last_call_ts)
    if wait > 0:
        time.sleep(wait)
    _last_call_ts = time.time()

# ---------------------- Sheet ID / Credentials ----------------------

def _env_sheet_id() -> str:
    """Resolve the Google Sheet ID from env vars."""
    for k in ("VEGA_SHEET_ID", "SHEET_ID", "GOOGLE_SHEET_ID"):
        v = os.getenv(k, "").strip()
        if v:
            return v
    raise RuntimeError(
        "No Google Sheet ID found. Set VEGA_SHEET_ID (or SHEET_ID / GOOGLE_SHEET_ID) "
        "in your Render environment."
    )

# Simple TTL cache for credentials + client + spreadsheet
_creds_cache: dict | None = None
_gc_cache: gspread.Client | None = None
_ss_cache: gspread.Spreadsheet | None = None
_cache_born: float = 0.0

def _load_credentials_dict() -> dict:
    """
    Load service-account credentials as a dict using the priority order:
    1) GOOGLE_SHEETS_CREDENTIALS_JSON -> absolute path to file
    2) GCP_SERVICE_ACCOUNT_JSON        -> JSON string
    3) ./Json/credentials.json or ./credentials.json
    """
    # 1) Explicit secret-file path (Render Secret Files pattern)
    path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "").strip()
    if not path:
        # Popular default for Render Secret Files
        default_secret = "/etc/secrets/credentials.json"
        if os.path.exists(default_secret):
            path = default_secret

    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2) Full JSON blob in env
    blob = os.getenv("GCP_SERVICE_ACCOUNT_JSON", "").strip()
    if blob:
        return json.loads(blob)

    # 3) Local dev fallbacks
    for candidate in ("Json/credentials.json", "credentials.json"):
        if os.path.exists(candidate):
            with open(candidate, "r", encoding="utf-8") as f:
                return json.load(f)

    raise RuntimeError(
        "Google credentials not found. Use Render Secret Files and set "
        "GOOGLE_SHEETS_CREDENTIALS_JSON to the absolute path (e.g. /etc/secrets/credentials.json), "
        "or provide GCP_SERVICE_ACCOUNT_JSON."
    )

def _maybe_refresh_cache() -> None:
    """Invalidate the cached client/spreadsheet after TTL."""
    global _creds_cache, _gc_cache, _ss_cache, _cache_born
    if not _cache_born or (time.time() - _cache_born) > _TTL_SEC:
        _creds_cache = None
        _gc_cache = None
        _ss_cache = None
        _cache_born = time.time()

def _gc() -> gspread.Client:
    """Get a cached gspread client (refresh by TTL)."""
    global _creds_cache, _gc_cache, _cache_born
    _maybe_refresh_cache()
    if _gc_cache is None:
        _creds_cache = _creds_cache or _load_credentials_dict()
        _gc_cache = gspread.service_account_from_dict(_creds_cache)
    return _gc_cache

def _ss() -> gspread.Spreadsheet:
    """Get a cached Spreadsheet (refresh by TTL)."""
    global _ss_cache
    _maybe_refresh_cache()
    if _ss_cache is None:
        _throttle()  # opening by key hits the API
        _ss_cache = _gc().open_by_key(_env_sheet_id())
    return _ss_cache

# ---------------------- Resilient request helpers ----------------------

def _with_retries(fn, *args, **kwargs):
    """
    Call a function with throttle + small backoff on 429/5xx.
    Intended for short, single API operations.
    """
    delays = [0, 0.6, 1.2]  # up to ~2s extra
    last_exc = None
    for d in delays:
        if d:
            time.sleep(d)
        try:
            _throttle()
            return fn(*args, **kwargs)
        except APIError as e:
            last_exc = e
            # Retry on 429 or 5xx
            code = getattr(e, "response", None)
            code = getattr(code, "status_code", None) or getattr(e, "code", None)
            if code and int(code) in (429, 500, 502, 503, 504):
                continue
            raise
        except Exception as e:
            last_exc = e
            # Retry on generic transient network errors
            continue
    # If we exhausted retries, raise the last error
    if last_exc:
        raise last_exc

# ---------------------- Public API used by app.py ----------------------

def batch_get(ranges: List[str]) -> List[List[List[str]]]:
    """
    Get multiple A1 ranges possibly across worksheets.
    Returns list aligned with ranges, each item is a 2D list of values.
    """
    ss = _ss()
    out: List[List[List[str]]] = []
    for r in ranges:
        try:
            vals = _with_retries(ss.values_get, r).get("values", [])
        except Exception:
            vals = []
        out.append(vals)
    return out

def read_range(a1: str) -> List[List[str]]:
    """
    Read a range "Sheet!A1:Z" or "Sheet" (defaults to A1:Z2000).
    """
    tab, rng = (a1.split("!", 1) + ["A1:Z2000"])[:2] if "!" in a1 else (a1, "A1:Z2000")
    ws = _with_retries(_ss().worksheet, tab)
    try:
        return _with_retries(ws.get, rng) or []
    except Exception:
        return []

def write_range(a1: str, rows: List[List]) -> None:
    """Write values to a range; auto-creates the worksheet if needed."""
    tab, rng = (a1.split("!", 1) + ["A1"])[:2] if "!" in a1 else (a1, "A1")
    try:
        ws = _with_retries(_ss().worksheet, tab)
    except WorksheetNotFound:
        ws = _with_retries(_ss().add_worksheet, title=tab, rows=2000, cols=26)
    _with_retries(ws.update, rng, rows, value_input_option="USER_ENTERED")

def append_row(tab: str, row: List) -> None:
    """Append a single row to a worksheet; auto-creates the worksheet if needed."""
    try:
        ws = _with_retries(_ss().worksheet, tab)
    except WorksheetNotFound:
        ws = _with_retries(_ss().add_worksheet, title=tab, rows=2000, cols=26)
    cleaned = [("" if x is None else x) for x in row]
    _with_retries(ws.append_row, cleaned, value_input_option="USER_ENTERED")

def append_trade_log(row: List, tab_name: str = "NA_TradeLog") -> None:
    append_row(tab_name, row)

def ensure_tab(tab: str, headers: List[str]) -> None:
    """
    Ensure a tab exists and that header row contains at least the given headers
    (union; preserves existing order and columns).
    """
    ss = _ss()
    try:
        ws = _with_retries(ss.worksheet, tab)
    except WorksheetNotFound:
        ws = _with_retries(ss.add_worksheet, title=tab, rows=2000, cols=26)
        _with_retries(ws.update, "A1", [headers])
        return

    cur = _with_retries(ws.row_values, 1) or []
    if not cur:
        _with_retries(ws.update, "A1", [headers])
        return

    need = list(cur)
    changed = False
    for h in headers:
        if h not in need:
            need.append(h)
            changed = True
    if changed:
        _with_retries(ws.update, "A1", [need])

def read_config() -> List[List[str]]:
    """Return Config rows (2D values) or empty list if no tab."""
    try:
        ws = _with_retries(_ss().worksheet, "Config")
    except WorksheetNotFound:
        return []
    return _with_retries(ws.get, "A1:Z999") or []

def upsert_config(key: str, value: str) -> None:
    """
    Upsert a key/value into the Config tab.
    Creates the tab if missing and seeds header row.
    """
    ss = _ss()
    try:
        ws = _with_retries(ss.worksheet, "Config")
    except WorksheetNotFound:
        ws = _with_retries(ss.add_worksheet, title="Config", rows=200, cols=5)
        _with_retries(ws.update, "A1", [["Key", "Value"]])

    rows = _with_retries(ws.get_all_values)
    for i, r in enumerate(rows[1:], start=2):  # skip header
        if r and str(r[0]).strip() == key:
            _with_retries(ws.update, f"A{i}:B{i}", [[key, str(value)]])
            return
    _with_retries(ws.append_row, [key, str(value)], value_input_option="USER_ENTERED")

def bootstrap_sheet() -> List[str]:
    """
    Create core tabs with headers if they don't exist.
    Returns list of created tab names.
    """
    ss = _ss()
    created: List[str] = []

    def _mk(title: str, hdrs: List[str]):
        nonlocal created
        try:
            _with_retries(ss.worksheet, title)
        except WorksheetNotFound:
            ws = _with_retries(ss.add_worksheet, title=title, rows=2000, cols=26)
            _with_retries(ws.update, "A1", [hdrs])
            created.append(title)

    _mk("NA_Watch",  ["Ticker", "Country", "Strategy", "Entry", "Stop", "Target", "Note", "Status", "Audit"])
    _mk("APAC_Watch",["Ticker", "Country", "Strategy", "Entry", "Stop", "Target", "Note", "Status", "Audit"])

    _mk("NA_TradeLog",   ["Timestamp","TradeID","Symbol","Side","Qty","Price","Note","ExitPrice","ExitQty","Fees","PnL","R","Tags","Audit"])
    _mk("APAC_TradeLog", ["Timestamp","TradeID","Symbol","Side","Qty","Price","Note","ExitPrice","ExitQty","Fees","PnL","R","Tags","Audit"])

    _mk("Config", ["Key", "Value"])
    return created

def snapshot_tab(tab: str) -> str:
    """
    Copy a worksheet to a new sheet named <tab>_snap_YYYYMMDD_HHMM with values only.
    Returns the new title.
    """
    ss = _ss()
    try:
        ws = _with_retries(ss.worksheet, tab)
    except WorksheetNotFound:
        raise RuntimeError(f"Tab '{tab}' not found")

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    new_title = f"{tab}_snap_{ts}"

    new_ws = _with_retries(ss.add_worksheet, title=new_title, rows=ws.row_count, cols=ws.col_count)
    vals = _with_retries(ws.get_all_values)
    if vals:
        _with_retries(new_ws.update, "A1", vals)
    return new_title

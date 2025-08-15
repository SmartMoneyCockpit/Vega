# sheets_client.py — minimal, rate-limit-friendly Google Sheets helper for Vega
#
# Auth sources (priority):
# 1) GOOGLE_SHEETS_CREDENTIALS_JSON -> path to service-account JSON (e.g. /etc/secrets/credentials.json)
# 2) GCP_SERVICE_ACCOUNT_JSON       -> JSON string
# 3) ./Json/credentials.json or ./credentials.json
#
# Sheet ID env keys (first found wins):
#   VEGA_SHEET_ID  | SHEET_ID | GOOGLE_SHEET_ID
#
# Caching:
# - Spreadsheet + Worksheet objects cached with TTL to reduce API calls.
#   Set TTL via VEGA_SHEETS_TTL_SEC (default 300). You can also set SHEETS_TTL_SEC.

from __future__ import annotations

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple, Any

import gspread

# -------------------- config / caches --------------------

_TTL_SEC: float = float(os.getenv("VEGA_SHEETS_TTL_SEC", os.getenv("SHEETS_TTL_SEC", "300")))

# Spreadsheet cache: (spreadsheet, expires_at, sheet_id)
_SS_CACHE: Tuple[Any, float, str] = (None, 0.0, "")

# Worksheet cache per tab name: {tab: (worksheet, expires_at)}
_WS_CACHE: Dict[str, Tuple[Any, float]] = {}

# Remember tabs we’ve already ensured (headers created/merged) this run
_ensured_tabs_runtime = set()

WorksheetNotFound = gspread.exceptions.WorksheetNotFound

# -------------------- helpers --------------------

def _now() -> float:
    return time.time()

def _env_sheet_id() -> str:
    for k in ("VEGA_SHEET_ID", "SHEET_ID", "GOOGLE_SHEET_ID"):
        v = os.getenv(k)
        if v and v.strip():
            return v.strip()
    raise RuntimeError("No Sheet ID. Set VEGA_SHEET_ID (or SHEET_ID / GOOGLE_SHEET_ID) in Render env.")

def _service_account_credentials() -> dict:
    # 1) Path in env
    path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # 2) Raw JSON in env
    blob = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if blob:
        return json.loads(blob)
    # 3) Local fallbacks
    for p in ("Json/credentials.json", "credentials.json"):
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    raise RuntimeError(
        "Google credentials not found. Use Render Secret Files and set "
        "GOOGLE_SHEETS_CREDENTIALS_JSON to the secret file path."
    )

def _gc():
    # gspread Client from credentials dict
    return gspread.service_account_from_dict(_service_account_credentials())

def _with_retries(fn, *args, **kwargs):
    """Small retry helper for transient errors."""
    for i in range(3):
        try:
            return fn(*args, **kwargs)
        except Exception:
            if i == 2:
                raise
            time.sleep(0.5 * (i + 1))  # backoff: 0.5s, 1.0s

def _ss():
    """Get Spreadsheet with TTL cache."""
    global _SS_CACHE
    ss, exp, cached_id = _SS_CACHE
    wanted_id = _env_sheet_id()
    if ss is not None and _now() < exp and cached_id == wanted_id:
        return ss
    # refresh
    client = _gc()
    ss = _with_retries(client.open_by_key, wanted_id)
    _SS_CACHE = (ss, _now() + _TTL_SEC, wanted_id)
    # invalidate worksheet cache (titles may have changed)
    _WS_CACHE.clear()
    return ss

def _ws(tab: str):
    """Get a Worksheet by title with TTL cache."""
    item = _WS_CACHE.get(tab)
    if item and _now() < item[1]:
        return item[0]
    try:
        ws = _with_retries(_ss().worksheet, tab)
    except WorksheetNotFound:
        # Create lazily when writers call ensure_tab/write_range/append_row
        raise
    _WS_CACHE[tab] = (ws, _now() + _TTL_SEC)
    return ws

# -------------------- public API --------------------

def batch_get(ranges: List[str]) -> List[List[List[str]]]:
    """Batch read across tabs; graceful on errors."""
    out: List[List[List[str]]] = []
    for a1 in ranges:
        tab, rng = (a1.split("!", 1) + ["A1:Z2000"])[:2] if "!" in a1 else (a1, "A1:Z2000")
        try:
            ws = _ws(tab)
            vals = _with_retries(ws.get, rng) or []
        except Exception:
            vals = []
        out.append(vals)
    return out

def read_range(a1: str) -> List[List[str]]:
    tab, rng = (a1.split("!", 1) + ["A1:Z2000"])[:2] if "!" in a1 else (a1, "A1:Z2000")
    ws = _ws(tab)
    return _with_retries(ws.get, rng) or []

def write_range(a1: str, rows: List[List]) -> None:
    tab, rng = (a1.split("!", 1) + ["A1"])[:2] if "!" in a1 else (a1, "A1")
    try:
        ws = _ws(tab)
    except WorksheetNotFound:
        ws = _with_retries(_ss().add_worksheet, title=tab, rows=2000, cols=26)
        _WS_CACHE[tab] = (ws, _now() + _TTL_SEC)
    _with_retries(ws.update, rng, rows, value_input_option="USER_ENTERED")

def append_row(tab: str, row: List) -> None:
    try:
        ws = _ws(tab)
    except WorksheetNotFound:
        ws = _with_retries(_ss().add_worksheet, title=tab, rows=2000, cols=26)
        _WS_CACHE[tab] = (ws, _now() + _TTL_SEC)
    clean = [("" if x is None else x) for x in row]
    _with_retries(ws.append_row, clean, value_input_option="USER_ENTERED")

def append_trade_log(row: List, tab_name: str = "NA_TradeLog") -> None:
    append_row(tab_name, row)

def ensure_tab(tab: str, headers: List[str]) -> None:
    """Create the tab if missing; ensure header row contains at least `headers`."""
    key = (tab, tuple(headers))
    if key in _ensured_tabs_runtime:
        return

    ss = _ss()
    try:
        ws = _with_retries(ss.worksheet, tab)
    except WorksheetNotFound:
        ws = _with_retries(ss.add_worksheet, title=tab, rows=2000, cols=26)
        _with_retries(ws.update, "A1", [headers])
        _WS_CACHE[tab] = (ws, _now() + _TTL_SEC)
        _ensured_tabs_runtime.add(key)
        return

    cur = _with_retries(ws.row_values, 1) or []
    if not cur:
        _with_retries(ws.update, "A1", [headers])
        _ensured_tabs_runtime.add(key)
        return

    need, changed = list(cur), False
    for h in headers:
        if h not in need:
            need.append(h)
            changed = True
    if changed:
        _with_retries(ws.update, "A1", [need])

    _ensured_tabs_runtime.add(key)

def read_config() -> List[List[str]]:
    try:
        return read_range("Config!A1:Z999") or []
    except Exception:
        return []

def upsert_config(key: str, value: str) -> None:
    try:
        ws = _ws("Config")
    except WorksheetNotFound:
        ws = _with_retries(_ss().add_worksheet, title="Config", rows=200, cols=5)
        _with_retries(ws.update, "A1", [["Key", "Value"]])
        _WS_CACHE["Config"] = (ws, _now() + _TTL_SEC)

    rows = _with_retries(ws.get_all_values)
    for i, r in enumerate(rows[1:], start=2):
        if r and str(r[0]).strip() == key:
            _with_retries(ws.update, f"A{i}:B{i}", [[key, str(value)]])
            return
    _with_retries(ws.append_row, [key, str(value)], value_input_option="USER_ENTERED")

def bootstrap_sheet() -> List[str]:
    """Create core tabs if missing; return names of tabs that were created."""
    ss = _ss()
    created: List[str] = []

    def _mk(title: str, hdrs: List[str]):
        nonlocal created
        try:
            _with_retries(ss.worksheet, title)
        except WorksheetNotFound:
            ws = _with_retries(ss.add_worksheet, title=title, rows=2000, cols=26)
            _with_retries(ws.update, "A1", [hdrs])
            _WS_CACHE[title] = (ws, _now() + _TTL_SEC)
            created.append(title)

    _mk("NA_Watch",   ["Ticker", "Country", "Strategy", "Entry", "Stop", "Target", "Note", "Status", "Audit"])
    _mk("APAC_Watch", ["Ticker", "Country", "Strategy", "Entry", "Stop", "Target", "Note", "Status", "Audit"])
    _mk("NA_TradeLog",   ["Timestamp", "TradeID", "Symbol", "Side", "Qty", "Price", "Note", "ExitPrice", "ExitQty", "Fees", "PnL", "R", "Tags", "Audit"])
    _mk("APAC_TradeLog", ["Timestamp", "TradeID", "Symbol", "Side", "Qty", "Price", "Note", "ExitPrice", "ExitQty", "Fees", "PnL", "R", "Tags", "Audit"])
    _mk("Config", ["Key", "Value"])
    return created

def snapshot_tab(tab: str) -> str:
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
    _WS_CACHE[new_title] = (new_ws, _now() + _TTL_SEC)
    return new_title

# sheets_client.py — minimal, Render-friendly Google Sheets helpers
# Works with:
#   GOOGLE_SHEETS_CREDENTIALS_JSON = /etc/secrets/credentials.json
#   VEGA_SHEET_ID (or SHEET_ID)    = your spreadsheet id

import os, json, time
from typing import List, Dict, Tuple, Optional

import gspread
from gspread.exceptions import WorksheetNotFound
from google.oauth2.service_account import Credentials

# ---- auth & spreadsheet -----------------------------------------------------

_GC      = None     # gspread client (singleton)
_SPREAD  = None     # gspread Spreadsheet (singleton)
_LAST_OK = 0        # last successful open

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def _load_creds():
    """Create google credentials from a file path or a JSON string."""
    raw = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "").strip() or "/etc/secrets/credentials.json"
    try:
        if os.path.isfile(raw):
            return Credentials.from_service_account_file(raw, scopes=SCOPES)
        # treat as inline JSON
        data = json.loads(raw)
        return Credentials.from_service_account_info(data, scopes=SCOPES)
    except Exception as e:
        raise RuntimeError(f"Google credentials not found/invalid: {e}")

def _client() -> gspread.Client:
    global _GC
    if _GC is None:
        _GC = gspread.authorize(_load_creds())
    return _GC

def _sheet() -> gspread.Spreadsheet:
    """Return spreadsheet handle (reused across calls)."""
    global _SPREAD, _LAST_OK
    sid = os.getenv("VEGA_SHEET_ID") or os.getenv("SHEET_ID")
    if not sid:
        raise RuntimeError("Missing VEGA_SHEET_ID (or SHEET_ID) env var.")
    # reopen occasionally to be safe
    if _SPREAD is None or (time.time() - _LAST_OK) > 300:
        _SPREAD = _client().open_by_key(sid)
        _LAST_OK = time.time()
    return _SPREAD

# ---- worksheet/range helpers ------------------------------------------------

def _split_a1(a1: str) -> Tuple[str, Optional[str]]:
    """Return (tab, range_or_None). Accepts 'Tab', 'Tab!A1:Z', etc."""
    if "!" in a1:
        t, r = a1.split("!", 1)
        return t.strip(), r.strip()
    return a1.strip(), None

def ensure_tab(title: str, headers: List[str]) -> None:
    """Create worksheet if missing; ensure header row exists."""
    ss = _sheet()
    try:
        ws = ss.worksheet(title)
    except WorksheetNotFound:
        ws = ss.add_worksheet(title=title, rows=2000, cols=max(26, len(headers)))
        ws.update("A1", [headers])
        return
    # if existing but no header, set it
    try:
        first = ws.row_values(1)
        if not first:
            ws.update("A1", [headers])
        else:
            # append any missing headers at the end (non-destructive)
            missing = [h for h in headers if h not in first]
            if missing:
                new_hdr = first + missing
                ws.update("A1", [new_hdr])
    except Exception:
        pass

def read_range(a1: str) -> List[List[str]]:
    tab, rng = _split_a1(a1)
    ws = _sheet().worksheet(tab)
    return ws.get(rng) if rng else ws.get_all_values()

def write_range(a1: str, rows: List[List[str]]) -> None:
    tab, rng = _split_a1(a1)
    ws = _sheet().worksheet(tab)
    if not rng:
        # default to start at A1
        rng = f"A1"
    ws.

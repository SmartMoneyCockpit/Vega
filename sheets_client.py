# sheets_client.py — private Google Sheets helpers (service account)
import os, json, time
from typing import List, Optional
import gspread
from google.auth.exceptions import GoogleAuthError
from gspread.exceptions import APIError

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID") or os.environ.get("SHEET_ID") or ""
LOG_TAB  = os.environ.get("GOOGLE_SHEET_LOG_TAB", os.environ.get("GOOGLE_SHEET_MAIN_TAB", "TradeLog"))
WATCH_TAB= os.environ.get("GOOGLE_SHEET_WATCHLIST_TAB", os.environ.get("GOOGLE_SHEET_MAIN_TAB", "Watch List"))

# Optional gid envs (faster & exact). If present, we use them.
LOG_GID   = os.environ.get("LOG_GID")    # e.g., "2033714676"
WATCH_GID = os.environ.get("WATCH_GID")  # optional

# ---- Core auth ----
def _gc():
    try:
        raw = os.environ["GCP_SERVICE_ACCOUNT_JSON"]
        creds = json.loads(raw)
        return gspread.service_account_from_dict(creds)
    except KeyError:
        raise RuntimeError("Missing GCP_SERVICE_ACCOUNT_JSON env")
    except (json.JSONDecodeError, GoogleAuthError) as e:
        raise RuntimeError(f"Service account auth failed: {e}")

def _open():
    if not SHEET_ID:
        raise RuntimeError("Missing GOOGLE_SHEET_ID")
    return _gc().open_by_key(SHEET_ID)

# ---- Worksheet getters (by gid preferred, else by name) ----
def _get_ws_by_gid_or_name(sh: gspread.Spreadsheet, gid: Optional[str], name: str):
    if gid:
        ws = sh.get_worksheet_by_id(int(gid))
        if ws is None:
            raise RuntimeError(f"Worksheet gid {gid} not found (tab='{name}').")
        return ws
    return sh.worksheet(name)

def get_sheet(sheet_id: str, tab_name: str):
    """Back-compat signature used in app.py. Ignores passed sheet_id for simplicity."""
    sh = _open()
    # If called for LOG_TAB or WATCH_TAB, use gid if available
    if tab_name == LOG_TAB and LOG_GID:
        return _get_ws_by_gid_or_name(sh, LOG_GID, LOG_TAB)
    if tab_name == WATCH_TAB and WATCH_GID:
        return _get_ws_by_gid_or_name(sh, WATCH_GID, WATCH_TAB)
    return sh.worksheet(tab_name)

# ---- Read range (A1 notation) ----
def read_range(sheet_id: str, a1_range: str) -> List[List[str]]:
    """Returns list-of-lists (may be empty)."""
    sh = _open()
    # If range includes a sheet name, gspread handles it. Otherwise, default to first sheet.
    try:
        return sh.values_get(a1_range).get("values", [])
    except APIError:
        # Fallback: try via active worksheet when range lacks sheet name
        ws = sh.sheet1
        return ws.get(a1_range) or []

# ---- Append row ----
def append_row(sheet_id: str, tab_name: str, row_values: List[str], retries: int = 2, delay_sec: float = 0.4):
    """Append a row to the given tab (name). Retries lightly on transient API errors."""
    sh = _open()
    ws = None
    # Prefer gid for known tabs
    if tab_name == LOG_TAB and LOG_GID:
        ws = _get_ws_by_gid_or_name(sh, LOG_GID, LOG_TAB)
    elif tab_name == WATCH_TAB and WATCH_GID:
        ws = _get_ws_by_gid_or_name(sh, WATCH_GID, WATCH_TAB)
    else:
        ws = sh.worksheet(tab_name)

    attempt = 0
    while True:
        try:
            ws.append_row(row_values, value_input_option="USER_ENTERED")
            return True
        except APIError as e:
            attempt += 1
            if attempt > retries:
                raise RuntimeError(f"Append failed after retries: {e}")
            time.sleep(delay_sec)

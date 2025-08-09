# sheets_client.py — compact Google Sheets helpers (with bulk write)
import os, json, time
from typing import List, Optional
import gspread
from gspread.exceptions import APIError
from google.auth.exceptions import GoogleAuthError

SHEET_ID  = os.getenv("GOOGLE_SHEET_ID") or os.getenv("SHEET_ID") or ""
LOG_TAB   = os.getenv("GOOGLE_SHEET_LOG_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "TradeLog"))
WATCH_TAB = os.getenv("GOOGLE_SHEET_WATCHLIST_TAB", os.getenv("GOOGLE_SHEET_MAIN_TAB", "Watch List"))
LOG_GID   = os.getenv("LOG_GID"); WATCH_GID = os.getenv("WATCH_GID")

def _gc():
    try: return gspread.service_account_from_dict(json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"]))
    except KeyError: raise RuntimeError("Missing GCP_SERVICE_ACCOUNT_JSON")
    except (json.JSONDecodeError, GoogleAuthError) as e: raise RuntimeError(f"Service account auth failed: {e}")

def _open():
    if not SHEET_ID: raise RuntimeError("Missing GOOGLE_SHEET_ID")
    return _gc().open_by_key(SHEET_ID)

def _by_gid_or_name(sh, gid: Optional[str], name: str):
    if gid:
        ws = sh.get_worksheet_by_id(int(gid))
        if ws is None: raise RuntimeError(f"Worksheet gid {gid} not found ({name})")
        return ws
    return sh.worksheet(name)

def get_sheet(sheet_id: str, tab_name: str):
    sh = _open()
    if tab_name == LOG_TAB and LOG_GID: return _by_gid_or_name(sh, LOG_GID, LOG_TAB)
    if tab_name == WATCH_TAB and WATCH_GID: return _by_gid_or_name(sh, WATCH_GID, WATCH_TAB)
    return sh.worksheet(tab_name)

def read_range(sheet_id: str, a1_range: str) -> List[List[str]]:
    sh = _open()
    try: return sh.values_get(a1_range).get("values", [])
    except APIError: return (sh.sheet1.get(a1_range) or [])

def append_row(sheet_id: str, tab_name: str, row_values: List[str], retries=2, delay_sec=0.4):
    sh = _open()
    ws = (_by_gid_or_name(sh, LOG_GID, LOG_TAB) if tab_name==LOG_TAB and LOG_GID
          else _by_gid_or_name(sh, WATCH_GID, WATCH_TAB) if tab_name==WATCH_TAB and WATCH_GID
          else sh.worksheet(tab_name))
    for a in range(retries+1):
        try: ws.append_row(row_values, value_input_option="USER_ENTERED"); return True
        except APIError as e:
            if a>=retries: raise RuntimeError(f"Append failed after retries: {e}")
            time.sleep(delay_sec)

# NEW: bulk write/replace a range (e.g., watchlist import)
def write_range(tab_name: str, start_a1: str, values: List[List[str]]):
    sh = _open()
    ws = (_by_gid_or_name(sh, WATCH_GID, WATCH_TAB) if tab_name==WATCH_TAB and WATCH_GID else sh.worksheet(tab_name))
    if not values: return False
    ws.update(start_a1, values, value_input_option="USER_ENTERED")
    return True

def clear_range(tab_name: str, a1: str):
    sh = _open()
    ws = (_by_gid_or_name(sh, WATCH_GID, WATCH_TAB) if tab_name==WATCH_TAB and WATCH_GID else sh.worksheet(tab_name))
    ws.batch_clear([a1])
    return True

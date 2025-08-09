# config_client.py — tiny settings store in Google Sheets (Config tab)
import os, gspread, json, time
from typing import Dict, Optional
from gspread.exceptions import APIError
from google.auth.exceptions import GoogleAuthError

SHEET_ID   = os.getenv("GOOGLE_SHEET_ID") or os.getenv("SHEET_ID") or ""
CONFIG_TAB = os.getenv("GOOGLE_SHEET_CONFIG_TAB", "Config")
CONFIG_GID = os.getenv("CONFIG_GID")  # optional gid for Config tab

def _gc():
    try:
        return gspread.service_account_from_dict(json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"]))
    except KeyError:
        raise RuntimeError("Missing GCP_SERVICE_ACCOUNT_JSON")
    except (json.JSONDecodeError, GoogleAuthError) as e:
        raise RuntimeError(f"Service account auth failed: {e}")

def _open():
    if not SHEET_ID: raise RuntimeError("Missing GOOGLE_SHEET_ID")
    return _gc().open_by_key(SHEET_ID)

def _get_config_ws():
    sh = _open()
    if CONFIG_GID:
        ws = sh.get_worksheet_by_id(int(CONFIG_GID))
        if ws is None: raise RuntimeError(f"Config gid {CONFIG_GID} not found")
        return ws
    # Create if missing
    try:
        return sh.worksheet(CONFIG_TAB)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=CONFIG_TAB, rows=50, cols=3)

HEADERS = ["Key", "Value", "UpdatedAt"]

def _ensure_headers(ws):
    row = ws.get("A1:C1") or []
    cur = [c.strip() for c in (row[0] if row else [])]
    if cur != HEADERS:
        ws.update("A1", [HEADERS])

def get_config_dict() -> Dict[str, str]:
    ws = _get_config_ws(); _ensure_headers(ws)
    vals = ws.get("A2:C200") or []
    out = {}
    for r in vals:
        if len(r) >= 2 and r[0].strip():
            out[r[0].strip()] = r[1].strip() if len(r) > 1 else ""
    return out

def set_config_value(key: str, value: str):
    ws = _get_config_ws(); _ensure_headers(ws)
    vals = ws.get("A2:C200") or []
    now = time.strftime("%Y-%m-%d %H:%M:%S UTC")
    # find existing
    row_idx = None
    for i, r in enumerate(vals, start=2):
        if (r[0].strip() if len(r) else "") == key:
            row_idx = i; break
    if row_idx:
        ws.update(f"A{row_idx}:C{row_idx}", [[key, value, now]])
    else:
        ws.append_row([key, value, now], value_input_option="USER_ENTERED")

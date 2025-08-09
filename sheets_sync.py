# sheets_sync.py — minimal Google Sheets appender with service account
import os, json, gspread
from google.oauth2.service_account import Credentials
from typing import Dict, Any
SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
def _load_credentials():
    sa_path = os.getenv("GOOGLE_SA_PATH"); sa_json = os.getenv("GOOGLE_SA_JSON")
    if sa_path and os.path.exists(sa_path): return Credentials.from_service_account_file(sa_path, scopes=SCOPES)
    if sa_json: return Credentials.from_service_account_info(json.loads(sa_json), scopes=SCOPES)
    raise RuntimeError("Google SA credentials not provided. Set GOOGLE_SA_PATH or GOOGLE_SA_JSON.")
def _client(): return gspread.authorize(_load_credentials())
def _ensure_ws(sh, title): 
    try: return sh.worksheet(title)
    except gspread.WorksheetNotFound: return sh.add_worksheet(title=title, rows=100, cols=20)
def append_row(spreadsheet_id: str, ws_title: str, record: Dict[str, Any]):
    if not spreadsheet_id: raise RuntimeError("Missing SHEETS_SPREADSHEET_ID")
    sh = _client().open_by_key(spreadsheet_id); ws = _ensure_ws(sh, ws_title)
    if len(ws.get_all_values()) == 0: ws.append_row(list(record.keys()))
    ws.append_row([record.get(k, "") for k in record.keys()])

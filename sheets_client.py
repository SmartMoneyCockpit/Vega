
from typing import List, Optional
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def _client():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return gspread.authorize(creds)

def get_sheet(sheet_id: str, worksheet_title: Optional[str] = None):
    gc = _client()
    sh = gc.open_by_key(sheet_id)
    if worksheet_title:
        return sh.worksheet(worksheet_title)
    return sh.sheet1

def read_range(sheet_id: str, a1_range: str):
    gc = _client()
    sh = gc.open_by_key(sheet_id)
    try:
        return sh.values_get(a1_range).get("values", [])
    except Exception:
        ws_name, rng = a1_range.split("!", 1)
        ws = sh.worksheet(ws_name)
        return ws.get(rng) or []

def append_row(sheet_id: str, worksheet_title: str, row: List[str]):
    ws = get_sheet(sheet_id, worksheet_title)
    ws.append_row(row)

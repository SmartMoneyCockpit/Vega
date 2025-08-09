
from typing import List, Optional
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

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
        try:
            if "!" in a1_range:
                ws_name, rng = a1_range.split("!", 1)
                ws = sh.worksheet(ws_name)
                return ws.get(rng) or []
            else:
                ws = sh.worksheet(a1_range)
                return ws.get_all_values()
        except Exception:
            return []

def append_row(sheet_id: str, worksheet_title: str, row: List[str]):
    try:
        ws = get_sheet(sheet_id, worksheet_title)
        ws.append_row(row)
    except APIError:
        gc = _client()
        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet(worksheet_title)
        ws.append_row(row)

"""
sheets_client.py — minimal Google Sheets helper for Vega.

Auth sources (priority):
1) GOOGLE_SHEETS_CREDENTIALS_JSON -> path to service-account JSON (e.g. /etc/secrets/credentials.json)
2) GCP_SERVICE_ACCOUNT_JSON -> JSON string
3) ./Json/credentials.json or ./credentials.json

Sheet ID env: VEGA_SHEET_ID (or SHEET_ID / GOOGLE_SHEET_ID)
"""

from __future__ import annotations
import os, json
from datetime import datetime
from typing import List, Dict, Tuple
import gspread

def _env_sheet_id() -> str:
    for k in ("VEGA_SHEET_ID", "SHEET_ID", "GOOGLE_SHEET_ID"):
        v = os.getenv(k)
        if v and v.strip(): return v.strip()
    raise RuntimeError("No Sheet ID. Set VEGA_SHEET_ID (or SHEET_ID / GOOGLE_SHEET_ID) in Render env.")

def _service_account_credentials() -> dict:
    path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if path and os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f: return json.load(f)
    blob = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if blob: return json.loads(blob)
    for p in ("Json/credentials.json","credentials.json"):
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: return json.load(f)
    raise RuntimeError("Google credentials not found. Use Render Secret Files and set GOOGLE_SHEETS_CREDENTIALS_JSON to the path.")

def _gc(): return gspread.service_account_from_dict(_service_account_credentials())
def _ss(): return _gc().open_by_key(_env_sheet_id())

def batch_get(ranges: List[str]) -> List[List[List[str]]]:
    ss = _ss(); out=[]
    for r in ranges:
        try:
            vals = ss.values_get(r).get("values", [])
        except Exception:
            vals = []
        out.append(vals)
    return out

def read_range(a1: str) -> List[List[str]]:
    if "!" in a1: tab, rng = a1.split("!",1)
    else: tab, rng = a1, "A1:Z2000"
    ws = _ss().worksheet(tab)
    return ws.get(rng) or []

def write_range(a1: str, rows: List[List]) -> None:
    if "!" in a1: tab, rng = a1.split("!",1)
    else: tab, rng = a1, "A1"
    try: ws = _ss().worksheet(tab)
    except gspread.exceptions.WorksheetNotFound:
        ws = _ss().add_worksheet(title=tab, rows=2000, cols=26)
    ws.update(rng, rows, value_input_option="USER_ENTERED")

def append_row(tab: str, row: List) -> None:
    ss = _ss()
    try: ws = ss.worksheet(tab)
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=tab, rows=2000, cols=26)
    ws.append_row([("" if x is None else x) for x in row], value_input_option="USER_ENTERED")

def append_trade_log(row: List, tab_name: str="NA_TradeLog") -> None:
    append_row(tab_name, row)

def ensure_tab(tab: str, headers: List[str]) -> None:
    ss = _ss()
    try: ws = ss.worksheet(tab)
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=tab, rows=2000, cols=26)
        ws.update("A1", [headers]); return
    cur = ws.row_values(1) or []
    if not cur:
        ws.update("A1", [headers]); return
    need = list(cur); changed=False
    for h in headers:
        if h not in need:
            need.append(h); changed=True
    if changed: ws.update("A1",[need])

def read_config() -> List[List[str]]:
    try:
        return _ss().worksheet("Config").get("A1:Z999") or []
    except gspread.exceptions.WorksheetNotFound:
        return []

def upsert_config(key: str, value: str) -> None:
    ss = _ss()
    try: ws = ss.worksheet("Config")
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title="Config", rows=200, cols=5)
        ws.update("A1", [["Key","Value"]])
    rows = ws.get_all_values()
    for i, r in enumerate(rows[1:], start=2):
        if r and str(r[0]).strip()==key:
            ws.update(f"A{i}:B{i}", [[key, str(value)]]); return
    ws.append_row([key, str(value)], value_input_option="USER_ENTERED")

def bootstrap_sheet() -> List[str]:
    ss = _ss(); created=[]
    def _mk(title, hdrs):
        nonlocal created
        try: ss.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            ws = ss.add_worksheet(title=title, rows=2000, cols=26)
            ws.update("A1", [hdrs]); created.append(title)
    _mk("NA_Watch",  ["Ticker","Country","Strategy","Entry","Stop","Target","Note","Status","Audit"])
    _mk("APAC_Watch",["Ticker","Country","Strategy","Entry","Stop","Target","Note","Status","Audit"])
    _mk("NA_TradeLog",   ["Timestamp","TradeID","Symbol","Side","Qty","Price","Note","ExitPrice","ExitQty","Fees","PnL","R","Tags","Audit"])
    _mk("APAC_TradeLog", ["Timestamp","TradeID","Symbol","Side","Qty","Price","Note","ExitPrice","ExitQty","Fees","PnL","R","Tags","Audit"])
    _mk("Config", ["Key","Value"])
    return created

def snapshot_tab(tab: str) -> str:
    ss = _ss()
    try: ws = ss.worksheet(tab)
    except gspread.exceptions.WorksheetNotFound:
        raise RuntimeError(f"Tab '{tab}' not found")
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    new_title = f"{tab}_snap_{ts}"
    new_ws = ss.add_worksheet(title=new_title, rows=ws.row_count, cols=ws.col_count)
    vals = ws.get_all_values()
    if vals: new_ws.update("A1", vals)
    return new_title

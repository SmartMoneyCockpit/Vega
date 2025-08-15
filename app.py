# sheets_client.py — Render-friendly helpers for Google Sheets
# Requires:
#   GOOGLE_SHEETS_CREDENTIALS_JSON=/etc/secrets/credentials.json  (or inline JSON)
#   VEGA_SHEET_ID (fallback: SHEET_ID) = spreadsheet id

from __future__ import annotations
import os, json, time
from typing import List, Dict, Tuple, Optional

import gspread
from gspread.exceptions import WorksheetNotFound
from google.oauth2.service_account import Credentials

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_GC: Optional[gspread.Client] = None
_SPREAD: Optional[gspread.Spreadsheet] = None
_LAST_OPEN = 0.0

# ---------- auth & spreadsheet ----------

def _load_creds() -> Credentials:
    path_or_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "").strip()
    if not path_or_json:
        path_or_json = "/etc/secrets/credentials.json"
    try:
        if os.path.isfile(path_or_json):
            return Credentials.from_service_account_file(path_or_json, scopes=_SCOPES)
        data = json.loads(path_or_json)
        return Credentials.from_service_account_info(data, scopes=_SCOPES)
    except Exception as e:
        raise RuntimeError(f"Invalid Google creds: {e}")

def _client() -> gspread.Client:
    global _GC
    if _GC is None:
        _GC = gspread.authorize(_load_creds())
    return _GC

def _sheet() -> gspread.Spreadsheet:
    """Open spreadsheet by id; reuse handle; refresh every 5 min."""
    global _SPREAD, _LAST_OPEN
    sid = os.getenv("VEGA_SHEET_ID") or os.getenv("SHEET_ID")
    if not sid:
        raise RuntimeError("Missing VEGA_SHEET_ID (or SHEET_ID).")
    if _SPREAD is None or (time.time() - _LAST_OPEN) > 300:
        _SPREAD = _client().open_by_key(sid)
        _LAST_OPEN = time.time()
    return _SPREAD

# ---------- A1 helpers ----------

def _split_a1(a1: str) -> Tuple[str, Optional[str]]:
    if "!" in a1:
        t, r = a1.split("!", 1)
        return t.strip(), r.strip()
    return a1.strip(), None

# ---------- basic ops ----------

def read_range(a1: str) -> List[List[str]]:
    tab, rng = _split_a1(a1)
    ws = _sheet().worksheet(tab)
    return ws.get(rng) if rng else ws.get_all_values()

def write_range(a1: str, rows: List[List[str]]) -> None:
    tab, rng = _split_a1(a1)
    ws = _sheet().worksheet(tab)
    if not rng:
        rng = "A1"
    ws.update(rng, rows, value_input_option="USER_ENTERED")

def batch_get(ranges: List[str]) -> List[List[List[str]]]:
    return _sheet().batch_get(ranges)

def append_row(tab: str, row: List) -> None:
    ws = _sheet().worksheet(tab)
    ws.append_row(list(row), value_input_option="USER_ENTERED")

# ---------- app-specific helpers ----------

def ensure_tab(title: str, headers: List[str]) -> None:
    ss = _sheet()
    try:
        ws = ss.worksheet(title)
    except WorksheetNotFound:
        ws = ss.add_worksheet(title=title, rows=2000, cols=max(26, len(headers)))
        ws.update("A1", [headers])
        return

    # ensure header row has at least the expected headers
    try:
        first = ws.row_values(1)
        if not first:
            ws.update("A1", [headers])
        else:
            missing = [h for h in headers if h not in first]
            if missing:
                new_hdr = first + missing
                ws.update("A1", [new_hdr])
    except Exception:
        pass

def read_config(max_rows: int = 500) -> List[List[str]]:
    try:
        return read_range(f"Config!A1:Z{max_rows}")
    except Exception:
        return []

def append_trade_log(row: List, tab_name: str = "NA_TradeLog") -> None:
    append_row(tab_name, row)

def upsert_config(kv: Dict[str, str]) -> None:
    ensure_tab("Config", ["Key", "Value"])
    ws = _sheet().worksheet("Config")
    try:
        rows = ws.get_all_values()
    except Exception:
        rows = []
    cur = {}
    for r in rows[1:]:
        if not r:
            continue
        k = (r[0] or "").strip()
        v = (r[1] or "").strip() if len(r) > 1 else ""
        if k:
            cur[k] = v

    # naive update/append (Config is small)
    col1 = ws.col_values(1)
    for k, v in kv.items():
        if k in cur:
            try:
                idx = [i for i, x in enumerate(col1, start=1) if x == k][0]
                ws.update(f"B{idx}", [[str(v)]], value_input_option="USER_ENTERED")
            except Exception:
                ws.append_row([k, v], value_input_option="USER_ENTERED")
        else:
            ws.append_row([k, v], value_input_option="USER_ENTERED")

def snapshot_tab(tab: str) -> str:
    data = read_range(f"{tab}!A1:Z5000") or []
    snap = f"{tab}_snap_{time.strftime('%Y%m%d_%H%M')}"[:95]
    ensure_tab(snap, data[0] if data else ["A"])
    if data:
        write_range(f"{snap}!A1", data)
    return snap

def bootstrap_sheet() -> str:
    core = {
        "NA_Watch":      ["Ticker","Country","Strategy","Entry","Stop","Target","Note","Status","Audit"],
        "NA_TradeLog":   ["Timestamp","TradeID","Symbol","Side","Qty","Price","Note","ExitPrice","ExitQty","Fees","PnL","R","Tags","Audit"],
        "APAC_Watch":    ["Ticker","Country","Strategy","Entry","Stop","Target","Note","Status","Audit"],
        "APAC_TradeLog": ["Timestamp","TradeID","Symbol","Side","Qty","Price","Note","ExitPrice","ExitQty","Fees","PnL","R","Tags","Audit"],
        "Fee_Presets":   ["Preset","Markets","Base","BpsBuy","BpsSell","TaxBps","Notes"],
        "Earnings":      ["Timestamp","Ticker","NextEarnings"],
        "News_Daily":    ["Date","Region","Country","Source","Title","URL","Tickers","Notes"],
        "News_Archive":  ["Timestamp","Region","Country","Title","URL"],
        "Health_Log":    ["Timestamp","Mood","SleepHrs","Stress(1-10)","ExerciseMin","Notes"],
        "Config":        ["Key","Value"],
    }
    for t, hdr in core.items():
        ensure_tab(t, hdr)
    return "ok"

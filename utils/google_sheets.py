import os, json, datetime
import gspread
import pandas as pd

SHEET_ID = os.environ["SHEET_ID"]
LOG_GID  = int(os.getenv("LOG_GID", "0"))
LOG_TAB  = os.getenv("LOG_TAB", "TradeLog")

# Edit these if you prefer different columns (order matters)
HEADERS = ["Timestamp", "Type", "Symbol", "Status", "Notes"]

def _gc():
    creds = json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"])
    return gspread.service_account_from_dict(creds)

def _ws():
    gc = _gc()
    sh = gc.open_by_key(SHEET_ID)
    return sh.get_worksheet_by_id(LOG_GID) if LOG_GID else sh.worksheet(LOG_TAB)

def _ensure_headers(ws):
    vals = ws.get_all_values()
    if not vals:
        ws.insert_row(HEADERS, 1)
        return
    first = [c.strip() for c in vals[0]]
    if first != HEADERS:
        # reset row 1 to the canonical headers
        ws.delete_rows(1)
        ws.insert_row(HEADERS, 1)

def fetch_tradelog_last_n(n=10) -> pd.DataFrame:
    ws = _ws()
    _ensure_headers(ws)
    rows = ws.get_all_values()
    if len(rows) <= 1:
        return pd.DataFrame(columns=HEADERS)

    header = rows[0]
    data_rows = rows[1:]

    # Normalize row lengths to header length
    norm = []
    for r in data_rows:
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        elif len(r) > len(header):
            r = r[:len(header)]
        norm.append(r)

    df = pd.DataFrame(norm, columns=header)
    return df.tail(n)

def append_tradelog_row(entry: dict):
    """
    Minimal append used by your 'Quick Log' form.
    Accepts keys: Type, Symbol, Status, Notes
    """
    ws = _ws()
    _ensure_headers(ws)
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    row = {
        "Timestamp": now,
        "Type":   entry.get("Type", "Journal"),
        "Symbol": entry.get("Symbol", ""),
        "Status": entry.get("Status", "Open"),
        "Notes":  entry.get("Notes", ""),
    }

    ws.append_row([row[h] for h in HEADERS], value_input_option="USER_ENTERED")

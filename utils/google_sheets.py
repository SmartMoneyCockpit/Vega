import os
import json
import gspread
import pandas as pd

SHEET_ID = os.environ["SHEET_ID"]  # 1Nv77X...AhE
LOG_GID = os.getenv("LOG_GID")     # Optional: '2033714676'
LOG_TAB = os.getenv("LOG_TAB", "TradeLog")  # fallback to name if gid missing

def _gc():
    """Authenticate to Google Sheets via service account JSON in env."""
    creds = json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"])
    return gspread.service_account_from_dict(creds)

def fetch_tradelog_last_n(n=10) -> pd.DataFrame:
    """Fetch last n rows from the TradeLog sheet privately."""
    gc = _gc()
    sh = gc.open_by_key(SHEET_ID)

    if LOG_GID:
        try:
            ws = sh.get_worksheet_by_id(int(LOG_GID))
        except Exception as e:
            raise RuntimeError(f"Worksheet with gid {LOG_GID} not found: {e}")
    else:
        ws = sh.worksheet(LOG_TAB)

    rows = ws.get_all_values()
    if not rows:
        return pd.DataFrame()

    header, data = rows[0], rows[1:]
    return pd.DataFrame(data, columns=header).tail(n)

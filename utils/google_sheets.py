"""
Utility functions for connecting to and interacting with Google Sheets.

This module uses the `gspread` library to authenticate via a service account and
read/write data to a Google Sheet named `COCKPIT`.  If credentials are not
provided or authentication fails, the functions operate in offline mode by
reading from and writing to CSV files in the `data/` directory.
"""

import os
from pathlib import Path
from typing import List, Optional

import pandas as pd

try:
    import gspread  # type: ignore
    from oauth2client.service_account import ServiceAccountCredentials  # type: ignore
except ImportError:
    gspread = None  # type: ignore
    ServiceAccountCredentials = None  # type: ignore


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def _authenticate(credentials_path: Optional[str] = None):
    """Return an authenticated gspread client or `None` if authentication fails.

    Parameters
    ----------
    credentials_path : str, optional
        Path to the service account JSON file.  If `None`, the function looks
        for a file named `credentials.json` in the project root or uses the
        `GOOGLE_APPLICATION_CREDENTIALS` environment variable.
    """
    if gspread is None or ServiceAccountCredentials is None:
        return None
    try:
        if credentials_path is None:
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path is None:
            # Fallback to local credentials.json in project root
            local_path = Path(__file__).resolve().parent.parent / "credentials.json"
            if local_path.exists():
                credentials_path = str(local_path)
        if credentials_path is None:
            return None
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scopes)
        client = gspread.authorize(creds)
        return client
    except Exception:
        return None


def get_sheet(sheet_name: str = "COCKPIT", worksheet_name: str = "Sheet1", credentials_path: Optional[str] = None):
    """Return a gspread worksheet object if possible, otherwise `None`.

    If authentication fails or gspread is not installed, the function returns
    `None`.  Callers should handle the `None` case by falling back to local
    storage.
    """
    client = _authenticate(credentials_path)
    if client is None:
        return None
    try:
        sh = client.open(sheet_name)
        worksheet = sh.worksheet(worksheet_name)
        return worksheet
    except Exception:
        return None


def read_sheet(sheet_name: str = "COCKPIT", worksheet_name: str = "Sheet1", credentials_path: Optional[str] = None) -> pd.DataFrame:
    """Read a Google Sheet into a pandas DataFrame.

    If the sheet cannot be read, an empty DataFrame is returned instead.  In
    offline mode, the function attempts to read from a CSV file in the `data/`
    directory (e.g. `COCKPIT_Sheet1.csv`).
    """
    worksheet = get_sheet(sheet_name, worksheet_name, credentials_path)
    if worksheet is not None:
        try:
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception:
            pass
    # Offline fallback
    csv_path = DATA_DIR / f"{sheet_name}_{worksheet_name}.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return pd.DataFrame()


def append_row(row: List, sheet_name: str = "COCKPIT", worksheet_name: str = "Sheet1", credentials_path: Optional[str] = None) -> None:
    """Append a row to the specified Google Sheet.  If offline, append to CSV.
    """
    worksheet = get_sheet(sheet_name, worksheet_name, credentials_path)
    if worksheet is not None:
        try:
            worksheet.append_row(row)
            return
        except Exception:
            pass
    # Offline fallback
    csv_path = DATA_DIR / f"{sheet_name}_{worksheet_name}.csv"
    if not csv_path.exists():
        # Create file and write header if necessary
        df = pd.DataFrame([row])
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)
        df.loc[len(df)] = row
        df.to_csv(csv_path, index=False)
        df.to_csv(csv_path, index=False)

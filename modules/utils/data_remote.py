import os
from pathlib import Path
from typing import Optional
import pandas as pd
import requests

REPO_SLUG = os.getenv("VEGA_REPO", "")
DATA_BRANCH = os.getenv("VEGA_DATA_BRANCH", "")

def load_csv_auto(path: str) -> pd.DataFrame:
    """Load CSV from local path; if missing and env vars provided, try GitHub raw."""
    p = Path(path)
    if p.exists():
        try:
            return pd.read_csv(p)
        except Exception:
            pass
    if REPO_SLUG and DATA_BRANCH:
        url = f"https://raw.githubusercontent.com/{REPO_SLUG}/{DATA_BRANCH}/{path}"
        try:
            return pd.read_csv(url)
        except Exception:
            pass
    return pd.DataFrame()

def github_last_modified(path: str) -> Optional[str]:
    if not (REPO_SLUG and DATA_BRANCH): return None
    url = f"https://raw.githubusercontent.com/{REPO_SLUG}/{DATA_BRANCH}/{path}"
    try:
        r = requests.head(url, timeout=10)
        if r.ok:
            return r.headers.get("Last-Modified")
    except Exception:
        return None
    return None

def raw_url(path: str) -> Optional[str]:
    if not (REPO_SLUG and DATA_BRANCH): return None
    return f"https://raw.githubusercontent.com/{REPO_SLUG}/{DATA_BRANCH}/{path}"

def github_page_url(path: str) -> Optional[str]:
    if not (REPO_SLUG and DATA_BRANCH): return None
    return f"https://github.com/{REPO_SLUG}/blob/{DATA_BRANCH}/{path}"

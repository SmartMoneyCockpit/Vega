import os, pandas as pd
from pathlib import Path
import requests
REPO=os.getenv('VEGA_REPO',''); BR=os.getenv('VEGA_DATA_BRANCH','')
def load_csv_auto(p):
    P=Path(p)
    if P.exists():
        try: return pd.read_csv(P)
        except Exception: pass
    if REPO and BR:
        url=f'https://raw.githubusercontent.com/{REPO}/{BR}/{p}'
        try: return pd.read_csv(url)
        except Exception: pass
    return pd.DataFrame()
def raw_url(p):
    return f'https://raw.githubusercontent.com/{REPO}/{BR}/{p}' if REPO and BR else None
def github_page_url(p):
    return f'https://github.com/{REPO}/blob/{BR}/{p}' if REPO and BR else None

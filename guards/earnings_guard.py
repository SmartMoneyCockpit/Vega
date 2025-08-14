
"""
Earnings window guard for Vega orders.
Blocks new buys if earnings are within 30 days (user rule).

Requires POLYGON_API_KEY (or implement your own provider).
This module is safe to import even without a key (it will just return "unknown" and allow UI to warn).
"""
import os, datetime as dt, json, time
from typing import Optional

import requests

POLYGON_KEY = os.getenv("POLYGON_API_KEY")

def _polygon_earnings_date(ticker: str) -> Optional[str]:
    if not POLYGON_KEY:
        return None
    url = f"https://api.polygon.io/vX/reference/financials?ticker={ticker}&limit=1&apiKey={POLYGON_KEY}"
    try:
        r = requests.get(url, timeout=6)
        if r.status_code != 200:
            return None
        data = r.json()
        # Fallback: try corporate actions/earnings calendar if vX not available
        dt_str = None
        # This is a placeholder: adapt to your active Polygon endpoint for earnings calendar
        if isinstance(data, dict) and "results" in data and data["results"]:
            # Not exact earnings time; adapt as needed
            dt_str = data["results"][0].get("fiscal_period_end_date") or data["results"][0].get("start_date")
        return dt_str
    except Exception:
        return None

def days_to_earnings(ticker: str) -> Optional[int]:
    d = _polygon_earnings_date(ticker)
    if not d:
        return None
    try:
        when = dt.datetime.fromisoformat(d.split("T")[0])
        return (when.date() - dt.date.today()).days
    except Exception:
        return None

def is_blocked(ticker: str, min_days: int = 30) -> bool:
    dte = days_to_earnings(ticker)
    if dte is None:
        # Unknown: don't block hard, but the UI can warn.
        return False
    return dte < min_days

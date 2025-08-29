# utils/__init__.py  — re-exports + time helpers so imports like `from utils import now_pt` work

from __future__ import annotations
import os
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None  # CI fallback; not expected on 3.11

# ---- Preferred timezone for cockpit ----
TZ_NAME = os.getenv("VEGA_TZ", "America/Los_Angeles")

def _zone():
    if ZoneInfo is None:
        return timezone.utc
    try:
        return ZoneInfo(TZ_NAME)
    except Exception:
        return ZoneInfo("America/Los_Angeles") if ZoneInfo else timezone.utc

# ---- Time helpers (kept very small to avoid deps) ----
def now_pt() -> datetime:
    """Current time in Pacific Time (or VEGA_TZ if set)."""
    return datetime.now(_zone())

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def now_utc_iso() -> str:
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")

# Optional short alias some modules use
def now() -> str:
    """Human string in local cockpit TZ."""
    return now_pt().strftime("%Y-%m-%d %H:%M:%S")

# ---- (Optional) other utilities can be re-exported here to keep `from utils import X` working ----
# from .deps_check import show_missing  # uncomment if you want this old import path to keep working
# from .something_else import some_fn
def put_row_prev_close(*args, **kwargs):
    """Stub: placeholder until full logic is implemented."""
    return None
def last_price(symbol: str, default: float = 0.0):
    """Stub: return a safe default last price (override later with real data)."""
    try:
        # if you later wire real feeds, you can look them up here
        return float(default)
    except Exception:
        return 0.0

def get_ea(symbol: str):
    """Stub: 'get earnings announcement' date; empty string means unknown."""
    return ""

# utils/__init__.py
# small helpers re-exported; lets helpers be imported like "from utils import now_utc"

from __future__ import annotations
import os
from datetime import datetime, timezone, timedelta

try:
    from zoneinfo import ZoneInfo   # Python 3.9+
except Exception:
    from backports.zoneinfo import ZoneInfo  # type: ignore

# ----------------------------------------------------------------------
# Default timezone handling
# ----------------------------------------------------------------------
TZ_NAME = os.getenv("VEGA_TZ", "America/Los_Angeles")

def _tzinfo() -> ZoneInfo:
    try:
        return ZoneInfo(TZ_NAME)
    except Exception:
        return ZoneInfo("America/Los_Angeles") if ZoneInfo else timezone.utc

# ----------------------------------------------------------------------
# Time helpers
# ----------------------------------------------------------------------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def now_utc_str() -> str:
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")

def now_local() -> datetime:
    return datetime.now(_tzinfo())

def now_local_str() -> str:
    return now_local().strftime("%Y-%m-%d %H:%M:%S")

# ----------------------------------------------------------------------
# North America cash-session window helper
# ----------------------------------------------------------------------
WEEKDAYS_NA = {0, 1, 2, 3, 4}  # Mon–Fri

def as_na_window(
    now: datetime | None = None,
    tz_name: str | None = None,
    open_h: int = 6, open_m: int = 30,     # 06:30 local
    close_h: int = 13, close_m: int = 0,   # 13:00 local
    pre_minutes: int = 15,                 # buffer before open
    post_minutes: int = 30                 # buffer after close
) -> bool:
    """
    Return True if the current time is inside the North American
    cash-session window (including pre/post buffers).
    Defaults to America/Los_Angeles unless tz_name is provided.
    """
    _tz = ZoneInfo((tz_name or TZ_NAME) or "America/Los_Angeles")
    _now = (now.astimezone(_tz) if now else datetime.now(_tz))
    if _now.weekday() not in WEEKDAYS_NA:
        return False
    open_t  = _now.replace(hour=open_h,  minute=open_m,  second=0, microsecond=0)
    close_t = _now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
    start = open_t - timedelta(minutes=pre_minutes)
    end   = close_t + timedelta(minutes=post_minutes)
    return start <= _now <= end

# ----------------------------------------------------------------------
# Placeholder / misc utilities
# ----------------------------------------------------------------------
def get_symbol(symbol: str, default: float = 0.0) -> float:
    """
    Placeholder: always returns default.
    Override with real market data later.
    """
    return default

# ----------------------------------------------------------------------
# Exports
# ----------------------------------------------------------------------
__all__ = [
    "TZ_NAME",
    "now_utc", "now_utc_str",
    "now_local", "now_local_str",
    "as_na_window",
    "get_symbol",
]

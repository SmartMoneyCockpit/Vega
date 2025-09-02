# utils/__init__.py
# Small helper toolkit used by Vega workflows.

from __future__ import annotations
from datetime import datetime, time
from typing import Optional, Iterable
from zoneinfo import ZoneInfo

# ===================== Time helpers =====================

def now(tz: str = "America/Phoenix") -> datetime:
    """Timezone-aware 'now' (defaults to Phoenix, UTC-7 year-round)."""
    return datetime.now(ZoneInfo(tz))

def now_pt() -> datetime:
    """Explicit Phoenix-time helper (legacy callers import this)."""
    return now("America/Phoenix")

# Back-compat alias some scripts still use
get_now = now

# ===================== Trading-window helpers =====================

def _in_window(
    ts: Optional[datetime],
    tz: str,
    start: str,
    end: str,
    weekdays: Iterable[int],
) -> bool:
    z = ZoneInfo(tz)
    tloc = (ts.astimezone(z) if (ts and ts.tzinfo) else
            (ts.replace(tzinfo=z) if ts else datetime.now(z)))
    sh, sm = (int(x) for x in start.split(":", 1))
    eh, em = (int(x) for x in end.split(":", 1))
    open_t, close_t = time(sh, sm), time(eh, em)
    return (tloc.weekday() in set(weekdays)) and (open_t <= tloc.time() < close_t)

def in_us_window(
    ts: Optional[datetime] = None,
    tz: str = "America/Phoenix",
    start: str = "06:30",  # your US session open (local)
    end: str = "13:00",    # your US session close (local)
    weekdays: Iterable[int] = (0, 1, 2, 3, 4),
) -> bool:
    """US trading window check (defaults to Phoenix times)."""
    return _in_window(ts, tz, start, end, weekdays)

# --- Compatibility aliases used by older scripts ---
def in_us_mx_window(
    ts: Optional[datetime] = None,
    tz: str = "America/Phoenix",
    start: str = "06:30",
    end: str = "13:00",
    weekdays: Iterable[int] = (0, 1, 2, 3, 4),
) -> bool:
    """Alias to in_us_window (kept for backward compatibility)."""
    return in_us_window(ts, tz, start, end, weekdays)

def in_us_mxc_window(
    ts: Optional[datetime] = None,
    tz: str = "America/Phoenix",
    start: str = "06:30",
    end: str = "13:00",
    weekdays: Iterable[int] = (0, 1, 2, 3, 4),
) -> bool:
    """Alias to in_us_window (kept for backward compatibility)."""
    return in_us_window(ts, tz, start, end, weekdays)

# ===================== Formatting helpers =====================

def fmt_pct(x: Optional[float], digits: int = 2) -> str:
    if x is None:
        return "—"
    sign = "+" if x >= 0 else ""
    return f"{sign}{x * 100:.{digits}f}%"

def fmt_num(x: Optional[float], digits: int = 2) -> str:
    if x is None:
        return "—"
    return f"{x:.{digits}f}"

# Back-compat alias
fmt_out = fmt_pct

# ===================== Light market data =====================

def _yf():
    try:
        import yfinance as yf  # type: ignore
        return yf
    except Exception:
        return None

def last_price(ticker: str) -> Optional[float]:
    yf = _yf()
    if yf is None:
        return None
    try:
        h = yf.Ticker(ticker).history(period="2d")["Close"]
        return float(h.iloc[-1])
    except Exception:
        return None

def get_from_prev_close(ticker: str) -> Optional[float]:
    yf = _yf()
    if yf is None:
        return None
    try:
        h = yf.Ticker(ticker).history(period="2d")["Close"]
        prev, cur = float(h.iloc[-2]), float(h.iloc[-1])
        return (cur - prev) / prev
    except Exception:
        return None

__all__ = [
    "now", "now_pt", "get_now",
    "in_us_window", "in_us_mx_window", "in_us_mxc_window",
    "fmt_pct", "fmt_num", "fmt_out",
    "last_price", "get_from_prev_close",
]

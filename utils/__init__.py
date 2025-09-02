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

# ===================== Trading window helper =====================

def in_us_window(
    ts: Optional[datetime] = None,
    tz: str = "America/Phoenix",
    start: str = "06:30",   # local open (your rule)
    end: str = "13:00",     # local close (your rule)
    weekdays: Iterable[int] = (0, 1, 2, 3, 4),
) -> bool:
    """
    Return True if local time is within the US trading window [start, end)
    on a weekday (Mon=0 ... Sun=6). Holidays not considered here.
    """
    z = ZoneInfo(tz)
    if ts is None:
        tloc = now(tz)
    else:
        tloc = ts.astimezone(z) if ts.tzinfo else ts.replace(tzinfo=z)

    sh, sm = (int(x) for x in start.split(":", 1))
    eh, em = (int(x) for x in end.split(":", 1))
    open_t  = time(sh, sm)
    close_t = time(eh, em)

    return (tloc.weekday() in set(weekdays)) and (open_t <= tloc.time() < close_t)

# ===================== Format helpers =====================

def fmt_pct(x: Optional[float], digits: int = 2) -> str:
    """Format a fraction (0.0123) as +1.23%. None -> '—'."""
    if x is None:
        return "—"
    sign = "+" if x >= 0 else ""
    return f"{sign}{x * 100:.{digits}f}%"

def fmt_num(x: Optional[float], digits: int = 2) -> str:
    """Format a number with fixed decimals. None -> '—'."""
    if x is None:
        return "—"
    return f"{x:.{digits}f}"

# Back-compat alias some old scripts expect
fmt_out = fmt_pct

# ===================== Light market data =====================

def _yf():
    """Lazy import yfinance so simply importing utils doesn't require it."""
    try:
        import yfinance as yf  # type: ignore
        return yf
    except Exception:
        return None

def last_price(ticker: str) -> Optional[float]:
    """Return the latest close for a ticker (float), or None on failure."""
    yf = _yf()
    if yf is None:
        return None
    try:
        h = yf.Ticker(ticker).history(period="2d")["Close"]
        return float(h.iloc[-1])
    except Exception:
        return None

def get_from_prev_close(ticker: str) -> Optional[float]:
    """Fractional change vs previous close (0.0123 = +1.23%), or None."""
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
    "in_us_window",
    "fmt_pct", "fmt_num", "fmt_out",
    "last_price", "get_from_prev_close",
]

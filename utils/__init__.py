# utils/__init__.py
# Small helper toolkit used by Vega workflows.

from __future__ import annotations

from datetime import datetime
from typing import Optional
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
    """
    Return the latest close for a ticker (float), or None on failure.
    Uses yfinance; callers should handle None.
    """
    yf = _yf()
    if yf is None:
        return None
    try:
        h = yf.Ticker(ticker).history(period="2d")["Close"]
        return float(h.iloc[-1])
    except Exception:
        return None

def get_from_prev_close(ticker: str) -> Optional[float]:
    """
    Fractional change vs previous close (e.g., 0.0123 == +1.23%),
    or None if unavailable.
    """
    yf = _yf()
    if yf is None:
        return None
    try:
        h = yf.Ticker(ticker).history(period="2d")["Close"]
        prev, cur = float(h.iloc[-2]), float(h.iloc[-1])
        return (cur - prev) / prev
    except Exception:
        return None


# What we export
__all__ = [
    "now", "now_pt", "get_now",
    "fmt_pct", "fmt_num", "fmt_out",
    "last_price", "get_from_prev_close",
]

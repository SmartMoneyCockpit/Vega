
# src/filters/tradable.py
from __future__ import annotations
from typing import List
EXCLUDE_PREFIXES = ("$", "SPX", "NDX", ".", "^")
def is_tradable(symbol: str) -> bool:
    s = (symbol or "").upper()
    if not s or any(s.startswith(p) for p in EXCLUDE_PREFIXES): return False
    return True
def filter_tradable(symbols: List[str]) -> List[str]:
    return [s for s in symbols if is_tradable(s)]

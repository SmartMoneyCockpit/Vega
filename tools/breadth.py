# tools/breadth.py
import os, json
from pathlib import Path
from datetime import datetime, timezone

CACHE = Path("vault/cache/breadth.json")
POLYGON_KEY = os.getenv("POLYGON_KEY", "")

def _from_cache():
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None

def _fallback():
    return {
        "as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "advancers": 0,
        "decliners": 0,
        "newHighs": 0,
        "newLows": 0,
        "by_sector": [
            {"name": "Technology", "rs": 52, "advPct": 0.58},
            {"name": "Financials", "rs": 48, "advPct": 0.52},
            {"name": "Energy",     "rs": 55, "advPct": 0.64},
        ],
        "source": "fallback",
    }

def get_breadth():
    cached = _from_cache()
    if cached:
        cached["source"] = "cache"
        return cached
    # (optional) Add live fetch here later using POLYGON_KEY, then cache to CACHE
    return _fallback()
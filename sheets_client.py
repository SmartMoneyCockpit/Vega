
"""
Drop-in Google Sheets client for Vega Cockpit (Render-compatible).

Goals:
- Fix "Quota exceeded for quota metric 'Read requests' ... sheets.googleapis.com"
- Batch reads/writes, cache metadata and values (TTL), and auto-fallback to local snapshots
- Gentle rate limiting and exponential backoff for RESOURCE_EXHAUSTED / RATE_LIMIT_EXCEEDED

Usage (minimal change):
    from src.sheets_client import Sheets
    sheets = Sheets()  # reads config from env
    ws = sheets.ensure_tab(spreadsheet_id, "NA_TradeLog", headers=[...])
    rows = sheets.read_table(spreadsheet_id, "WatchList")            # cached
    sheets.append_rows(spreadsheet_id, "NA_TradeLog", [[...,...]])    # batched

Environment (set in Render dashboard):
    VEGA_SHEETS_TTL_SEC=120        # cache TTL for values
    VEGA_SHEETS_META_TTL_SEC=1800  # cache TTL for metadata (tab list etc.)
    VEGA_SHEETS_RPM_SOFT=50        # soft limit per minute
    VEGA_SHEETS_RPS_SOFT=5         # soft limit per second
    VEGA_SHEETS_SNAPSHOT_DIR=/opt/render/project/src/.cache/snapshots
    GOOGLE_SHEETS_CREDENTIALS_JSON=/opt/render/project/src/credentials.json  (or service account default)

This module only relies on gspread + google-auth. No extra libs required.
"""
from __future__ import annotations

import os
import time
import json
import threading
import hashlib
from typing import List, Dict, Any, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

# ---------------------------- utilities ----------------------------

def _now() -> float:
    return time.time()

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _hash_key(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
    return h.hexdigest()[:16]

class TTLCache:
    """Very small in-memory TTL cache (thread-safe)."""
    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self._lock = threading.Lock()
        self._mem: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._mem.get(key)
            if not item:
                return None
            ts, val = item
            if _now() - ts > self.ttl:
                self._mem.pop(key, None)
                return None
            return val

    def set(self, key: str, val: Any) -> None:
        with self._lock:
            self._mem[key] = (_now(), val)

class TokenBucket:
    """Simple token bucket limiter for RPM/RPS soft limits."""
    def __init__(self, per_sec: float, per_min: float) -> None:
        self.rate_sec = per_sec
        self.rate_min = per_min
        self.tokens_sec = per_sec
        self.tokens_min = per_min
        self.last = _now()
        self._lock = threading.Lock()

    def consume(self, cost: float = 1.0) -> None:
        with self._lock:
            now = _now()
            elapsed = now - self.last
            self.last = now
            # refill
            self.tokens_sec = min(self.rate_sec, self.tokens_sec + elapsed * self.rate_sec)
            self.tokens_min = min(self.rate_min, self.tokens_min + elapsed * (self.rate_min/60.0))
            # wait if not enough
            def need_sleep(tokens, cost): return max(0.0, (cost - tokens) / (self.rate_sec if tokens is self.tokens_sec else self.rate_min))
            while self.tokens_sec < cost or self.tokens_min < cost:
                sleep_for = 0.05
                time.sleep(sleep_for)
                now2 = _now()
                delta = now2 - self.last
                self.last = now2
                self.tokens_sec = min(self.rate_sec, self.tokens_sec + delta * self.rate_sec)
                self.tokens_min = min(self.rate_min, self.tokens_min + delta * (self.rate_min/60.0))
            self.tokens_sec -= cost
            self.tokens_min -= cost

# ---------------------------- Sheets wrapper ----------------------------

class Sheets:
    def __init__(self):
        ttl = float(os.getenv("VEGA_SHEETS_TTL_SEC", "120"))
        meta_ttl = float(os.getenv("VEGA_SHEETS_META_TTL_SEC", "1800"))
        rps = float(os.getenv("VEGA_SHEETS_RPS_SOFT", "5"))
        rpm = float(os.getenv("VEGA_SHEETS_RPM_SOFT", "50"))
        self.snap_dir = os.getenv("VEGA_SHEETS_SNAPSHOT_DIR", "./.cache/snapshots")
        _ensure_dir(self.snap_dir)

        self.cache = TTLCache(ttl)
        self.meta_cache = TTLCache(meta_ttl)
        self.limiter = TokenBucket(per_sec=rps, per_min=rpm)

        creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        if creds_path and os.path.exists(creds_path):
            creds = Credentials.from_service_account_file(creds_path, scopes=scope)
        else:
            # fallback to default service account if gspread can find it
            creds = Credentials.from_service_account_info(json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON", "{}") or "{}"), scopes=scope) if os.environ.get("GOOGLE_CREDENTIALS_JSON") else None
            if creds is None:
                # last resort: let gspread try default
                pass
        self.gc = gspread.authorize(creds) if 'creds' in locals() and creds is not None else gspread.service_account()

    # ---------- helpers ----------
    def _snapshot_path(self, spreadsheet_id: str, tab: str, a1: Optional[str]) -> str:
        key = _hash_key(spreadsheet_id, tab, a1 or "ALL")
        return os.path.join(self.snap_dir, f"{key}.json")

    def _save_snapshot(self, path: str, data: Any) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"ts": _now(), "data": data}, f)
        except Exception:
            pass

    def _load_snapshot(self, path: str) -> Optional[Any]:
        try:
            if not os.path.exists(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("data")
        except Exception:
            return None

    def _open(self, spreadsheet_id: str):
        # metadata cache: spreadsheet obj
        cache_key = f"open::{spreadsheet_id}"
        ss = self.meta_cache.get(cache_key)
        if ss is not None:
            return ss
        self.limiter.consume()
        ss = self.gc.open_by_key(spreadsheet_id)
        self.meta_cache.set(cache_key, ss)
        return ss

    def list_tabs(self, spreadsheet_id: str) -> List[str]:
        cache_key = f"tabs::{spreadsheet_id}"
        tabs = self.meta_cache.get(cache_key)
        if tabs is not None:
            return tabs
        ss = self._open(spreadsheet_id)
        self.limiter.consume()
        worksheets = ss.worksheets()
        tabs = [w.title for w in worksheets]
        self.meta_cache.set(cache_key, tabs)
        return tabs

    def ensure_tab(self, spreadsheet_id: str, tab: str, headers: Optional[List[str]] = None):
        """Create tab if not exists, set headers only once. Cached to avoid repeated metadata calls."""
        tabs = self.list_tabs(spreadsheet_id)
        ss = self._open(spreadsheet_id)
        if tab not in tabs:
            # create once
            self.limiter.consume()
            ws = ss.add_worksheet(title=tab, rows=1000, cols=50)
            # update cache
            self.meta_cache.set(f"tabs::{spreadsheet_id}", tabs + [tab])
        else:
            ws = ss.worksheet(tab)

        if headers:
            # read first row from cache or remote
            first_row = self.read_range(spreadsheet_id, tab, "1:1")
            if not first_row or not first_row[0] or [h.strip() for h in first_row[0]] != [h.strip() for h in headers]:
                # write headers once
                self.update_range(spreadsheet_id, tab, "1:1", [headers])
        return ws

    # ---------- value operations with caching/fallback ----------

    def read_range(self, spreadsheet_id: str, tab: str, a1_range: str) -> List[List[Any]]:
        cache_key = f"read::{spreadsheet_id}::{tab}::{a1_range}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        path = self._snapshot_path(spreadsheet_id, tab, a1_range)
        try:
            self.limiter.consume()
            ws = self._open(spreadsheet_id).worksheet(tab)
            values = ws.get(a1_range)  # gspread auto batch under the hood
            self.cache.set(cache_key, values)
            self._save_snapshot(path, values)
            return values
        except Exception as e:
            # fallback to snapshot
            snap = self._load_snapshot(path)
            if snap is not None:
                return snap
            # as last resort, return empty
            return []

    def read_table(self, spreadsheet_id: str, tab: str) -> List[Dict[str, Any]]:
        """Reads entire tab as list of dicts (header -> value). Cached; falls back to snapshot."""
        cache_key = f"table::{spreadsheet_id}::{tab}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        path = self._snapshot_path(spreadsheet_id, tab, None)
        try:
            self.limiter.consume()
            ws = self._open(spreadsheet_id).worksheet(tab)
            rows = ws.get_all_values()
            if not rows:
                return []
            headers = [h.strip() for h in rows[0]]
            data = [dict(zip(headers, r + [""] * (len(headers)-len(r)))) for r in rows[1:]]
            self.cache.set(cache_key, data)
            self._save_snapshot(path, data)
            return data
        except Exception:
            snap = self._load_snapshot(path)
            return snap or []

    def update_range(self, spreadsheet_id: str, tab: str, a1_range: str, values: List[List[Any]]) -> None:
        """Writes a 2D array to the given range; rate-limited with backoff."""
        path = self._snapshot_path(spreadsheet_id, tab, a1_range)
        backoff = 0.5
        for attempt in range(6):
            try:
                self.limiter.consume()
                ws = self._open(spreadsheet_id).worksheet(tab)
                ws.update(a1_range, values)
                # update cache & snapshot
                self._save_snapshot(path, values)
                self.cache.set(f"read::{spreadsheet_id}::{tab}::{a1_range}", values)
                return
            except Exception as e:
                msg = str(e)
                if "RESOURCE_EXHAUSTED" in msg or "RATE_LIMIT_EXCEEDED" in msg or "429" in msg:
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 8.0)
                    continue
                else:
                    raise

    def append_rows(self, spreadsheet_id: str, tab: str, rows: List[List[Any]]) -> None:
        """Appends rows in a single request; retries on limit errors."""
        if not rows:
            return
        backoff = 0.5
        for attempt in range(6):
            try:
                self.limiter.consume()
                ws = self._open(spreadsheet_id).worksheet(tab)
                ws.append_rows(rows, value_input_option="USER_ENTERED")
                # invalidate table cache (new rows)
                self.cache.set(f"table::{spreadsheet_id}::{tab}", None)
                return
            except Exception as e:
                msg = str(e)
                if "RESOURCE_EXHAUSTED" in msg or "RATE_LIMIT_EXCEEDED" in msg or "429" in msg:
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 8.0)
                    continue
                else:
                    raise

# Singleton for convenience
sheets = Sheets()

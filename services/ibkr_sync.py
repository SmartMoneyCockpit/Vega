
# src/services/ibkr_sync.py
from __future__ import annotations
import os, json, csv, requests
from typing import List

IBKR_BASE_URL = os.getenv("IBKR_BASE_URL", "").rstrip("/")
IBKR_VERIFY_SSL = os.getenv("IBKR_VERIFY_SSL", "false").lower() == "true"
DATA_DIR = os.getenv("DATA_DIR", "data")
FALLBACK_CSV = os.path.join(DATA_DIR, "ibkr_positions.csv")

def _cp_get(path: str):
    r = requests.get(f"{IBKR_BASE_URL}{path}", timeout=15, verify=IBKR_VERIFY_SSL)
    r.raise_for_status(); return r.json()

def _dedupe(items: List[str]) -> List[str]:
    out, seen = [], set()
    for s in items:
        s = (s or "").strip().upper()
        if s and s not in seen:
            out.append(s); seen.add(s)
    return out

def fetch_ibkr_symbols() -> List[str]:
    syms = []
    if IBKR_BASE_URL:
        try:
            accs = _cp_get("/v1/api/iserver/accounts")
            account_ids = [a.get("id") for a in accs.get("accounts", []) if a.get("id")]
            for acc in account_ids:
                for p in _cp_get(f"/v1/api/portfolio/{acc}/positions"):
                    sym = p.get("ticker") or p.get("symbol") or ""
                    exch = (p.get("exchange") or "").upper()
                    tv = f"{exch}:{sym}" if exch in ("NYSE","NASDAQ","AMEX","ARCA") else sym
                    if tv: syms.append(tv)
        except Exception as e:
            print("[ibkr_sync] live IBKR failed:", e)
    if not syms and os.path.exists(FALLBACK_CSV):
        with open(FALLBACK_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sym = (row.get("Symbol") or "").strip().upper()
                exch = (row.get("Exchange") or "").strip().upper()
                tv = f"{exch}:{sym}" if exch in ("NYSE","NASDAQ","AMEX","ARCA") else sym
                if tv: syms.append(tv)
    return _dedupe(syms)

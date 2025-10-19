# src/vega/bridge_client.py
from __future__ import annotations
import httpx
from config.ib_bridge_client import get_bridge_url, default_headers

BASE = get_bridge_url().rstrip("/")
HEADERS = default_headers()

def _get(path: str, **kw):
    return httpx.get(f"{BASE}{path}", headers=HEADERS, timeout=6.0, **kw)

def health() -> dict:
    return _get("/health").json()

def connect() -> dict:
    return _get("/connect").json()

def quote(symbol: str) -> dict:
    return _get("/quote", params={"symbol": symbol}).json()

def bars(symbol: str, tf: str = "1d", limit: int = 100) -> dict:
    return _get("/bars", params={"symbol": symbol, "tf": tf, "limit": limit}).json()

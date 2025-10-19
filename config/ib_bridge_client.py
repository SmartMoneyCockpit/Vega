
# config/ib_bridge_client.py
"""
Centralized helpers for reaching your IBKR Bridge (XIBC) from the Vega cockpit.

Priority for the base URL:
1) IBKR_BRIDGE_URL (full URL like "https://bridge.cryptobitcoinprofits.com")
2) IB_BRIDGE_URL    (legacy; full URL)
3) Build from BRIDGE_SCHEME/BRIDGE_HOST/BRIDGE_PORT (e.g., http/93.127.136.167/8888)
4) Final fallback: http://127.0.0.1:8080
"""
from __future__ import annotations
import os

def get_bridge_url() -> str:
    # full-URL envs first
    for var in ("IBKR_BRIDGE_URL", "IB_BRIDGE_URL"):
        val = os.getenv(var)
        if val:
            return val.rstrip("/")
    # piecewise envs
    scheme = os.getenv("BRIDGE_SCHEME", "http").strip()
    host   = (os.getenv("BRIDGE_HOST") or "").strip()
    port   = (os.getenv("BRIDGE_PORT") or "").strip()
    if host:
        if host in ("0.0.0.0", "::"):
            host = "127.0.0.1"
        if not port:
            port = "8088"
        return f"{scheme}://{host}:{port}".rstrip("/")
    # final fallback
    return "http://127.0.0.1:8080"

def get_bridge_api_key() -> str:
    """
    Returns the API key header value required by the bridge (if any).
    """
    return (
        os.getenv("IB_BRIDGE_API_KEY")
        or os.getenv("IBKR_BRIDGE_API_KEY")
        or os.getenv("BRIDGE_API_KEY")
        or ""
    )

def default_headers() -> dict:
    key = get_bridge_api_key()
    return {"x-api-key": key} if key else {}

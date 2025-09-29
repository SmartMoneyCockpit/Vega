
# src/config/ib_bridge_client.py
from __future__ import annotations
import os

def get_bridge_url() -> str:
    for var in ("IBKR_BRIDGE_URL", "IB_BRIDGE_URL"):
        val = os.getenv(var)
        if val:
            return val.rstrip("/")
    scheme = os.getenv("BRIDGE_SCHEME", "http").strip()
    host   = (os.getenv("BRIDGE_HOST") or "").strip()
    port   = (os.getenv("BRIDGE_PORT") or "").strip()
    if host:
        if host in ("0.0.0.0", "::"):
            host = "127.0.0.1"
        if not port:
            port = "8088"
        return f"{scheme}://{host}:{port}".rstrip("/")
    return "http://127.0.0.1:8088"

def get_bridge_api_key() -> str:
    return (
        os.getenv("IB_BRIDGE_API_KEY")
        or os.getenv("IBKR_BRIDGE_API_KEY")
        or os.getenv("BRIDGE_API_KEY")
        or ""
    )

def default_headers() -> dict:
    key = get_bridge_api_key()
    return {"x-api-key": key} if key else {}

# src/components/bridge.py
import os
from urllib.parse import urlparse

def _sanitize(url: str) -> str:
    url = url.strip().rstrip("/")
    if not url:
        return url
    parsed = urlparse(url if "://" in url else f"http://{url}")
    scheme = parsed.scheme or "http"
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (8088 if scheme in ("http","https") else 80)
    # avoid unusable bind addresses
    if host in ("0.0.0.0", "::"):
        host = os.getenv("BRIDGE_PUBLIC_HOST", os.getenv("IB_HOST", "127.0.0.1"))
    return f"{scheme}://{host}:{port}"

def get_bridge_base() -> str:
    # 1) Strong preference: full URL via IBKR_BRIDGE_URL (or IB_BRIDGE_URL)
    base = os.getenv("IBKR_BRIDGE_URL") or os.getenv("IB_BRIDGE_URL", "")
    if base:
        return _sanitize(base)
    # 2) Fallback: compose from parts (BRIDGE_*)
    scheme = os.getenv("BRIDGE_SCHEME", "http")
    host   = os.getenv("BRIDGE_HOST", "127.0.0.1")
    port   = os.getenv("BRIDGE_PORT", "8088")
    return _sanitize(f"{scheme}://{host}:{port}")

def get_bridge_headers() -> dict:
    api_key = os.getenv("IB_BRIDGE_API_KEY") or os.getenv("BRIDGE_API_KEY") or ""
    return {"x-api-key": api_key} if api_key else {}

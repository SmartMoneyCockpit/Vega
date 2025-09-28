# src/components/bridge.py
import os

def get_bridge_base() -> str:
    scheme = os.getenv("BRIDGE_SCHEME", "http")
    host   = os.getenv("BRIDGE_HOST", "127.0.0.1")
    # if someone set a bind-all, use localhost for client calls
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    port   = os.getenv("BRIDGE_PORT", "8088")
    return f"{scheme}://{host}:{port}"

def get_bridge_headers() -> dict:
    api_key = os.getenv("IB_BRIDGE_API_KEY", "")
    return {"x-api-key": api_key} if api_key else {}

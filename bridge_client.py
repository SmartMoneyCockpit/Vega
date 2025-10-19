# bridge_client.py
import os, requests

BRIDGE_URL = os.getenv("BRIDGE_URL", "").rstrip("/")
BRIDGE_TOKEN = os.getenv("BRIDGE_TOKEN", "")

class BridgeError(Exception):
    pass

def _headers():
    if not BRIDGE_TOKEN:
        raise BridgeError("Missing BRIDGE_TOKEN env var")
    return {"Authorization": f"Bearer {BRIDGE_TOKEN}"}

def bridge_health(timeout=5):
    if not BRIDGE_URL:
        raise BridgeError("Missing BRIDGE_URL env var")
    r = requests.get(f"{BRIDGE_URL}/health", timeout=timeout)
    r.raise_for_status()
    return r.json()

def bridge_connect(timeout=5):
    if not BRIDGE_URL:
        raise BridgeError("Missing BRIDGE_URL env var")
    r = requests.get(f"{BRIDGE_URL}/health", headers=_headers(), timeout=timeout)
    r.raise_for_status()
    return r.json()

def bridge_scan(params: dict | None = None, timeout=10):
    """Example scan call. Change the path/body to match your bridge’s real scan endpoint."""
    if not BRIDGE_URL:
        raise BridgeError("Missing BRIDGE_URL env var")
    r = requests.get(f"{BRIDGE_URL}/scan", headers=_headers(), params=params or {}, timeout=timeout)
    if r.status_code == 401:
        raise BridgeError("Unauthorized (check BRIDGE_TOKEN)")
    r.raise_for_status()
    return r.json()

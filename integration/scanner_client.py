# integration/scanner_client.py
# Minimal client to read Vega Scanner snapshot via HTTP or local file.
from __future__ import annotations
import os, json, time
from pathlib import Path
from typing import Dict, Any, Optional
import requests

DEFAULT_URL = os.environ.get("SCANNER_URL", "http://127.0.0.1:8009/snapshot")
DEFAULT_PATH = os.environ.get("SCANNER_PATH", "outputs/snapshot.json")

def load_snapshot(timeout: float = 2.0) -> Optional[Dict[str, Any]]:
    url = os.environ.get("SCANNER_URL", DEFAULT_URL)
    path = os.environ.get("SCANNER_PATH", DEFAULT_PATH)

    # Try HTTP first
    try:
        r = requests.get(url, timeout=timeout)
        if r.ok:
            return r.json()
    except Exception:
        pass

    # Fallback to local file
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
    return None

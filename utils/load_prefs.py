from __future__ import annotations
import json, yaml, os, datetime as dt
from typing import Any, Dict

_PREFS_PATH = os.environ.get("VEGA_PREFS_PATH", "config/vega_prefs.yaml")
_VERSION_PATH = os.environ.get("VEGA_VERSION_PATH", "config/version.json")

class VegaPrefs:
    def __init__(self, prefs: Dict[str, Any], version: Dict[str, Any]):
        self._prefs = prefs or {}
        self._version = version or {}

    def get(self, *keys, default=None):
        node = self._prefs
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    def enabled(self, *keys, default=False) -> bool:
        val = self.get(*keys, default=default)
        return bool(val) is True

    @property
    def version(self) -> str:
        return self._version.get("version", "0.0.0")

    @property
    def last_updated(self) -> str:
        return self._version.get("last_updated_utc", "")

def load_prefs() -> VegaPrefs:
    with open(_PREFS_PATH, "r", encoding="utf-8") as f:
        prefs = yaml.safe_load(f) or {}
    if os.path.exists(_VERSION_PATH):
        version = json.load(open(_VERSION_PATH, "r", encoding="utf-8"))
    else:
        version = {
            "version": "0.0.0",
            "last_updated_utc": dt.datetime.utcnow().isoformat()+"Z",
            "change_notes": "bootstrap"
        }
    return VegaPrefs(prefs, version)

# utils/load_prefs.py
# Unified preferences loader for Vega Cockpit.
# - Single source of truth (replaces any prefs_bootstrap.py usage)
# - Safe if files/env are missing
# - Returns VegaPrefs, a dict subclass with helpers: enabled(), getp()

from __future__ import annotations
import os
import json
from typing import Any, Dict

try:
    import yaml  # requires pyyaml in requirements
except Exception:  # harden if yaml isn't installed
    yaml = None  # type: ignore


# ---------- Config paths (can be overridden by env) ----------
DEFAULT_PREFS_PATH = os.environ.get("VEGA_PREFS_PATH", "config/vega_prefs.yaml")
DEFAULT_VERSION_PATH = os.environ.get("VEGA_VERSION_PATH", "config/version.json")


# ---------- Small dict-with-helpers wrapper ----------
class VegaPrefs(dict):
    """
    Dict with helper methods used across the cockpit.

    Methods
    -------
    getp(*keys, default=None) -> Any
        Nested path get. Example: prefs.getp("morning_report", "status_banner", default=True)

    enabled(*keys, default=True) -> bool
        Like getp() but coerces to boolean with tolerant parsing (True/False, 1/0, yes/no, on/off).
    """
    TRUTHY = {"true", "1", "yes", "on", "y", "t"}
    FALSY  = {"false", "0", "no", "off", "n", "f"}

    def _coerce_bool(self, value: Any, default: bool = True) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            s = value.strip().lower()
            if s in self.TRUTHY:
                return True
            if s in self.FALSY:
                return False
        return default

    def getp(self, *keys: str, default: Any = None) -> Any:
        node: Any = self
        for k in keys:
            if isinstance(node, dict) and k in node:
                node = node[k]
            else:
                return default
        return node

    def enabled(self, *keys: str, default: bool = True) -> bool:
        val = self.getp(*keys, default=default)
        return self._coerce_bool(val, default=default)


# ---------- File readers ----------
def _load_yaml(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path) or yaml is None:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}
    except Exception:
        return {}


def _load_json(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data or {}
    except Exception:
        return {}


# ---------- Optional env overrides ----------
def _env_overrides() -> Dict[str, Any]:
    """
    Read simple VEGA_* env vars and fold into prefs.
    Example: VEGA_REGION=USA -> {"region": "USA"}
    Extend as needed for your cockpit.
    """
    out: Dict[str, Any] = {}
    for k, v in os.environ.items():
        if not k.startswith("VEGA_"):
            continue
        key = k[len("VEGA_"):].lower()
        out[key] = v
    return out


# ---------- Public API ----------
def load_prefs(
    prefs_path: str = DEFAULT_PREFS_PATH,
    version_path: str = DEFAULT_VERSION_PATH,
) -> VegaPrefs:
    """
    Merge order (later wins):
        {} <- YAML prefs <- version.json under key 'version' <- VEGA_* env overrides
    Returns:
        VegaPrefs (dict subclass) with helpers .enabled() and .getp()
    """
    prefs: Dict[str, Any] = {}

    # 1) YAML (if present)
    prefs.update(_load_yaml(prefs_path))

    # 2) Version info (if present)
    version_info = _load_json(version_path)
    if version_info:
        prefs["version"] = version_info

    # 3) Env overrides
    prefs.update(_env_overrides())

    # 4) Minimal safe defaults
    if "app" not in prefs:
        prefs["app"] = {"name": "Vega Cockpit"}
    # sensible defaults used by pages
    prefs.setdefault("morning_report", {}).setdefault("status_banner", True)

    return VegaPrefs(prefs)

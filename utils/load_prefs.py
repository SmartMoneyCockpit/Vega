from __future__ import annotations
import os, json
from typing import Any, Dict

try:
    import yaml  # pyyaml should be in requirements
except Exception:  # harden if yaml isn't present
    yaml = None

# Default config file locations (overridable via env)
DEFAULT_PREFS_PATH = os.environ.get("VEGA_PREFS_PATH", "config/vega_prefs.yaml")
DEFAULT_VERSION_PATH = os.environ.get("VEGA_VERSION_PATH", "config/version.json")

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

def _env_overrides() -> Dict[str, Any]:
    """
    Optional: read simple VEGA_* env vars and fold into prefs.
    Only grabs flat key=value pairs like VEGA_REGION=USA -> {"region": "USA"}.
    Extend as needed for your cockpit.
    """
    mapping = {}
    for k, v in os.environ.items():
        if not k.startswith("VEGA_"):
            continue
        key = k.removeprefix("VEGA_").lower()
        mapping[key] = v
    return mapping

def load_prefs(
    prefs_path: str = DEFAULT_PREFS_PATH,
    version_path: str = DEFAULT_VERSION_PATH
) -> Dict[str, Any]:
    """
    Unified preferences loader for Vega Cockpit.
    Merge order (later wins): defaults <- YAML prefs <- version.json <- env overrides.
    """
    prefs: Dict[str, Any] = {}

    # 1) YAML config (if present)
    prefs.update(_load_yaml(prefs_path))

    # 2) Version info (optional)
    version_info = _load_json(version_path)
    if version_info:
        prefs["version"] = version_info

    # 3) Environment overrides
    prefs.update(_env_overrides())

    # 4) Minimal safe defaults if empty
    if "app" not in prefs:
        prefs["app"] = {"name": "Vega Cockpit"}

    return prefs

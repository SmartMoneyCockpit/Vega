# src/utils/prefs_bootstrap.py

# This shim keeps legacy imports working:
# from utils.prefs_bootstrap import prefs

try:
    # Case 1: load_prefs.py already exposes `prefs`
    from .load_prefs import prefs  # type: ignore[attr-defined]
except Exception:
    # Case 2: it exposes a function like `load_prefs()`
    from .load_prefs import load_prefs as prefs  # type: ignore

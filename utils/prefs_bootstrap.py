# src not used here; your layout is Vega/app.py + Vega/utils/*
# This shim keeps legacy imports working:
# from utils.prefs_bootstrap import prefs

try:
    # If utils/load_prefs.py exposes `prefs`, just forward it.
    from .load_prefs import prefs  # type: ignore[attr-defined]
except Exception:
    # Otherwise, fall back to a function named `load_prefs` and alias it as `prefs`.
    from .load_prefs import load_prefs as prefs  # type: ignore

from core.registry import register
import importlib

CANDIDATES = [
    "pages.01_RealTime_Scanner",
    "pages.real_time_scanner",
    "pages.realtime_scanner",
    "pages.scanner",
]

def _load():
    for name in CANDIDATES:
        try:
            return importlib.import_module(name)
        except Exception:
            continue
    raise ImportError(f"None of these scanner modules were found: {CANDIDATES}")

@register("tools/real-time-scanner")
def page():
    mod = _load()
    for fn_name in ("page", "render", "main", "run"):
        fn = getattr(mod, fn_name, None)
        if callable(fn):
            return fn()
    return None

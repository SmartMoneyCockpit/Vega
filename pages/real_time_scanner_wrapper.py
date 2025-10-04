
from core.registry import register
import importlib
ROUTE = "tools/real-time-scanner"
CANDIDATES = ["pages.01_RealTime_Scanner","pages.real_time_scanner","pages.realtime_scanner","pages.scanner"]
def _load():
    for name in CANDIDATES:
        try: return importlib.import_module(name)
        except Exception: continue
    raise ImportError(f"Scanner module not found: {CANDIDATES}")
@register(ROUTE)
def page():
    mod = _load()
    for fn in ("page","render","main","run"):
        f = getattr(mod, fn, None)
        if callable(f): return f()
    return None

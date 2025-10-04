from core.registry import register
import importlib

CANDIDATES = [
    "pages.markets.apac",
    "pages.markets.asia_pacific",
    "pages.APAC",
    "pages.Markets_APAC",
]

def _load():
    for name in CANDIDATES:
        try:
            return importlib.import_module(name)
        except Exception:
            continue
    raise ImportError(f"APAC module not found. Tried: {CANDIDATES}")

@register("markets/apac")
def page():
    mod = _load()
    for fn in ("page","render","main","run"):
        f = getattr(mod, fn, None)
        if callable(f): return f()
    return None

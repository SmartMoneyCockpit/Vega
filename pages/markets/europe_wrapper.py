from core.registry import register
import importlib

CANDIDATES = [
    "pages.markets.europe",
    "pages.Europe",
    "pages.Markets_EU",
]

def _load():
    for name in CANDIDATES:
        try:
            return importlib.import_module(name)
        except Exception:
            continue
    raise ImportError(f"Europe module not found. Tried: {CANDIDATES}")

@register("markets/europe")
def page():
    mod = _load()
    for fn in ("page","render","main","run"):
        f = getattr(mod, fn, None)
        if callable(f): return f()
    return None

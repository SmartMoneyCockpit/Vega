from core.registry import register
import importlib

CANDIDATES = [
    "pages.markets.north_america",
    "pages.markets.northamerica",
    "pages.NorthAmerica",
    "pages.Markets_NA",
]

def _load():
    for name in CANDIDATES:
        try:
            return importlib.import_module(name)
        except Exception:
            continue
    raise ImportError(f"North America module not found. Tried: {CANDIDATES}")

@register("markets/north-america")
def page():
    mod = _load()
    for fn in ("page","render","main","run"):
        f = getattr(mod, fn, None)
        if callable(f): return f()
    return None

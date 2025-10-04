from core.registry import register
import importlib

ROUTE = "scanner/live"
MODULE = "pages.10_IBKR_Scanner"

@register(ROUTE)
def page():
    m = importlib.import_module(MODULE)
    for fn in ("page", "render", "main", "run"):
        f = getattr(m, fn, None)
        if callable(f):
            return f()
    return None

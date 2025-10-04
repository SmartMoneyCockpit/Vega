from core.registry import register
import importlib

ROUTE = "ibkr/feed-status"
MODULE = "pages.095_IB_Feed_Status"

@register(ROUTE)
def page():
    m = importlib.import_module(MODULE)
    for fn in ("page", "render", "main", "run"):
        f = getattr(m, fn, None)
        if callable(f):
            return f()
    return None

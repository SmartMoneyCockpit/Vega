
from core.registry import register
import importlib
ROUTE = "scanner/on-demand"
MODULE = "pages.01_Scanner_OnDemand"
@register(ROUTE)
def page():
    m = importlib.import_module(MODULE)
    for fn in ("page","render","main","run"):
        f = getattr(m, fn, None)
        if callable(f): return f()
    return None

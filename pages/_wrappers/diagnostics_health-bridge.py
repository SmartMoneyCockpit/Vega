
from core.registry import register
import importlib
ROUTE = "diagnostics/health-bridge"
MODULE = "pages.99_Bridge_Health_Test"
@register(ROUTE)
def page():
    m = importlib.import_module(MODULE)
    for fn in ("page","render","main","run"):
        f = getattr(m, fn, None)
        if callable(f): return f()
    return None

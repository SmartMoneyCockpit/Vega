
from core.registry import register
import importlib
ROUTE = "ibkr/quick-test"
MODULE = "pages.097_IBKR_Quick_Test_ibuy"
@register(ROUTE)
def page():
    m = importlib.import_module(MODULE)
    for fn in ("page","render","main","run"):
        f = getattr(m, fn, None)
        if callable(f): return f()
    return None

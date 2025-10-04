
from core.registry import register
import importlib
ROUTE = "tools/tradingview-bridge"
MODULE = "pages.10_TradingView_Bridge"
@register(ROUTE)
def page():
    m = importlib.import_module(MODULE)
    for fn in ("page","render","main","run"):
        f = getattr(m, fn, None)
        if callable(f): return f()
    return None

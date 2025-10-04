
from core.registry import register
import importlib
ROUTE = "tools/tradingview-charts"
MODULE = "pages.05_TradingView_Charts"
@register(ROUTE)
def page():
    m = importlib.import_module(MODULE)
    for fn in ("page","render","main","run"):
        f = getattr(m, fn, None)
        if callable(f): return f()
    return None


from core.registry import register
import importlib
ROUTE = "tools/vega-native-chart"
MODULE = "pages.06_Vega_Native_Chart"
@register(ROUTE)
def page():
    m = importlib.import_module(MODULE)
    for fn in ("page","render","main","run"):
        f = getattr(m, fn, None)
        if callable(f): return f()
    return None

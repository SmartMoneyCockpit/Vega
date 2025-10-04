
"""
Filesystem-based auto-discovery of pages under ./pages/**
- Does NOT import a 'pages' package (works with Streamlit's special dir).
- Route from path: pages/reports/morning.py -> 'reports/morning'.
- Honors ROUTE if present; otherwise uses path-derived route.
- Registers any callable page().
"""
import importlib, pkgutil, pathlib, sys
from core.registry import register, PAGE_REGISTRY

PROJECT_ROOT = pathlib.Path.cwd()
PAGES_ROOT = PROJECT_ROOT / "pages"

def _iter_modules_fs():
    if not PAGES_ROOT.exists():
        return []
    return list(pkgutil.walk_packages([str(PAGES_ROOT)], prefix="pages."))

def _route_from_modname(module_name: str) -> str:
    rel = module_name.split("pages.", 1)[-1]
    return rel.replace(".", "/")

def autorun():
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    for modinfo in _iter_modules_fs():
        modname = getattr(modinfo, "name", None) or modinfo[0]
        try:
            m = importlib.import_module(modname)
        except Exception:
            continue
        route = getattr(m, "ROUTE", None)
        page_fn = getattr(m, "page", None)
        if callable(page_fn):
            if not route:
                route = _route_from_modname(modname)
            if route not in PAGE_REGISTRY:
                register(route)(page_fn)

def build_groups():
    groups = {}
    for route in sorted(PAGE_REGISTRY.keys()):
        segs = [s for s in route.split("/") if s]
        group = segs[0].capitalize() if segs else "Pages"
        label = (segs[-1].replace("_"," ").title() if segs else route)
        groups.setdefault(group, []).append({"label": label, "route": route})
    return [{"group": g, "items": items} for g, items in groups.items()]

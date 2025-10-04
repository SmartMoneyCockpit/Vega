"""
Auto-discover pages under ./pages/** and register them.

Rules:
- If a module sets ROUTE = "group/key", that route is used.
- Else route is derived from relative path (without .py),
  e.g. pages/reports/morning.py -> "reports/morning".
- A renderable function must be named `page()`.
"""
import importlib
import pkgutil
import pathlib
import sys
from core.registry import register, PAGE_REGISTRY

def _iter_modules(root_pkg: str = "pages"):
    """Yield ModuleInfo for all modules under `root_pkg`."""
    try:
        pkg = importlib.import_module(root_pkg)
    except Exception:
        return []
    base = pathlib.Path(pkg.__file__).parent
    return list(pkgutil.walk_packages([str(base)], prefix=f"{root_pkg}."))

def _route_from_modname(module_name: str) -> str:
    """Convert 'pages.reports.morning' -> 'reports/morning'."""
    rel = module_name.split("pages.", 1)[-1]
    return rel.replace(".", "/")

def autorun():
    """Import pages/** modules and register any callable `page()` function."""
    # Ensure 'pages' importable
    if "pages" not in sys.modules:
        try:
            import pages  # noqa: F401
        except Exception:
            return

    for modinfo in _iter_modules("pages"):
        modname = getattr(modinfo, "name", None) or modinfo[0]
        try:
            m = importlib.import_module(modname)
        except Exception:
            # Skip broken imports, but don't crash the router
            continue

        route = getattr(m, "ROUTE", None)
        page_fn = getattr(m, "page", None)

        if callable(page_fn):
            if not route:
                route = _route_from_modname(modname)
            if route not in PAGE_REGISTRY:
                register(route)(page_fn)

def build_groups():
    """
    Build sidebar group structure from PAGE_REGISTRY.
    Top-level segment becomes the group name; leaf becomes the label.
    """
    groups = {}
    for route in sorted(PAGE_REGISTRY.keys()):
        segs = [s for s in route.split("/") if s]
        group = segs[0].capitalize() if segs else "Pages"
        label = (segs[-1].replace("_", " ").title() if segs else route)
        groups.setdefault(group, []).append({"label": label, "route": route})
    return [{"group": g, "items": items} for g, items in groups.items()]

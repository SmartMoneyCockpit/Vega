"""
Route registry for Vega Cockpit (non-destructive).
Use @register("route/key") on any page function to map it explicitly.
"""
from typing import Callable, Dict
PAGE_REGISTRY: Dict[str, Callable[[], None]] = {}

def register(route: str):
    def deco(fn: Callable[[], None]):
        PAGE_REGISTRY[route] = fn
        return fn
    return deco

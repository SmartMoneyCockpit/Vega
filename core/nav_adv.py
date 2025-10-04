
import streamlit as st
from core.registry import PAGE_REGISTRY
from core.search import search_routes
from core.menu_config import load_menu_config

ICONS = {
    "Cockpit":"🧭",
    "Reports":"📰",
    "Health":"❤️",
    "Health & Journal":"❤️",
    "Journal":"📔",
    "Admin":"⚙️",
    "Analytics":"📊",
    "ETF":"📈",
    "FX":"💱",
    "Alerts":"🚨",
    "Tools":"🧰",
    "Data":"🗃️",
}

def _set_query_param(route: str):
    st.session_state["_route"] = route
    st.query_params.from_dict({"page": route})
    # recents
    lst = st.session_state.get("_recent_routes", [])
    if route in lst:
        lst.remove(route)
    lst.insert(0, route)
    st.session_state["_recent_routes"] = lst[:8]

def _get_initial_route(default_route: str):
    q = st.query_params
    if "page" in q and q["page"]:
        return q["page"]
    return st.session_state.get("_route", default_route)

def _maybe_override_with_fixed(groups_auto):
    cfg = load_menu_config()
    fixed = cfg.get("groups") or []
    return fixed if fixed else groups_auto

def sidebar_menu(groups_auto, default_route="home"):
    groups = _maybe_override_with_fixed(groups_auto)
    st.sidebar.markdown("### Navigation")
    # Search
    q = st.sidebar.text_input("Search pages", key="menu_search", placeholder="Type to filter...")
    recents = st.session_state.get("_recent_routes", [])
    if recents:
        with st.sidebar.expander("Recently used", expanded=False):
            for r in recents:
                if st.button(r, key=f"recent_{r}"):
                    _set_query_param(r)

    # Show accordions
    current = _get_initial_route(default_route)
    chosen = current

    # Optional search results
    if q:
        results = search_routes(groups, q, limit=20)
        if results:
            st.sidebar.caption("Search results")
            for g,l,r in results:
                if st.sidebar.button(f"{l}  ·  {g}", key=f"search_{r}"):
                    chosen = r
        st.sidebar.markdown("---")

    for g in groups:
        title = f"{ICONS.get(g['group'], '')} {g['group']}".strip()
        with st.sidebar.expander(title, expanded=True):
            labels = [it["label"] for it in g["items"]]
            routes = [it["route"] for it in g["items"]]
            try:
                idx = routes.index(current)
            except ValueError:
                idx = 0
            sel = st.radio(
                " ",
                options=list(range(len(labels))),
                format_func=lambda i: labels[i],
                index=idx if idx < len(labels) else 0,
                label_visibility="collapsed",
                key=f"radio_{g['group']}",
            )
            r = routes[sel]
            if r != chosen:
                chosen = r

    _set_query_param(chosen)
    return chosen

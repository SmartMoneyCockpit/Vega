import streamlit as st
from core.registry import register, PAGE_REGISTRY
from core.autoreg import autorun, build_groups
from core.nav_adv import sidebar_menu
from core.breadcrumbs import draw_breadcrumb

st.set_page_config(page_title="Vega Cockpit (Accordion+Search)", layout="wide")

autorun()
groups = build_groups()
if not groups:
    groups = [{"group":"Cockpit","items":[{"label":"Home","route":"home"}]}]
    @register("home")
    def page():
        st.title("Home")
        st.write("No pages discovered under ./pages. Add page modules with a page() function.")

default = groups[0]["items"][0]["route"]
chosen = sidebar_menu(groups, default_route=default)
draw_breadcrumb(chosen)

page_fn = PAGE_REGISTRY.get(chosen)
if page_fn:
    try:
        page_fn()
    except Exception as e:
        st.error(f"Error rendering '{chosen}': {e}")
else:
    st.error(f"No page found for route '{chosen}'.")

st.sidebar.markdown("---")
st.sidebar.caption("Deep link: ?page=<route>")

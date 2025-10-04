
import streamlit as st
from core.registry import PAGE_REGISTRY
from core.search import build_search_index

def page():
    st.title("All Pages")
    idx = build_search_index([{"group":"All","items":[{"label":k, "route":k} for k in sorted(PAGE_REGISTRY.keys())]}])
    for _, label, route in idx:
        st.write(f"- **{label}**  —  `{route}`")

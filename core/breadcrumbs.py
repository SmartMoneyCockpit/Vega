
import streamlit as st

def draw_breadcrumb(route: str):
    segs = [s for s in route.split("/") if s]
    if not segs:
        return
    st.write(" / ".join(segs).title())

import streamlit as st
from .utils import save_snapshot

def export_png_stub():
    st.toast("Export started (stub)...")
    png = b"PNG\x89stub"
    path = save_snapshot(png, outdir="snapshots", prefix="grid-breadth")
    st.success(f"Saved snapshot: {path}")

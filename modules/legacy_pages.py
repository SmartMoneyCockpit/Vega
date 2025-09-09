import os
import streamlit as st

def render():
    st.header("Legacy (v1.x) Pages")
    base_dirs = ["pages", "ui"]
    found = False
    for d in base_dirs:
        if os.path.isdir(d):
            files = [f for f in os.listdir(d) if f.endswith(".py")]
            if files:
                found = True
                st.subheader(f"{d}/")
                for f in sorted(files):
                    st.page_link(f"{d}/{f}", label=f.replace('_',' ').replace('.py',''))
    if not found:
        st.info("No legacy Streamlit pages were found in ./pages or ./ui. If your older app lived elsewhere, keep the folder and .py files, and they will appear here automatically.")

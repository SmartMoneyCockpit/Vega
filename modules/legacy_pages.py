
import os, runpy, types
import streamlit as st

def _label(name:str)->str:
    return name.replace('_',' ').replace('.py','')

def render():
    st.header("Legacy (v1.x) Pages")

    # 1) Proper Streamlit pages: ./pages/*.py -> use page_link (supported)
    if os.path.isdir("pages"):
        files = sorted([f for f in os.listdir("pages") if f.endswith(".py")])
        if files:
            st.subheader("pages/")
            for f in files:
                st.page_link(f"pages/{f}", label=_label(f))

    # 2) Old UI scripts: ./ui/*.py -> run inline (Streamlit only routes from /pages)
    if os.path.isdir("ui"):
        ui_files = sorted([f for f in os.listdir("ui") if f.endswith(".py")])
        if ui_files:
            st.subheader("ui/ (inline runner)")
            choice = st.selectbox("Select a legacy ui script to open", ui_files, key="legacy_ui_choice")
            if st.button("Open legacy ui script"):
                # Temporarily no-op set_page_config so old scripts don't crash
                old_set = st.set_page_config
                try:
                    st.set_page_config = lambda *args, **kwargs: None
                    runpy.run_path(os.path.join("ui", choice), run_name="__main__")
                except SystemExit:
                    pass
                except Exception as e:
                    st.error(f"Error running {choice}: {e}")
                finally:
                    st.set_page_config = old_set

    if (not os.path.isdir("pages")) and (not os.path.isdir("ui")):
        st.info("No legacy pages found. Add scripts under ./pages or ./ui and they will appear here.")

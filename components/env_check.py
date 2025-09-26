
# components/env_check.py
import os
import streamlit as st

REQUIRED = ["IB_HOST", "IB_PORT", "IB_CLIENT_ID"]
def render_env_check():
    st.subheader("Deployment Check")
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        st.error("Missing environment variables: " + ", ".join(missing))
    else:
        st.success("Environment looks good.")
        with st.expander("Current IB vars"):
            st.json({k: os.getenv(k) for k in REQUIRED})


from __future__ import annotations
import os, streamlit as st

def render_heatmap(region: str = "USA"):
    st.markdown(f"### Sector Heatmap — {region}")
    # Toggle between Authenticated vs Public
    mode = st.radio("Data source", ["Authenticated", "Public"], index=0, horizontal=True)
    if mode == "Authenticated":
        # Expect user cookies/session saved by backend; we just embed the private URL if available
        auth_url = os.getenv(f"TV_HEATMAP_{region.upper()}_AUTH_URL", "")
        if auth_url:
            st.components.v1.iframe(auth_url, height=520, scrolling=True)
        else:
            st.info("No authenticated TradingView URL set. Falling back to public.")
            mode = "Public"
    if mode == "Public":
        pub_url = os.getenv(f"TV_HEATMAP_{region.upper()}_PUBLIC_URL", "")
        if pub_url:
            st.components.v1.iframe(pub_url, height=520, scrolling=True)
        else:
            st.warning("Public heatmap URL not configured.")

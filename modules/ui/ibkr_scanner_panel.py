import streamlit as st, os, pandas as pd
from pathlib import Path
def render():
    st.subheader("IBKR Stock Scanner")
    enable = os.getenv("VEGA_ENABLE_IBKR","0") == "1"
    if enable:
        try:
            import ib_insync  # noqa
            st.success("Live IBKR mode is enabled. (ib_insync detected)")
        except Exception:
            enable = False
    if not enable:
        st.info("Live IBKR connect is disabled on this host. Showing latest saved results if available.")
        p = Path("reports/scanner/ibkr_latest.csv")
        if p.exists(): st.dataframe(pd.read_csv(p), use_container_width=True)
        else: st.caption("No saved scan results yet.")

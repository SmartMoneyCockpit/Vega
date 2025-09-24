import os
import pandas as pd
import streamlit as st

def _try_load(url_or_path: str):
    if not url_or_path:
        return pd.DataFrame()
    try:
        if url_or_path.startswith(("http://","https://")):
            return pd.read_csv(url_or_path)
        if os.path.exists(url_or_path):
            return pd.read_csv(url_or_path)
    except Exception as e:
        st.debug(f"vv_panel: failed to load {url_or_path}: {e}")
    return pd.DataFrame()

def vv_panel(region: str, csv_env: str, default_csv: str = ""):
    st.subheader(f"VectorVest Candidates — {region}")
    # Prefer ENV URL, fallback to committed CSV file
    df = _try_load(os.environ.get(csv_env, "").strip())
    if df.empty and default_csv:
        df = _try_load(default_csv)

    if df.empty:
        st.info(f"No VectorVest results yet for {region}. "
                f"Set env var {csv_env} to a CSV URL or commit {default_csv}.")
        return

    pref = ["Symbol","Name","Strategy","Reason","Score","Date","RS","RV","RT"]
    cols = [c for c in pref if c in df.columns] or list(df.columns)[:6]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

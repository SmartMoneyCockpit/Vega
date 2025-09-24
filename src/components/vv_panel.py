import os
import pandas as pd
import streamlit as st

def _load_csv_from_env_or_disk(csv_env: str, default_path: str) -> pd.DataFrame:
    url = os.environ.get(csv_env, "").strip()
    # Try URL first (e.g., Google Sheets published CSV), then local file
    if url:
        try:
            return pd.read_csv(url)
        except Exception as e:
            st.debug(f"vv_panel: failed to load URL {url}: {e}")
    if default_path and os.path.exists(default_path):
        try:
            return pd.read_csv(default_path)
        except Exception as e:
            st.debug(f"vv_panel: failed to load file {default_path}: {e}")
    return pd.DataFrame()

def vv_panel(region: str, csv_env: str, default_csv: str = ""):
    st.subheader(f"VectorVest Candidates — {region}")
    df = _load_csv_from_env_or_disk(csv_env, default_csv)
    if df.empty:
        st.info(f"No VectorVest results yet for {region}.")
        return
    # Prefer common informative columns if available
    pref = ["Symbol","Name","Score","Strategy","Reason","Date","RS","RV","RT"]
    cols = [c for c in pref if c in df.columns]
    if not cols:
        cols = list(df.columns)[:6]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

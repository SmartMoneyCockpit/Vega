import os
from pathlib import Path
import streamlit as st
from modules.utils.data_remote import raw_url, github_page_url

st.set_page_config(page_title="Diagnostics", layout="wide")
st.title("Diagnostics")

repo = os.getenv("VEGA_REPO","(not set)")
branch = os.getenv("VEGA_DATA_BRANCH","(not set)")
st.write({"VEGA_REPO": repo, "VEGA_DATA_BRANCH": branch})

paths = [
    "data/snapshots/na_indices.csv",
    "data/snapshots/eu_indices.csv",
    "data/snapshots/apac_indices.csv",
    "reports/NA/latest.md",
    "reports/EU/latest.md",
    "reports/APAC/latest.md",
]
for p in paths:
    exists_local = Path(p).exists()
    st.write({
        "path": p,
        "local_exists": exists_local,
        "raw_url": raw_url(p),
        "github_url": github_page_url(p)
    })

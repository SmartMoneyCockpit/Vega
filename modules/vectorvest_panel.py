import streamlit as st, json, os, pandas as pd
from .vectorvest_utils import compute_vv_columns
def render():
    st.header("VectorVest Screeners (Live Cache)")
    p = os.path.join("vault","cache","vectorvest_signals.json")
    if not os.path.exists(p):
        st.info("Waiting for server cache…"); return
    data = json.load(open(p,"r",encoding="utf-8"))
    df = compute_vv_columns(pd.DataFrame(data.get("signals", [])), os.path.join("modules","rules","_vega_scores.yaml"))
    st.dataframe(df, use_container_width=True)

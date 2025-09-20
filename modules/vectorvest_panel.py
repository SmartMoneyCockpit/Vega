
import streamlit as st, json, os, pandas as pd
from .vectorvest_utils import compute_vv_columns

def render():
    st.header("VectorVest Screeners (Live Cache)")
    p = os.path.join("vault","cache","vectorvest_signals.json")
    if not os.path.exists(p):
        st.info("Waiting for server cache…"); return
    try:
        data = json.load(open(p,"r",encoding="utf-8"))
    except Exception as e:
        st.error(f"Failed to read {p}: {e}"); return
    df = compute_vv_columns(pd.DataFrame(data.get("signals", [])), os.path.join("modules","rules","_vega_scores.yaml"))
    if df is None or df.empty:
        st.info("No rows to display yet (check your signals)."); return
    st.dataframe(df, use_container_width=True, height=600)

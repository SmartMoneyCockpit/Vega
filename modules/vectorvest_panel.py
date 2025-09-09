import streamlit as st, json, os, pandas as pd
def render():
    st.header("VectorVest Screeners (Live Cache)")
    p = os.path.join("vault","cache","vectorvest_signals.json")
    if not os.path.exists(p):
        st.info("Waiting for server cache…"); return
    data = json.load(open(p,"r",encoding="utf-8"))
    df = pd.DataFrame(data.get("signals", []))
    st.dataframe(df, use_container_width=True)

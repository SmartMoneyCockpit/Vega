import streamlit as st, json, os, pandas as pd
def render():
    st.header("ETF Tactical (Server-fed)")
    p = os.path.join("vault","cache","etf_tactical.json")
    if not os.path.exists(p):
        st.info("Waiting for server cache…"); return
    data = json.load(open(p,"r",encoding="utf-8"))
    st.dataframe(pd.DataFrame(data.get("signals", [])), use_container_width=True)

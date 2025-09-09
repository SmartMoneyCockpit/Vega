import streamlit as st, os, json, pandas as pd
def render():
    st.header("Guardrails Gauges")
    p = os.path.join("vault","cache","guardrails.json")
    if not os.path.exists(p):
        st.info("No guardrails file yet."); return
    data = json.load(open(p,"r",encoding="utf-8"))
    exp = data.get("exposure",{}); alerts = data.get("alerts",[])
    st.subheader("Exposure")
    df = pd.DataFrame([{"Sector":k,"Weight":v} for k,v in exp.items()])
    st.dataframe(df, use_container_width=True)
    st.subheader("Alerts")
    if alerts: st.write(alerts)
    else: st.success("No alerts")

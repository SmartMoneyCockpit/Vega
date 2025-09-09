import streamlit as st, os, json, pandas as pd
def _j(name):
    p = os.path.join("vault","cache",name)
    return json.load(open(p,"r",encoding="utf-8")) if os.path.exists(p) else None
def render():
    st.header("Market Breadth Dashboard")
    adv = (_j("breadth_adv.json") or {}).get("value","—")
    dec = (_j("breadth_dec.json") or {}).get("value","—")
    hilo = (_j("breadth_hilo.json") or {}).get("value","—")
    c1,c2,c3 = st.columns(3)
    c1.metric("Advancers", adv); c2.metric("Decliners", dec); c3.metric("New Highs/Lows", hilo)
    rows = (_j("breadth_sector.json") or {}).get("rows", [])
    if not rows:
        rows = [["Technology",52,0.98],["Financials",48,0.92],["Energy",55,1.04]]
    st.dataframe(pd.DataFrame(rows, columns=["Sector","% Advancing","RS"]), use_container_width=True)

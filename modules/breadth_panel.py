# modules/breadth_panel.py
import streamlit as st
import pandas as pd
from tools.breadth import get_breadth

def render():
    st.header("Market Breadth Dashboard")
    data = get_breadth()
    st.caption(f"Breadth as of {data['as_of_utc']} (source: {data.get('source')})")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Advancers", data.get("advancers", 0))
    c2.metric("Decliners", data.get("decliners", 0))
    c3.metric("New Highs", data.get("newHighs", 0))
    c4.metric("New Lows", data.get("newLows", 0))

    sectors = pd.DataFrame([
        {"Sector": s.get("name"), "RS": s.get("rs"), "% Advancing": s.get("advPct")} 
        for s in data.get("by_sector", [])
    ])
    st.dataframe(sectors, use_container_width=True)
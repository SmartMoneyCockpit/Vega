import streamlit as st
import pandas as pd
from modules.utils.data_remote import load_csv_auto
from modules.utils.tv_links import tv_symbol_url

st.set_page_config(page_title="Screener — Text", layout="wide")
st.title("Screener — Text")

df = load_csv_auto("data/screener.csv")
if df.empty:
    st.info("No screener data yet. Place a CSV at data/screener.csv on the vega-data branch.")
else:
    st.write("### Results")
    for _, r in df.iterrows():
        sym = str(r.get("symbol","")).strip()
        cols = st.columns([2,1,1,1,2])
        with cols[0]:
            st.markdown(f"[**{sym}** ↗]({tv_symbol_url(sym)})", unsafe_allow_html=True)
        with cols[1]: st.write(r.get("price","—"))
        with cols[2]: st.write(r.get("rs","—"))
        with cols[3]: st.write(r.get("grade","—"))
        with cols[4]: st.write(r.get("decision","—"))
        with st.expander(f"A-to-Z Quickview — {sym}"):
            st.write({
                "Macro/Sector": r.get("macro",""),
                "Fundamentals": r.get("fundamentals",""),
                "MTF Technicals": r.get("technicals",""),
                "Options (POP 60%, 21–90 DTE)": r.get("options",""),
                "Risk/Targets": r.get("risk",""),
                "Contras/Hedges": r.get("contras",""),
                "Earnings Window": r.get("earnings",""),
                "Tariff/USMCA": r.get("tariff",""),
                "Notes": r.get("notes","")
            })

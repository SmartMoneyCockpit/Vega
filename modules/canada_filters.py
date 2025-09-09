import streamlit as st, pandas as pd

def render():
    st.header("Canada Filters (Smart Money)")
    st.caption("Tariff Grade 🟢🟠🔴 • USMCA • Smart Money Grade (📈/📉) • Action Plan (Buy/Hold/Avoid)")
    df = pd.DataFrame([
        {"Ticker":"CPD.TO","Name":"iShares Prefs","TariffGrade":"🟢","USMCA":"Protected","SmartMoneyGrade":"📈","ActionPlan":"HOLD"},
        {"Ticker":"ZPR.TO","Name":"BMO Ladder Prefs","TariffGrade":"🟢","USMCA":"Protected","SmartMoneyGrade":"📈","ActionPlan":"HOLD"},
        {"Ticker":"HPR.TO","Name":"Global X Active Prefs","TariffGrade":"🟢","USMCA":"Protected","SmartMoneyGrade":"📈","ActionPlan":"HOLD"}
    ])
    st.dataframe(df, use_container_width=True)

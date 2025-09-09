import streamlit as st, pandas as pd

def render():
    st.header('AI Trade Quality Scorecard')
    st.dataframe(pd.DataFrame([{'Ticker':'SQQQ','Grade':'A-','Notes':'Risk-off candidate'}]), use_container_width=True)

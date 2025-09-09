import streamlit as st

def render():
    st.header('Backtest Mode')
    st.toggle('Enable Backtest Mode', value=False)

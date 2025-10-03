
import streamlit as st, pandas as pd
from app_auth import login_gate
if not login_gate():
    pass

st.set_page_config(page_title="RS Dashboard", layout="wide")
st.title("Relative Strength Momentum Dashboard (Skeleton)")

def get_rs():
    if 'rs_df' in st.session_state and not st.session_state['rs_df'].empty:
        return st.session_state['rs_df']
    return pd.DataFrame({
        'Bucket': ['USA','Canada','Mexico','LATAM ex-MX','Tech','Industrials','Materials','Financials','Staples'],
        'RS Trend': ['🟡','🟡','🟢','🟡','🟠','🟢','🟡','🟡','🟢']
    })

st.dataframe(get_rs(), use_container_width=True)
st.info("Wire to your internal DB later; this page reads st.session_state['rs_df'] if present.")

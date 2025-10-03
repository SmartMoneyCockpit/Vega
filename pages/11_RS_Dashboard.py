import streamlit as st
from app_auth import login_gate
if not login_gate(): pass
from data_bridge import get_rs_df

st.set_page_config(page_title="RS Dashboard", layout="wide")
st.title("Relative Strength Momentum Dashboard")
st.dataframe(get_rs_df(), use_container_width=True)
st.info("This reads db_adapter.load_rs() if available; else session_state; else demo.")

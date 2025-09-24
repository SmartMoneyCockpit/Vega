import streamlit as st
_KEY = "_tv_symbol"
def push_symbol(symbol: str):
    st.session_state[_KEY] = symbol
def get_symbol(default: str = "SPY") -> str:
    return st.session_state.get(_KEY, default)

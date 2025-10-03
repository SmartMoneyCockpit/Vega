import os, streamlit as st

def login_gate():
    user = os.getenv("BASIC_AUTH_USER", "")
    pwd  = os.getenv("BASIC_AUTH_PASS", "")
    if not user or not pwd:
        return True  # no gate configured

    if "auth_ok" not in st.session_state:
        st.session_state.auth_ok = False

    if st.session_state.auth_ok:
        return True

    st.title("Vega Cockpit — Sign In")
    u = st.text_input("Username", key="auth_u")
    p = st.text_input("Password", type="password", key="auth_p")
    if st.button("Sign in"):
        if u == user and p == pwd:
            st.session_state.auth_ok = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()
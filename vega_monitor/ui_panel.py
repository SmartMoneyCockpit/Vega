import streamlit as st
from time import time
st.subheader("Vega Resource Health (ACI)")
st.caption("Shields before swords · live resource snapshot")
st.info("Runtime monitor active. Defensive Mode will auto-gate if thresholds breach. Check alerts for entries/exits.")
st.write(f"Last refresh: {int(time())}")

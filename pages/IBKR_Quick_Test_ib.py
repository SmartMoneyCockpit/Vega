# pages/IBKR_Quick_Test_ib.py
import requests, streamlit as st
from config.ib_bridge_client import get_bridge_url, get_bridge_api_key

BRIDGE_URL = get_bridge_url()
API_KEY = get_bridge_api_key()

st.title("IBKR Quick Test (ib_insync)")

if st.button("Run Connectivity Test"):
    out = {}
    try:
        out["/health"] = requests.get(f"{BRIDGE_URL}/health", timeout=4).json()
    except Exception as e:
        out["/health"] = f"ERROR: {e}"

    try:
        out["/status"] = requests.get(f"{BRIDGE_URL}/status",
                                      headers={"x-api-key": API_KEY}, timeout=6).json()
    except Exception as e:
        out["/status"] = f"ERROR: {e}"

    try:
        out["/price AAPL"] = requests.get(f"{BRIDGE_URL}/price/AAPL",
                                          params={"snapshot": "true"},
                                          headers={"x-api-key": API_KEY}, timeout=6).json()
    except Exception as e:
        out["/price AAPL"] = f"ERROR: {e}"

    st.json(out)
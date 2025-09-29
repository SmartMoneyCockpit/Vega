
import streamlit as st, httpx
from config.ib_bridge_client import get_bridge_url, default_headers

st.header("IBKR Ticker (Bridge)")
base = get_bridge_url().rstrip("/")
symbol = st.text_input("Symbol", value="SPY")

if st.button("Fetch last price"):
    try:
        r = httpx.get(f"{base}/price/{symbol}", headers=default_headers(), timeout=8.0)
        r.raise_for_status()
        st.json(r.json())
    except httpx.HTTPStatusError as e:
        st.error(f"Bridge error {e.response.status_code}: {e.response.text[:400]}")
    except httpx.RequestError as e:
        st.error(f"Timed out / network error: {e}")

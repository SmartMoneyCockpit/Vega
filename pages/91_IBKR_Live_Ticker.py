# pages/91_IBKR_Live_Ticker.py
import os, time, requests, streamlit as st

st.set_page_config(page_title="IBKR Live Ticker", layout="wide")
st.title("IBKR Live Ticker")

BRIDGE_URL = os.getenv("IBKR_BRIDGE_URL", "http://127.0.0.1:8088")
API_KEY    = os.getenv("IBKR_API_KEY", os.getenv("BRIDGE_API_KEY", ""))

def fetch_quote(sym: str):
    try:
        r = requests.get(
            f"{BRIDGE_URL}/price/{sym}",
            headers={"x-api-key": API_KEY},
            timeout=5
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# --- User controls
symbols = st.text_input("Symbols (comma separated)", "SPY,AAPL,MSFT").upper().split(",")
refresh = st.slider("Refresh every (seconds)", 2, 30, 5)

# --- Live loop
placeholder = st.empty()
while True:
    with placeholder.container():
        cols = st.columns(len(symbols))
        for i, sym in enumerate(symbols):
            sym = sym.strip()
            if not sym:
                continue
            data = fetch_quote(sym)
            if "error" in data:
                cols[i].error(f"{sym}: {data['error']}")
            else:
                last = data.get("last")
                bid  = data.get("bid")
                ask  = data.get("ask")
                cols[i].metric(sym, f"{last}", delta=f"Bid {bid} / Ask {ask}")
    time.sleep(refresh)

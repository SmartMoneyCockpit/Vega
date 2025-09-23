# pages/90_IBKR_Quick_Test.py
import os, time, requests, streamlit as st

st.set_page_config(page_title="IBKR Quick Test", layout="wide")
st.title("IBKR Quick Test")

BRIDGE_URL = os.getenv("IBKR_BRIDGE_URL", "http://127.0.0.1:8088")
API_KEY    = os.getenv("IBKR_API_KEY",   os.getenv("BRIDGE_API_KEY", ""))

@st.cache_data(ttl=5.0, show_spinner=False)
def fetch_health():
    try:
        r = requests.get(f"{BRIDGE_URL}/health", timeout=3)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=2.0, show_spinner=False)
def fetch_price(sym: str):
    try:
        r = requests.get(
            f"{BRIDGE_URL}/price/{sym}",
            headers={"x-api-key": API_KEY},
            timeout=4,
        )
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)

# ---- Status row
col1, col2, col3 = st.columns([2,2,3])
with col1:
    st.caption("Bridge URL")
    st.code(BRIDGE_URL, language="bash")
with col2:
    st.caption("API Key present?")
    st.write("✅ yes" if bool(API_KEY) else "❌ missing")

health, herr = fetch_health()
with col3:
    st.caption("Bridge / Gateway Status")
    if herr:
        st.error(f"Health error: {herr}")
    elif health:
        st.success(f"Connected: {health.get('connected')}  | Host: {health.get('host')}:{health.get('port')}")
    else:
        st.warning("No health data")

st.divider()

# ---- Quote form
sym = st.text_input("Symbol", value="SPY").strip().upper()
if st.button("Get Quote", type="primary") or sym:
    data, err = fetch_price(sym)
    if err:
        st.error(err)
    elif data:
        last = data.get("last")
        bid  = data.get("bid")
        ask  = data.get("ask")
        close= data.get("close")
        t    = data.get("time","")
        st.metric("Last", f"{last if last is not None else '—'}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Bid",  f"{bid if bid is not None else '—'}")
        c2.metric("Ask",  f"{ask if ask is not None else '—'}")
        c3.metric("Prev Close", f"{close if close is not None else '—'}")
        st.caption(f"Timestamp: {t}")
        st.info("If values are None, ensure market data permissions and Gateway subscriptions are active.")

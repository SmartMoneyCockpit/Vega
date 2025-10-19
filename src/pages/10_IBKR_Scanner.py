import os, json, time, streamlit as st, httpx
from vega.bridge_client import quote
import os, pathlib, sys
try:
    from config.ib_bridge_client import get_bridge_url, get_bridge_api_key  # type: ignore
except Exception:
    def get_bridge_url() -> str:
        return (os.getenv("IBKR_BRIDGE_URL") or os.getenv("IB_BRIDGE_URL") or "").rstrip("/")
    def get_bridge_api_key() -> str:
        return os.getenv("IB_BRIDGE_API_KEY") or os.getenv("BRIDGE_API_KEY") or os.getenv("IBKR_BRIDGE_API_KEY") or ""


st.set_page_config(page_title='IBKR Scanner (Bridge)', layout='wide')
st.title('IBKR Stock Scanner — Bridge Mode (server decides delayed/live)')

base = get_bridge_url()
api_key = get_bridge_api_key()
headers = {'x-api-key': api_key} if api_key else {}
st.caption(f"Bridge: {base} (auth={'yes' if api_key else 'no'})")

st.subheader('Single symbol snapshot')
c1, c2 = st.columns([1,3])
with c1:
    sym = st.text_input("Symbol", "SPY").strip().upper()
    go = st.button("Get Last Price", use_container_width=True)
with c2:
    if go and sym:
        try:
            r = httpx.get(f"{base}/quote?symbol={sym}}", headers=headers, timeout=6.0)
            r.raise_for_status()
            st.json(r.json())
        except Exception as e:
            st.error(f"{e}")

st.divider()
st.subheader("Batch snapshot (approved_tickers.json)")
path = "data/approved_tickers.json"
approved = []
if os.path.exists(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        approved = (payload.get("north_america") or payload.get("tickers") or [])[:200]
    except Exception as e:
        st.error(f"Could not load {path}: {e}")

limit = st.slider("Batch size", min_value=10, max_value=200, value=min(50, len(approved) or 50), step=10)
if st.button("Fetch batch prices", use_container_width=True, disabled=not approved):
    rows = []
    with st.spinner("Fetching last prices..."):
        for s in approved[:limit]:
            try:
                data = quote(s)
                rows.append({"symbol": s, **data})
            except Exception as e:
                rows.append({"symbol": s, "error": str(e)})
            time.sleep(0.05)
    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
elif not approved:
    st.info('No approved_tickers.json found; add one under data/approved_tickers.json with a "north_america" list.')

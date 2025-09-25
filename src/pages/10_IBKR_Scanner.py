import os, json, time
import streamlit as st
import httpx
from config.ib_bridge_client import get_bridge_url, get_bridge_api_key

st.set_page_config(page_title='IBKR Scanner (Bridge)', layout='wide')
st.title('IBKR Stock Scanner — Bridge Mode (Delayed or Live set on server)')

base = get_bridge_url()
api_key = get_bridge_api_key()
headers = {'x-api-key': api_key} if api_key else {}
st.caption(f'Bridge: {base} (auth={'yes' if api_key else 'no'})')

st.subheader('Single symbol snapshot')
c1, c2 = st.columns([1,3])
with c1:
    sym = st.text_input('Symbol', 'AAPL').strip().upper()
with c2:
    if st.button('Get snapshot'):
        try:
            r = httpx.get(f'{base}/price/{sym}', headers=headers, timeout=8.0)
            r.raise_for_status()
            st.success('OK')
            st.json(r.json())
        except Exception as e:
            st.error(str(e))

st.divider()
st.subheader('Batch snapshot (Approved tickers)')
DATA_DIR = os.getenv('DATA_DIR', 'data')
APPROVED_JSON = os.path.join(DATA_DIR, 'approved_tickers.json')

approved = []
try:
    if os.path.exists(APPROVED_JSON):
        import json as _json
        with open(APPROVED_JSON) as f:
            approved = _json.load(f).get('north_america', [])
except Exception:
    approved = []

limit = st.slider('Max symbols', min_value=5, max_value=50, value=min(20, len(approved) or 20))
if st.button('Run batch') and approved:
    rows = []
    with st.spinner('Fetching last prices...'):
        for sym in approved[:limit]:
            try:
                r = httpx.get(f'{base}/price/{sym}', headers=headers, timeout=6.0)
                r.raise_for_status()
                data = r.json()
                rows.append({'symbol': sym, **data})
            except Exception as e:
                rows.append({'symbol': sym, 'error': str(e)})
            time.sleep(0.05)
    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
elif not approved:
    st.info('No approved_tickers.json found; add one under data/approved_tickers.json with a "north_america" list.')
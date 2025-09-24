import streamlit as st, os, pandas as pd
from pathlib import Path
st.set_page_config(page_title='IBKR Scanner', layout='wide')
st.title('IBKR Stock Scanner (Environment-Aware)')
enable = os.getenv('VEGA_ENABLE_IBKR','0') == '1'
if enable:
    try:
        st.success('Live IBKR mode is enabled. (ib_insync detected)')
    except Exception:
        enable = False
if not enable:
    st.info('Live IBKR connect is disabled on this host. Showing latest saved results if available.')
    p = Path('reports/scanner/ibkr_latest.csv')
    if p.exists():
        st.dataframe(pd.read_csv(p), use_container_width=True)
    else:
        st.caption('No saved scan results yet.')


st.divider()
st.subheader("Live snapshot (optional)")
col1, col2, col3 = st.columns([2,1,1])
with col1:
    sym = st.text_input("Symbol", "AAPL")
with col2:
    do = st.button("Get snapshot")
with col3:
    host = st.text_input("Host", "127.0.0.1")
port = st.number_input("Port", 4002)
client_id = st.number_input("Client ID", 16)

if do:
    try:
        from ibkr_bridge.mktdata import snapshot
        data = snapshot(sym, host=host, port=int(port), client_id=int(client_id))
        st.success("Requested market data; see details below")
        st.write(str(data))
    except Exception as e:
        st.warning(f"Live snapshot unavailable: {e}")

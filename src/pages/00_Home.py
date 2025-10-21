import streamlit as st

st.set_page_config(page_title='Vega Cockpit', layout='wide')
st.title('Vega Cockpit – Home')

st.write('Quick links:')

st.page_link('pages/01_North_America_Text_Dashboard.py', label='🌎 North America')
st.page_link('pages/02_Europe_Text_Dashboard.py',       label='🌍 Europe')
st.page_link('pages/02_APAC_Text_Dashboard.py',         label='🌏 APAC')
st.page_link('pages/10_IBKR_Scanner.py',                label='🧪 IBKR Scanner')
st.page_link('pages/10_TradingView_Bridge.py',          label='🔗 TradingView Bridge')
st.page_link('pages/99_Diagnostics.py',                 label='🧰 Diagnostics')


# --- Vega Risk Tile (EODHD) ---------------------------------------------------
import sys, pathlib
_here = pathlib.Path(__file__).resolve()
sys.path.append(str(_here.parents[1]))  # ensure src is importable

try:
    from components.risk_tile import render as render_risk_tile
    import streamlit as st
    st.markdown("---")
    render_risk_tile()
except Exception as _ex:
    import streamlit as st
    st.warning(f"Risk Tile not available: {_ex}")

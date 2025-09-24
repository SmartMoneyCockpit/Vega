# app.py
import streamlit as st
import os, json, datetime, sys
from vega.utils.slug_guard import scan_pages_for_slug_collisions, list_pages_and_slugs, assert_unique_page_links

# Boot-time guard
collisions = scan_pages_for_slug_collisions("pages")
if collisions:
    lines = "\n".join(f"  /{k} -> {', '.join(v)}" for k,v in sorted(collisions.items()))
    sys.exit("[BOOT BLOCKED] Duplicate page URL paths detected:\n" + lines)

# Startup log (optional)
st.session_state.setdefault("_vega_pages_logged", False)
if not st.session_state._vega_pages_logged:
    st.session_state._vega_pages_logged = True
    print("PAGES", json.dumps(list_pages_and_slugs("pages")))

st.set_page_config(page_title='Vega Cockpit', layout='wide')
st.title('Vega Cockpit')

# Grouped links (match files present)
CORE = [
    ('pages/00_Home.py','🏠 Home'),
    ('pages/10_IBKR_Scanner.py','🧪 IBKR Scanner'),
    ('pages/10_TradingView_Bridge.py','🔗 TradingView Bridge'),
]

MARKETS = [
    ('pages/01_North_America_Text_Dashboard.py','🌎 North America'),
    ('pages/02_Europe_Text_Dashboard.py','🌍 Europe'),
    ('pages/02_APAC_Text_Dashboard.py','🌏 APAC'),
]

TOOLS = [
    ('pages/99_Diagnostics.py','🧰 Diagnostics'),
]

ALL = CORE + MARKETS + TOOLS
assert_unique_page_links([p for p,_ in ALL])

st.subheader('Core')
for p, label in CORE:
    st.page_link(p, label=label)
st.subheader('Markets')
for p, label in MARKETS:
    st.page_link(p, label=label)
st.subheader('Tools')
for p, label in TOOLS:
    st.page_link(p, label=label)

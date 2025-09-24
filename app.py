# app.py
import streamlit as st
import os, re, sys, json, datetime
from vega.utils.slug_guard import (
    infer_slug_from_filename,
    scan_pages_for_slug_collisions,
    assert_unique_page_links,
    list_pages_and_slugs,
)

# ---------- Boot-time safety checks & startup log ----------
os.makedirs("logs", exist_ok=True)
pages_dir = "pages"
collisions = scan_pages_for_slug_collisions(pages_dir)
if collisions:
    lines = "\n".join(f"  /{slug} -> {', '.join(files)}" for slug, files in sorted(collisions.items()))
    msg = "[BOOT BLOCKED] Duplicate page URL paths detected:\n" + lines
    with open("logs/startup_checks.log", "a", encoding="utf-8") as fh:
        fh.write(f"{datetime.datetime.utcnow().isoformat()}Z  {msg}\n")
    sys.exit(msg)

# optional: print page/slug table to logs each start
page_table = list_pages_and_slugs(pages_dir)
with open("logs/startup_checks.log", "a", encoding="utf-8") as fh:
    fh.write(f"{datetime.datetime.utcnow().isoformat()}Z  PAGES={json.dumps(page_table)}\n")

# ---------- Streamlit UI ----------
st.set_page_config(page_title='Vega Cockpit', layout='wide')
st.title('Vega Cockpit')

# Explicit, future-proof nav links (grouped). Ensure targets are unique:
CORE = [
    ('pages/00_Home.py',               '🏠 Home'),
    ('pages/096_IBKR_Ticker_ib.py',    '⏱️ IBKR Ticker (ib_insync)'),
    ('pages/097_IBKR_Quick_Test_ib.py','🧪 IBKR Quick Test (ib_insync)'),
    ('pages/098_IBKR_Order_Ticket_ib.py','🧾 IBKR Order Ticket (ib_insync)'),
]
MARKETS = [
    ('pages/101_North_America.py',     '🌎 North America'),
    ('pages/102_Europe.py',            '🌍 Europe'),
    ('pages/103_APAC.py',              '🌏 APAC'),
]
STATUS = [
    ('pages/095_IB_Feed_Status.py',    '📡 IB Feed Status'),
]
EXTRAS = [
    ('pages/05_TradingView_Charts.py', '📊 TradingView Charts'),
    ('pages/06_Vega_Native_Chart.py',  '📈 Vega Native Chart'),
    ('pages/404_Not_Found.py',         '🚧 404 / Help'),
]

ALL_LINKS = CORE + MARKETS + STATUS + EXTRAS
assert_unique_page_links([p for p, _ in ALL_LINKS])  # fast fail if a path is linked twice

st.subheader("Core")
for path, label in CORE:
    st.page_link(path, label=label)

st.subheader("Markets")
for path, label in MARKETS:
    st.page_link(path, label=label)

st.subheader("Status")
for path, label in STATUS:
    st.page_link(path, label=label)

with st.expander("Extras"):
    for path, label in EXTRAS:
        st.page_link(path, label=label)

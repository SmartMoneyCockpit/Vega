# src/app.py
import streamlit as st
import os, sys, json, datetime
from vega.utils.slug_guard import (
    scan_pages_for_slug_collisions,
    list_pages_and_slugs,
    assert_unique_page_links,
)

# ---- paths ----
BASE_DIR = os.path.dirname(__file__)
PAGES_DIR = "pages"                       # what Streamlit expects
PAGES_ABS = os.path.join(BASE_DIR, PAGES_DIR)
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# ---------- Boot-time safety checks & startup log ----------
os.makedirs(LOGS_DIR, exist_ok=True)

collisions = scan_pages_for_slug_collisions(PAGES_ABS)
if collisions:
    lines = "\n".join(f"  /{slug} -> {', '.join(files)}" for slug, files in sorted(collisions.items()))
    msg = "[BOOT BLOCKED] Duplicate page URL paths detected:\n" + lines
    with open(os.path.join(LOGS_DIR, "startup_checks.log"), "a", encoding="utf-8") as fh:
        fh.write(f"{datetime.datetime.utcnow().isoformat()}Z  {msg}\n")
    sys.exit(msg)

# Log page/slug table once when the app starts
st.session_state.setdefault("_vega_pages_logged", False)
if not st.session_state._vega_pages_logged:
    st.session_state._vega_pages_logged = True
    page_table = list_pages_and_slugs(PAGES_ABS)
    with open(os.path.join(LOGS_DIR, "startup_checks.log"), "a", encoding="utf-8") as fh:
        fh.write(f"{datetime.datetime.utcnow().isoformat()}Z  PAGES={json.dumps(page_table)}\n")

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Vega Cockpit", layout="wide")
st.title("Vega Cockpit – Home")

# ----- helpers -----
def exists_in_pages(name: str) -> bool:
    return os.path.exists(os.path.join(PAGES_ABS, name))

def first_existing(*names):
    for n in names:
        if exists_in_pages(n):
            return f"{PAGES_DIR}/{n}"
    return None

# Explicit, future-proof nav links (grouped). Ensure targets are unique:
CORE = [
    (f"{PAGES_DIR}/00_Home.py",                  "🏠 Home"),
    (f"{PAGES_DIR}/096_IBKR_Ticker_ib.py",       "⏱️ IBKR Ticker (ib_insync)"),
    (f"{PAGES_DIR}/097_IBKR_Quick_Test_ib.py",   "🧪 IBKR Quick Test (ib_insync)"),
    (f"{PAGES_DIR}/098_IBKR_Order_Ticket_ib.py", "🧾 IBKR Order Ticket (ib_insync)"),
]

# --- Markets links (auto-detect common filenames) ---
MARKETS = []
na = first_existing(
    "101_North_America.py",
    "01_North_America_Text_Dashboard.py",
    "North_America_Text_Dashboard.py",
)
if na:
    MARKETS.append((na, "🌎 North America"))

eu = first_existing(
    "102_Europe.py",
    "02_Europe_Text_Dashboard.py",
    "Europe_Text_Dashboard.py",
)
if eu:
    MARKETS.append((eu, "🌍 Europe"))

apac = first_existing(
    "103_APAC.py",
    "03_APAC.py",
    "02_APAC_Text_Dashboard.py",
    "APAC_Text_Dashboard.py",
)
if apac:
    MARKETS.append((apac, "🌏 APAC"))

STATUS = [
    (f"{PAGES_DIR}/095_IB_Feed_Status.py", "📡 IB Feed Status"),
]

EXTRAS = [
    (f"{PAGES_DIR}/05_TradingView_Charts.py", "📊 TradingView Charts"),
    (f"{PAGES_DIR}/06_Vega_Native_Chart.py", "📈 Vega Native Chart"),
    (f"{PAGES_DIR}/404_Not_Found.py",        "🚧 404 / Help"),
]

ALL_LINKS = CORE + MARKETS + STATUS + EXTRAS
assert_unique_page_links([p for p, _ in ALL_LINKS])  # fast-fail if a path is linked twice

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

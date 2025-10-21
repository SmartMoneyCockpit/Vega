# src/app.py (home + env/IB panels + safe page links)

import os, sys, json, datetime
import streamlit as st

# ---- Vega grouped nav guard (auto-added) ----
from pathlib import Path
import os, sys
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PAGES_DIR = ROOT / "pages"  # canonical pages dir
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
# ---------------------------------------------

from vega.utils.slug_guard import (
    scan_pages_for_slug_collisions,
    list_pages_and_slugs,
    assert_unique_page_links,
)

# ---- optional components ----
try:
    from components.ib_status import status_badge, render_ib_panel
except Exception:
    status_badge = render_ib_panel = None

try:
    from components.env_check import render_env_check
except Exception:
    render_env_check = None

# ---- NEW: bridge (VPS) client hooks ----
BRIDGE_URL = os.getenv("BRIDGE_URL", "").rstrip("/")
try:
    from bridge_client import bridge_connect, bridge_health, bridge_scan, BridgeError  # type: ignore
except Exception:
    # Soft fallback if helper module not present yet
    def _missing(*args, **kwargs):
        raise RuntimeError("bridge_client.py not found in repo. Add it to enable scanner bridge.")
    BridgeError = RuntimeError  # type: ignore
    bridge_connect = bridge_health = bridge_scan = _missing  # type: ignore

# ---- paths / bootstrap ----
BASE_DIR  = os.path.dirname(__file__)
PAGES_DIR = "pages"                             # Streamlit expects this folder next to src/app.py
PAGES_ABS = os.path.join(BASE_DIR, PAGES_DIR)
LOGS_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Block duplicate slugs
collisions = scan_pages_for_slug_collisions(PAGES_ABS)
if collisions:
    lines = "\n".join(f"  /{slug} -> {', '.join(files)}" for slug, files in sorted(collisions.items()))
    msg = "[BOOT BLOCKED] Duplicate page URL paths detected:\n" + lines
    with open(os.path.join(LOGS_DIR, "startup_checks.log"), "a", encoding="utf-8") as fh:
        fh.write(f"{datetime.datetime.utcnow().isoformat()}Z  {msg}\n")
    sys.exit(msg)

# Log discovered pages once per session
st.session_state.setdefault("_vega_pages_logged", False)
if not st.session_state["_vega_pages_logged"]:
    st.session_state["_vega_pages_logged"] = True
    table = list_pages_and_slugs(PAGES_ABS)
    with open(os.path.join(LOGS_DIR, "startup_checks.log"), "a", encoding="utf-8") as fh:
        fh.write(f"{datetime.datetime.utcnow().isoformat()}Z  PAGES={json.dumps(table)}\n")

# ---- helpers ----
def exists_in_pages(name: str) -> bool:
    return os.path.exists(os.path.join(PAGES_ABS, name))

def first_existing(*names: str):
    for n in names:
        if exists_in_pages(n):
            return f"{PAGES_DIR}/{n}"
    return None

# ---- UI header ----
st.set_page_config(page_title="Vega Cockpit", layout="wide")
if status_badge:
    status_badge()
st.title("Vega Cockpit – Home")

# ---- link buckets ----
CORE = []
for file, label in [
    ("00_Home.py",                  "🏠 Home"),
    ("096_IBKR_Ticker_ib.py",      "⏱️ IBKR Ticker (ib_insync)"),
    ("097_IBKR_Quick_Test_ib.py",  "🧪 IBKR Quick Test (ib_insync)"),
    ("098_IBKR_Order_Ticket_ib.py","🧾 IBKR Order Ticket (ib_insync)"),
    ("01_Scanner_OnDemand.py",     "🔎 Scanner OnDemand"),
]:
    if exists_in_pages(file):
        CORE.append((f"{PAGES_DIR}/{file}", label))

MARKETS = []
na = first_existing("101_North_America.py", "01_North_America_Text_Dashboard.py", "North_America_Text_Dashboard.py")
if na: MARKETS.append((na, "🌎 North America"))
eu = first_existing("102_Europe.py", "02_Europe_Text_Dashboard.py", "Europe_Text_Dashboard.py")
if eu: MARKETS.append((eu, "🌍 Europe"))
apac = first_existing("103_APAC.py", "03_APAC.py", "02_APAC_Text_Dashboard.py", "APAC_Text_Dashboard.py")
if apac: MARKETS.append((apac, "🌏 APAC"))

STATUS = []
if exists_in_pages("095_IB_Feed_Status.py"):
    STATUS.append((f"{PAGES_DIR}/095_IB_Feed_Status.py", "📡 IB Feed Status"))
if exists_in_pages("Logs_IBKR.py"):
    STATUS.append((f"{PAGES_DIR}/Logs_IBKR.py", "🪵 IBKR Logs"))

EXTRAS = []
if exists_in_pages("05_TradingView_Charts.py"):
    EXTRAS.append((f"{PAGES_DIR}/05_TradingView_Charts.py", "📊 TradingView Charts"))
if exists_in_pages("06_Vega_Native_Chart.py"):
    EXTRAS.append((f"{PAGES_DIR}/06_Vega_Native_Chart.py", "📈 Vega Native Chart"))
nf = first_existing("404_Not_Found.py", "Not_Found.py", "404.py", "Help.py")
if nf: EXTRAS.append((nf, "🚧 404 / Help"))

ALL_LINKS = CORE + MARKETS + STATUS + EXTRAS
assert_unique_page_links([p for p, _ in ALL_LINKS])

# ---- optional panels ----
if render_env_check:
    with st.container():
        render_env_check()

if render_ib_panel:
    with st.container():
        render_ib_panel()

# ---- NEW: Bridge (VPS) Status panel on Home ----
with st.container():
    st.subheader("Bridge (VPS) Status")
    cols = st.columns([1,1,2])
    with cols[0]:
        if BRIDGE_URL:
            st.success(f"URL: {BRIDGE_URL}")
        else:
            st.warning("BRIDGE_URL not set")
    with cols[1]:
        # Never show the token value; just indicate presence.
        st.info("Token: ✅ set" if os.getenv("BRIDGE_TOKEN") else "Token: ⚠️ missing")
    ok_health = ok_connect = False
    try:
        h = bridge_health()
        ok_health = True
        st.caption(f"Health: {h}")
    except Exception as e:
        st.error(f"Health check failed: {e}")
    try:
        c = bridge_connect()
        ok_connect = True
        st.caption(f"Connect: {c}")
    except Exception as e:
        st.error(f"Connect failed: {e}")

    # Quick test scan button (safe; no secrets printed)
    if ok_connect:
        if st.button("Run Bridge Scan Test"):
            try:
                res = bridge_scan(params={"symbol": "SPY"})
                st.success("Scan OK")
                st.json(res)
            except Exception as e:
                st.error(f"Scan failed: {e}")

# ---- render links (NO list comprehensions; avoid implicit writes) ----
st.subheader("Core")
for p, l in CORE:
    st.page_link(p, label=l)

st.subheader("Markets")
for p, l in MARKETS:
    st.page_link(p, label=l)

st.subheader("Status")
for p, l in STATUS:
    st.page_link(p, label=l)

with st.expander("Extras"):
    for p, l in EXTRAS:
        st.page_link(p, label=l)

# ---- Vega grouped sidebar (auto-added) ----
def render_grouped_nav():
    st.sidebar.markdown("### Navigation")
    try:
        with st.sidebar.expander("Dashboards", expanded=True):
            st.page_link("pages/00_Home.py", label="Home", icon="🏠")
            st.page_link("pages/01_North_America_Text_Dashboard.py", label="North America", icon="🇺🇸")
            st.page_link("pages/02_APAC_Text_Dashboard.py", label="APAC", icon="🌏")
            st.page_link("pages/02_Europe_Text_Dashboard.py", label="Europe", icon="🇪🇺")
            st.page_link("pages/10_Breadth_Grid.py", label="Breadth Grid", icon="🧮")
            st.page_link("pages/12_Sector_Flip_Alerts.py", label="Sector Flip Alerts", icon="⚡")
        with st.sidebar.expander("Charts", expanded=False):
            st.page_link("pages/05_TradingView_Charts.py", label="TradingView Charts", icon="📊")
            st.page_link("pages/06_Vega_Native_Chart.py", label="Vega Native Chart", icon="🗺️")
            st.page_link("pages/10_TradingView_Bridge.py", label="TradingView Bridge", icon="🔌")
        with st.sidebar.expander("Scanners", expanded=False):
            st.page_link("pages/01_RealTime_Scanner.py", label="Real-Time Scanner", icon="⏱️")
            st.page_link("pages/01_Scanner_OnDemand.py", label="On-Demand Scanner", icon="🧰")
            st.page_link("pages/real_time_scanner_wrapper.py", label="RT Scanner Wrapper", icon="📦")
        with st.sidebar.expander("Admin", expanded=False):
            st.page_link("pages/00_Admin_Data_Entry.py", label="Admin Data Entry", icon="🧾")
            st.page_link("pages/09_Owners_Daily_Digest.py", label="Owners Daily Digest", icon="📰")
    except Exception:
        st.sidebar.info("Upgrade Streamlit to use grouped navigation.")

# Render grouped nav
try:
    render_grouped_nav()
except Exception:
    pass
# -------------------------------------------

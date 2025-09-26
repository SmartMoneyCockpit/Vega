# src/app.py (injected IB badge/panel + env check)
import streamlit as st, os, sys, json, datetime
from vega.utils.slug_guard import scan_pages_for_slug_collisions, list_pages_and_slugs, assert_unique_page_links

try:
    from components.ib_status import status_badge, render_ib_panel
except Exception:
    status_badge = render_ib_panel = None
try:
    from components.env_check import render_env_check
except Exception:
    render_env_check = None

BASE_DIR=os.path.dirname(__file__); PAGES_DIR="pages"; PAGES_ABS=os.path.join(BASE_DIR,PAGES_DIR); LOGS_DIR=os.path.join(BASE_DIR,"logs")
os.makedirs(LOGS_DIR, exist_ok=True)
collisions = scan_pages_for_slug_collisions(PAGES_ABS)
if collisions:
    lines="\n".join(f"  /{slug} -> {', '.join(files)}" for slug,files in sorted(collisions.items()))
    msg="[BOOT BLOCKED] Duplicate page URL paths detected:\n"+lines
    with open(os.path.join(LOGS_DIR,"startup_checks.log"),"a",encoding="utf-8") as fh: fh.write(f"{datetime.datetime.utcnow().isoformat()}Z  {msg}\n"); sys.exit(msg)

st.session_state.setdefault("_vega_pages_logged", False)
if not st.session_state["_vega_pages_logged"]:
    st.session_state["_vega_pages_logged"]=True
    table=list_pages_and_slugs(PAGES_ABS)
    with open(os.path.join(LOGS_DIR,"startup_checks.log"),"a",encoding="utf-8") as fh: fh.write(f"{datetime.datetime.utcnow().isoformat()}Z  PAGES={json.dumps(table)}\n")

st.set_page_config(page_title="Vega Cockpit", layout="wide")
if status_badge: status_badge()
st.title("Vega Cockpit – Home")

def exists_in_pages(name): return os.path.exists(os.path.join(PAGES_ABS,name))
def first_existing(*names):
    for n in names:
        if exists_in_pages(n): return f"{PAGES_DIR}/{n}"
    return None

CORE=[]; 
for file,label in [("00_Home.py","🏠 Home"),("096_IBKR_Ticker_ib.py","⏱️ IBKR Ticker (ib_insync)"),("097_IBKR_Quick_Test_ib.py","🧪 IBKR Quick Test (ib_insync)"),("098_IBKR_Order_Ticket_ib.py","🧾 IBKR Order Ticket (ib_insync)")]:
    if exists_in_pages(file): CORE.append((f"{PAGES_DIR}/{file}",label))

MARKETS=[]; na=first_existing("101_North_America.py","01_North_America_Text_Dashboard.py","North_America_Text_Dashboard.py")
if na: MARKETS.append((na,"🌎 North America"))
eu=first_existing("102_Europe.py","02_Europe_Text_Dashboard.py","Europe_Text_Dashboard.py")
if eu: MARKETS.append((eu,"🌍 Europe"))
apac=first_existing("103_APAC.py","03_APAC.py","02_APAC_Text_Dashboard.py","APAC_Text_Dashboard.py")
if apac: MARKETS.append((apac,"🌏 APAC"))

STATUS=[]; 
if exists_in_pages("095_IB_Feed_Status.py"): STATUS.append((f"{PAGES_DIR}/095_IB_Feed_Status.py","📡 IB Feed Status"))
if exists_in_pages("Logs_IBKR.py"): STATUS.append((f"{PAGES_DIR}/Logs_IBKR.py","🪵 IBKR Logs"))

EXTRAS=[]; 
if exists_in_pages("05_TradingView_Charts.py"): EXTRAS.append((f"{PAGES_DIR}/05_TradingView_Charts.py","📊 TradingView Charts"))
if exists_in_pages("06_Vega_Native_Chart.py"): EXTRAS.append((f"{PAGES_DIR}/06_Vega_Native_Chart.py","📈 Vega Native Chart"))
nf=first_existing("404_Not_Found.py","Not_Found.py","404.py","Help.py")
if nf: EXTRAS.append((nf,"🚧 404 / Help"))

ALL_LINKS=CORE+MARKETS+STATUS+EXTRAS; assert_unique_page_links([p for p,_ in ALL_LINKS])

if render_env_check: 
    with st.container(): render_env_check()
if render_ib_panel: 
    with st.container(): render_ib_panel()

st.subheader("Core"); [st.page_link(p,label=l) for p,l in CORE]
st.subheader("Markets"); [st.page_link(p,label=l) for p,l in MARKETS]
st.subheader("Status"); [st.page_link(p,label=l) for p,l in STATUS]
with st.expander("Extras"): 
    [st.page_link(p,label=l) for p,l in EXTRAS]

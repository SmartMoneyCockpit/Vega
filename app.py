import streamlit as st
st.set_page_config(page_title='Vega Cockpit', layout='wide')
st.title('Vega Cockpit')


# [VEGA: PANELS INJECTION]
import yaml
from modules.sector_heatmap import render as render_sector_heatmap, load_sector_data
from modules.alerts.sector_flip import render as render_sector_flips
from modules.emailing.aplus_digest import build_digest
try:
    with open("config/settings.yaml","r") as _f:
        SETTINGS = yaml.safe_load(_f) or {}
except Exception:
    SETTINGS = {}
st.markdown("## Stay Out / Get Back In")
s1, s2 = st.columns([3,2])
with s1:
    render_sector_heatmap(st, SETTINGS)
with s2:
    df = load_sector_data(mode=SETTINGS.get("tradingview",{}).get("mode","public"))
    render_sector_flips(st, df, SETTINGS)



# --- IBKR Live Ticker (mini widget) -----------------------------------------
import os, requests

BRIDGE_URL = os.getenv("IBKR_BRIDGE_URL", "http://127.0.0.1:8088")
API_KEY    = os.getenv("IBKR_API_KEY", os.getenv("BRIDGE_API_KEY", ""))

def _ibkr_quote(sym: str):
    try:
        r = requests.get(f"{BRIDGE_URL}/price/{sym}",
                         headers={"x-api-key": API_KEY}, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

with st.expander("IBKR Live Ticker", expanded=False):
    left, right = st.columns([3,1])
    with left:
        _syms = st.text_input("Symbols (comma separated)", 
                              st.session_state.get("ibkr_syms", "SPY,AAPL,MSFT")).upper()
        st.session_state["ibkr_syms"] = _syms
    with right:
        refresh = st.slider("Refresh (s)", 2, 30, 5)

    try:
        (st.autorefresh if hasattr(st, "autorefresh") else st.experimental_rerun)(
            interval=refresh*1000, key="ibkr_live_ticker_mini")
    except Exception:
        pass

    syms = [s.strip() for s in _syms.split(",") if s.strip()]
    cols = st.columns(max(1, len(syms)))
    for i, sym in enumerate(syms):
        data = _ibkr_quote(sym)
        if "error" in data:
            cols[i].error(f"{sym}: {data['error']}")
        else:
            last = data.get("last")
            bid  = data.get("bid")
            ask  = data.get("ask")
            cols[i].metric(sym, f"{last if last is not None else '—'}",
                           delta=f"Bid {bid if bid is not None else '—'} / Ask {ask if ask is not None else '—'}")
# ---------------------------------------------------------------------------


# --- IBKR Status & Portfolio Panel ------------------------------------------
import requests

def _ibkr_health():
    try:
        r = requests.get(f"{BRIDGE_URL}/health", headers={"x-api-key": API_KEY}, timeout=4)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def _ibkr_positions():
    try:
        r = requests.get(f"{BRIDGE_URL}/positions", headers={"x-api-key": API_KEY}, timeout=6)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return [{"error": str(e)}]

st.subheader("IBKR Connection Status")
h = _ibkr_health()
if "error" in h:
    st.error(f"Bridge error: {h['error']}")
else:
    st.success(f"Connected: {h.get('connected')} | Host: {h.get('host')}:{h.get('port')}")

with st.expander("IBKR Portfolio Positions", expanded=False):
    poss = _ibkr_positions()
    if isinstance(poss, list) and poss:
        st.table(poss)
    else:
        st.write("No positions or error.")
# ---------------------------------------------------------------------------

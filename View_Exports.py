import streamlit as st
from services.tradingview_exports import export_watchlist, export_trades, export_links, tv_deeplink
from utils.picks_bridge import seed_session_picks
from components.tv_embed import tv_embed
from streamlit.components.v1 import html as _html

st.set_page_config(page_title="TradingView Export & Launch", layout="wide")

st.title("TradingView Export & Launch")
st.caption("IBKR → Vega (compute) → TradingView (display)")

seed_session_picks()  # seed demo data if empty

# Region control (fallback for older Streamlit)
try:
    region = st.segmented_control("Region", ["NA","EU","APAC"], default="NA")
except Exception:
    region = st.radio("Region", ["NA","EU","APAC"], index=0)

interval = st.selectbox("Default interval", ["15","60","240","D","W"], index=3)

picks = st.session_state.get(f"{region}_picks", [])

st.markdown("### Today's Picks")
if picks:
    st.dataframe([{**p, "tv_url": tv_deeplink(p.get("symbol",""), p.get("exchange"), interval)} for p in picks], use_container_width=True)
else:
    st.info("No picks available for this region yet. Your A-to-Z pipeline will populate st.session_state['<REGION>_picks'].")

col1, col2, col3 = st.columns(3)
symbols = [p.get("symbol") for p in picks]
with col1:
    if st.button("Export Watchlist TXT", use_container_width=True, type="primary"):
        path = export_watchlist(symbols, f"exports/tv_watchlist_{region}.txt")
        with open(path, "rb") as f:
            st.download_button("Download watchlist", f, file_name=path.split("/")[-1], mime="text/plain", use_container_width=True)

with col2:
    if st.button("Export Trades CSV", use_container_width=True):
        rows = [{**p, "interval": interval} for p in picks]
        path = export_trades(rows, f"exports/tv_trades_{region}.csv")
        with open(path, "rb") as f:
            st.download_button("Download trades", f, file_name=path.split("/")[-1], mime="text/csv", use_container_width=True)

with col3:
    if st.button("Export Links CSV", use_container_width=True):
        path = export_links(symbols, f"exports/tv_links_{region}.csv", interval=interval)
        with open(path, "rb") as f:
            st.download_button("Download links", f, file_name=path.split("/")[-1], mime="text/csv", use_container_width=True)

st.markdown("### Quick Launch Links")
open_links = [tv_deeplink(p.get("symbol",""), p.get("exchange"), interval) for p in picks]
for p, url in zip(picks[:50], open_links[:50]):
    st.markdown(f"- **{p.get('symbol')}** → [Open in TradingView]({url}) — {p.get('side','')} @ {p.get('entry','')} | SL {p.get('stop','')} | T1 {p.get('target1','')} ")

if open_links:
    _html("""
    <button id='openall' style='padding:8px 12px;border-radius:8px;border:1px solid #ddd;cursor:pointer;'>Open All in TradingView</button>
    <script>
    const links = %s;
    document.getElementById('openall').onclick = () => {
        let i = 0;
        const step = () => {
            if (i >= links.length) return;
            window.open(links[i], '_blank');
            i += 1;
            setTimeout(step, 350);
        };
        step();
    };
    </script>
    """ % (open_links), height=0)

with st.expander("Inline TradingView Preview (optional)", expanded=False):
    default_symbol = symbols[0] if symbols else "NASDAQ:AMZN"
    s = st.text_input("Symbol (EXCHANGE:SYMBOL or SYMBOL)", default_symbol)
    tv_embed(s, interval=interval)

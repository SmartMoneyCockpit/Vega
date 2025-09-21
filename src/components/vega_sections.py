# src/components/vega_sections.py
import os, pandas as pd, streamlit as st
from components.tv_bridge import render_chart

# ---- VectorVest loader ------------------------------------------------------
def _vv_env_key(region: str) -> str:
    m = {
        "NA": "VV_NA_CSV_URL", "NORTH AMERICA": "VV_NA_CSV_URL",
        "APAC": "VV_APAC_CSV_URL",
        "EU": "VV_EU_CSV_URL", "EUROPE": "VV_EU_CSV_URL",
    }
    return m.get(region.upper(), "VV_NA_CSV_URL")

@st.cache_data(ttl=300, show_spinner=False)
def load_vv(region: str) -> pd.DataFrame:
    url = os.getenv(_vv_env_key(region), "")
    df = None
    if url:
        try:
            df = pd.read_csv(url)
        except Exception as e:
            st.warning(f"VectorVest: could not load {url} — {e}")
    if df is None:
        data_dir = os.getenv("DATA_DIR", "data")
        local = os.path.join(data_dir, f"vv_{region.lower().replace(' ','_')}.csv")
        if os.path.exists(local):
            try:
                df = pd.read_csv(local)
            except Exception as e:
                st.warning(f"VectorVest: failed reading {local} — {e}")
    if df is None:
        df = pd.DataFrame(columns=["Symbol","Name","Price","VST","RT","RS","RV","CI","GRT","DY","Sector"])
    return df

def vv_panel(region: str, default_symbol: str, max_rows: int = 50) -> str:
    st.subheader(f"VectorVest Candidates — {region}")
    df = load_vv(region)
    if df.empty:
        st.info("No VectorVest results yet for this region.")
        return default_symbol

    cols = [c for c in ["Symbol","Name","Price","VST","RT","RS","RV","CI","GRT","DY","Sector"] if c in df.columns]
    small = df[cols].head(max_rows)
    st.dataframe(small, use_container_width=True, hide_index=True)
    syms = small["Symbol"].astype(str).tolist()
    pick = st.selectbox("Pick a ticker", [default_symbol] + syms, index=0, key=f"vvpick_{region}")
    return pick

# ---- TradingView chart block (public embed) --------------------------------
def chart_block(symbol: str, interval: str, theme: str, height: int):
    st.subheader("Chart")
    render_chart(symbol=symbol, interval=interval, theme=theme, height=height, mode="auto")
    st.link_button("Open on TradingView", f"https://www.tradingview.com/chart/?symbol={symbol}", use_container_width=True)

# ---- Screener text notes ----------------------------------------------------
def screener_notes(region: str, symbol: str):
    st.subheader("Screener Notes")
    key = f"screener_{region}_{symbol}"
    st.text_area("Notes (per symbol, session-saved)", value=st.session_state.get(key, ""), key=key, height=160)

from utils.prefs_bootstrap import prefs
import streamlit as st
import pandas as pd
from src.config_schema import load_config
from src.providers import MarketDataProvider
from src.indicators import apply_pack
from src.charts import price_with_ma

st.set_page_config(page_title="Vega Cockpit", layout="wide")

@st.cache_data(show_spinner=False)
def get_config():
    return load_config("vega_config.yaml")

@st.cache_data(show_spinner=False)
def fetch(symbol: str, period: str = "6mo", interval: str = "1d"):
    cfg = get_config()
    provider = MarketDataProvider(cfg.providers.order + ["public"])
    return provider._fetch(symbol, period, interval)

cfg = get_config()
st.title("Vega Cockpit — Core Fix Pack")

regions = []
if cfg.ui.enable_us: regions.append("USA")
if cfg.ui.enable_canada: regions.append("Canada")
if cfg.ui.enable_mexico: regions.append("Mexico")
if cfg.ui.enable_europe: regions.append("Europe")
if cfg.ui.enable_apac: regions.append("APAC")

if not regions:
    st.warning("No regions enabled in config.")
    st.stop()

tabs = st.tabs(regions)

# Europe demo
if "Europe" in regions:
    with tabs[regions.index("Europe")]:
        st.subheader("Europe Indices & ETFs")
        symbols = []
        for ex in cfg.exchanges:
            symbols += ex.indices + ex.etfs
        picked = st.multiselect("Symbols", symbols, default=symbols[:6])
        col1, col2 = st.columns(2)
        for i, s in enumerate(picked):
            df = fetch(s)
            if df is None or df.empty:
                st.error(f"No data for {s}")
                continue
            df = apply_pack(df, cfg.indicators.model_dump())
            fig = price_with_ma(df, title=s)
            (col1 if i % 2 == 0 else col2).plotly_chart(fig, use_container_width=True)


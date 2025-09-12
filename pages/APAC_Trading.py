import streamlit as st
from pathlib import Path

st.set_page_config(page_title="APAC Trading", layout="wide")
st.title("🌏 Asia–Pacific Trading — Vega Cockpit")

cfg_path = Path("config/markets/apac.yaml")
st.success("APAC config loaded.") if cfg_path.exists() else st.error("Missing config: config/markets/apac.yaml")

with st.expander("Quick Filters", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1: st.selectbox("Risk Regime", ["Neutral", "Risk-On", "Risk-Off"], index=0)
    with c2: st.checkbox("Hide names within 30 days of earnings", value=True)
    with c3: st.checkbox("Show FX overlays", value=True)

st.subheader("Starter Universe")
st.markdown("- **Indices**: Nikkei (^N225), ASX 200 (^AXJO), CSI 300 (000300.SS), Hang Seng (^HSI), KOSPI (^KS11)")
st.markdown("- **ETFs**: EWJ/DXJ, EWA, FXI/MCHI/EWH, EWY")
st.markdown("- **FX**: USDJPY, AUDUSD, USDCNY, USDHKD")
st.caption("Upgrade path: wire to your data layer for live prices, breadth, IV, & earnings windows.")

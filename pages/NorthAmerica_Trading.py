import streamlit as st
from pathlib import Path

st.set_page_config(page_title="North America Trading", layout="wide")
st.title("🌎 North America Trading — Vega Cockpit")

cfg_path = Path("config/markets/na.yaml")
st.success("North America config loaded.") if cfg_path.exists() else st.error("Missing config: config/markets/na.yaml")

with st.expander("Quick Filters", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1: st.selectbox("Risk Regime", ["Neutral", "Risk-On", "Risk-Off"], index=0)
    with c2: st.checkbox("Hide names within 30 days of earnings", value=True)
    with c3: st.checkbox("Show FX overlays", value=True)

st.subheader("Starter Universe")
st.markdown("- **Indices**: S&P 500, Nasdaq, Dow, Russell 2000, TSX, IPC Mexico")
st.markdown("- **ETFs**: SPY/QQQ/DIA/IWM (US), XIC.TO/ZSP.TO (CA), EWW (MX)")
st.markdown("- **FX**: USDCAD, USDMXN • **Commodities**: Oil, NatGas, Gold, Silver, Copper")
st.caption("Upgrade path: hook to RS/Breadth/IV + your earnings & tariff rules.")

import streamlit as st
from pathlib import Path
import pandas as pd

try:
    import yaml  # optional
except Exception:
    yaml = None

st.set_page_config(page_title="Europe Trading", layout="wide")
st.title("🌍 Europe Trading — Vega Cockpit")

cfg_path = Path("config/markets/europe.yaml")
if not cfg_path.exists():
    st.error("Missing config: config/markets/europe.yaml")
    st.stop()
st.success("Europe config loaded.")

with st.expander("Quick Filters", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1: st.selectbox("Risk Regime", ["Neutral", "Risk-On", "Risk-Off"], index=0)
    with c2: st.checkbox("Hide names within 30 days of earnings", value=True)
    with c3: st.checkbox("Show FX overlays", value=True)

st.subheader("Starter Universe")

if yaml:
    try:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        exchanges = cfg.get("exchanges", [])
        df = pd.DataFrame([
            {"Exchange": e.get("name",""),
             "Indices": ", ".join(e.get("indices",[]) or []),
             "ETFs": ", ".join(e.get("etfs",[]) or [])}
            for e in exchanges
        ])
        st.dataframe(df, use_container_width=True) if not df.empty else st.info("No exchanges in config.")
        fx = ", ".join(cfg.get("fx_pairs", []) or [])
        com = ", ".join(cfg.get("commodities", []) or [])
        st.markdown(f"**FX Pairs:** {fx or '—'}  \n**Commodities:** {com or '—'}")
    except Exception as e:
        st.warning(f"Could not parse YAML: {e}")
        st.code(cfg_path.read_text(encoding="utf-8"), language="yaml")
else:
    st.info("PyYAML not installed; showing config text instead.")
    st.code(cfg_path.read_text(encoding="utf-8"), language="yaml")

st.caption("Upgrade path: connect to live prices, RS/breadth, IV, and earnings windows.")

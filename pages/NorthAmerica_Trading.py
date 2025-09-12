import streamlit as st
from pathlib import Path
import pandas as pd

# Try to use PyYAML if present; fall back to showing raw text
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

st.set_page_config(page_title="North America Trading", layout="wide")
st.title("🌎 North America Trading — Vega Cockpit")

# --- Config load (fail-safe) ---
cfg_path = Path("config/markets/na.yaml")
if not cfg_path.exists():
    st.error("Missing config: config/markets/na.yaml")
    st.stop()
st.success("North America config loaded.")

# --- Quick Filters (UI only for now) ---
with st.expander("Quick Filters", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.selectbox("Risk Regime", ["Neutral", "Risk-On", "Risk-Off"], index=0)
    with c2:
        st.checkbox("Hide names within 30 days of earnings", value=True)
    with c3:
        st.checkbox("Show FX overlays", value=True)

# --- Starter Universe (read from YAML if possible) ---
st.subheader("Starter Universe")

if yaml:
    try:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        exchanges = cfg.get("exchanges", [])
        df = pd.DataFrame(
            [
                {
                    "Exchange": e.get("name", ""),
                    "Indices": ", ".join(e.get("indices", []) or []),
                    "ETFs": ", ".join(e.get("etfs", []) or []),
                }
                for e in exchanges
            ]
        )
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No exchanges defined in config.")

        fx_pairs = ", ".join(cfg.get("fx_pairs", []) or [])
        commodities = ", ".join(cfg.get("commodities", []) or [])
        st.markdown(
            f"**FX Pairs:** {fx_pairs or '—'}  \n"
            f"**Commodities:** {commodities or '—'}"
        )
    except Exception as e:
        st.warning(f"Could not parse YAML: {e}")
        st.code(cfg_path.read_text(encoding="utf-8"), language="yaml")
else:
    st.info("PyYAML not installed; showing config text instead.")
    st.code(cfg_path.read_text(encoding="utf-8"), language="yaml")

st.caption(
    "Upgrade path: hook to RS/Breadth/IV + your earnings & tariff rules."
)

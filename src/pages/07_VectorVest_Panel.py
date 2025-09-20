
import os, json, streamlit as st

st.set_page_config(page_title="VectorVest Panel", layout="wide")
st.title("VectorVest — Panel")
st.caption("RT • RV • RS • VST • CI • EPS • Growth • Sales Growth")

st.subheader("Diagnostics")
vv_json = os.path.join("vault","cache","vectorvest_signals.json")
st.write({"vectorvest_signals.json_exists": os.path.exists(vv_json), "path": vv_json})
if os.path.exists(vv_json):
    try:
        data = json.load(open(vv_json,"r",encoding="utf-8"))
        st.write({"signals_count": len(data.get("signals", []))})
    except Exception as e:
        st.error(f"Failed to parse vectorvest_signals.json: {e}")

st.subheader("Panel")
# Try both import paths; if both fail, inline render
try:
    from modules.vectorvest_panel import render as render_vv
    render_vv()
except Exception as e1:
    try:
        import sys
        sys.path.append(".")
        from modules.vectorvest_panel import render as render_vv
        render_vv()
    except Exception as e2:
        st.warning("Falling back to inline renderer (could not import modules.vectorvest_panel).")
        try:
            import pandas as pd
            from modules.vectorvest_utils import compute_vv_columns  # provided in this patch
            if os.path.exists(vv_json):
                data = json.load(open(vv_json,"r",encoding="utf-8"))
                df = compute_vv_columns(pd.DataFrame(data.get("signals", [])), os.path.join("modules","rules","_vega_scores.yaml"))
                st.dataframe(df, use_container_width=True, height=600)
            else:
                st.info("No cache file present at vault/cache/vectorvest_signals.json")
        except Exception as e3:
            st.error(f"Inline render failed: {e3}")

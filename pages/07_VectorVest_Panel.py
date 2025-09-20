
import os, streamlit as st

st.set_page_config(page_title="VectorVest Panel", layout="wide")

st.title("VectorVest — Panel")
st.caption("RT • RV • RS • VST • CI • EPS • Growth • Sales Growth")

# Quick diagnostics so you can see why a table might be empty
st.subheader("Diagnostics")
vv_json = os.path.join("vault","cache","vectorvest_signals.json")
exists = os.path.exists(vv_json)
st.write({"vectorvest_signals.json_exists": exists, "path": vv_json})

if exists:
    try:
        import json
        data = json.load(open(vv_json, "r", encoding="utf-8"))
        st.write({"signals_count": len(data.get("signals", []))})
    except Exception as e:
        st.error(f"Failed to read vectorvest_signals.json: {e}")

# Render the panel
st.subheader("Panel")
try:
    from modules.vectorvest_panel import render as render_vv
    render_vv()
except Exception as e:
    st.error(f"VectorVest panel render error: {e}")
    st.exception(e)

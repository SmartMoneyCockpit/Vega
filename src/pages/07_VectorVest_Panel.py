
import os, json, streamlit as st
import pandas as pd

st.set_page_config(page_title="VectorVest — Self-Contained", layout="wide")

st.title("VectorVest — Panel (Self-Contained)")
st.caption("RT • RV • RS • VST • CI • EPS • Growth • Sales Growth")

def compute_vst(df: pd.DataFrame, weights=(0.4,0.3,0.3)) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    # Normalize column names
    rename = {
        "RT":"rt","RV":"rv","RS":"rs","CI":"ci","EPS":"eps",
        "Growth":"growth","Sales Growth":"sales_growth","salesGrowth":"sales_growth","VST":"vst"
    }
    for k,v in rename.items():
        if k in out.columns and v not in out.columns:
            out[v] = out[k]
    # Compute VST when possible
    if all(c in out.columns for c in ["rt","rs","rv"]) and "vst" not in out.columns:
        w_rt,w_rs,w_rv = weights
        out["vst"] = (w_rt*out["rt"].astype(float) +
                      w_rs*out["rs"].astype(float) +
                      w_rv*out["rv"].astype(float))
    # Clip 0–2 scales
    for c in ["rt","rs","rv","ci","vst"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").clip(0,2)
    # Column order
    pref = ["symbol","name","price","rt","rv","rs","vst","ci","eps","growth","sales_growth"]
    cols = [c for c in pref if c in out.columns] + [c for c in out.columns if c not in pref]
    return out[cols]

# Diagnostics
st.subheader("Diagnostics")
vv_json = os.path.join("vault","cache","vectorvest_signals.json")
exists = os.path.exists(vv_json)
diag = {"vectorvest_signals.json_exists": exists, "path": vv_json}
if exists:
    try:
        raw = json.load(open(vv_json,"r",encoding="utf-8"))
        diag["signals_count"] = len(raw.get("signals", []))
    except Exception as e:
        diag["error"] = str(e)
st.write(diag)

st.subheader("Panel")
if not exists:
    st.info("Missing file: vault/cache/vectorvest_signals.json"); st.stop()

try:
    data = json.load(open(vv_json,"r",encoding="utf-8"))
    df = pd.DataFrame(data.get("signals", []))
    df = compute_vst(df)
    if df is None or df.empty:
        st.info("No rows to display (check your signals).")
    else:
        # UI safety overrides
        st.markdown(
            """<style>
            .stDataFrame, .stDataFrame [data-testid="stHorizontalBlock"], .stDataFrame div[role="grid"] {
                background-color:#0f1116 !important;
            }
            div[data-testid="stDataFrame"] div[role="grid"] {min-height:520px !important;}
            iframe { z-index: 0; }
            </style>""", unsafe_allow_html=True
        )
        st.dataframe(df, use_container_width=True, height=600)
        # CSV download
        try:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download VV Table (CSV)", data=csv, file_name="vectorvest_metrics.csv", mime="text/csv")
        except Exception:
            pass
except Exception as e:
    st.error(f"Render error: {e}")
    st.exception(e)

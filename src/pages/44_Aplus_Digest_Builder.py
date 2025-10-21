import os, sys, pathlib, json
import streamlit as st

_here = pathlib.Path(__file__).resolve()
sys.path.append(str(_here.parents[1]))

from modules.digest.sendgrid_digest import build_digest_payload, save_digest_preview

st.set_page_config(page_title="A+ Digest Builder", page_icon="📧", layout="centered")
st.title("📧 A+ Digest (Preview)")

st.caption("Builds a daily digest payload of A+ setups (preview only; no external email).")
raw = st.text_area("Paste setup JSON array", value='[{"ticker":"SPY","entry":430.0,"stop":420.0,"target":455.0,"rr":3.0}]', height=200)
if st.button("Build & Save Preview"):
    try:
        items = json.loads(raw)
        payload = build_digest_payload(items)
        path = save_digest_preview(payload)
        st.success(f"Saved preview: {path}")
        st.json(payload)
    except Exception as ex:
        st.error(f"Invalid JSON: {ex}")

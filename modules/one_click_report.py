import streamlit as st, os, glob
def render():
    st.header("One-Click Full Daily Report")
    st.write("Server creates a combined PDF each morning into /vault/exports.")
    pdfs = sorted(glob.glob("vault/exports/daily-report-*.pdf"))
    if pdfs:
        st.success(f"Latest report: {os.path.basename(pdfs[-1])}")
    else:
        st.info("No report yet. GitHub Action will generate it automatically.")

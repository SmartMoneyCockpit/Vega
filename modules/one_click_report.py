# modules/one_click_report.py
import os, glob
import streamlit as st

def _ensure_dirs():
    for d in ["vault/exports", "vault/snapshots", "vault/reports", "vault/cache"]:
        os.makedirs(d, exist_ok=True)

def _latest_daily_pdf():
    pdfs = sorted(glob.glob("vault/exports/daily-report-*.pdf"))
    return pdfs[-1] if pdfs else None

def render():
    _ensure_dirs()

    st.header("One-Click Full Daily Report")
    st.write("Server creates a combined PDF each morning into `/vault/exports`.")

    latest = _latest_daily_pdf()
    if latest:
        st.success(f"Latest report: **{os.path.basename(latest)}**")
    else:
        st.info("No report yet. GitHub Action will generate it automatically.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Send test email (no attachment)"):
            try:
                from tools.emailer import send_email
                send_email(
                    subject="Vega test email",
                    html_body="<h3>Vega test</h3><p>If you see this, SMTP creds are good.</p>",
                    # to_addrs=["your@email.com"],  # optional; else uses VEGA_EMAIL_TO
                )
                st.success("Test email sent ✅")
            except Exception as e:
                st.error(f"Email failed: {e}")

    with col2:
        disabled = latest is None
        if st.button("Email latest daily PDF", disabled=disabled):
            try:
                from tools.emailer import send_email
                send_email(
                    subject="Vega – Daily Report",
                    html_body=f"<p>Attached: {os.path.basename(latest)}</p>",
                    attachments=[latest],
                )
                st.success("Report emailed ✅")
            except Exception as e:
                st.error(f"Email failed: {e}")

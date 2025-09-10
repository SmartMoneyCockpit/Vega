# modules/one_click_report.py
import os, glob
import streamlit as st
from tools.emailer import smtp_diag, send_email

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
    st.caption(f"SMTP diag: {smtp_diag()}")

    latest = _latest_daily_pdf()
    if latest:
        st.success(f"Latest report: **{os.path.basename(latest)}**")
    else:
        st.info("No report yet. GitHub Action will generate it automatically.")

    default_rcpt = os.getenv("VEGA_EMAIL_TO", "")
    rcpt = st.text_input("Recipient (optional, overrides VEGA_EMAIL_TO)", default_rcpt)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Send test email (no attachment)"):
            try:
                send_email(
                    to_addrs=rcpt or None,
                    subject="Vega test email",
                    html_body="<h3>Vega test</h3><p>If you see this, SMTP creds are good.</p>",
                )
                st.success(f"Test email sent ✅ to {rcpt or default_rcpt or '(no default set)'}")
            except Exception as e:
                st.error(f"Email failed: {e}")

    with col2:
        disabled = latest is None
        if st.button("Email latest daily PDF", disabled=disabled):
            try:
                send_email(
                    to_addrs=rcpt or None,
                    subject="Vega – Daily Report",
                    html_body=f"<p>Attached: {os.path.basename(latest)}</p>",
                    attachments=[latest] if latest else None,
                )
                st.success(f"Report emailed ✅ to {rcpt or default_rcpt or '(no default set)'}")
            except Exception as e:
                st.error(f"Email failed: {e}")

    with col3:
        if st.button("Resend last report", disabled=latest is None):
            try:
                send_email(
                    to_addrs=rcpt or None,
                    subject="Vega – Daily Report (resend)",
                    html_body=f"<p>Re-sending: {os.path.basename(latest)}</p>",
                    attachments=[latest] if latest else None,
                )
                st.success("Resent ✅")
            except Exception as e:
                st.error(f"Email failed: {e}")
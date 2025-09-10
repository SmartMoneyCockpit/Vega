col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Send test email (no attachment)"):
        send_email(to_addrs=rcpt or None,
                   subject="Vega test email",
                   html_body="<h3>Vega test</h3><p>If you see this, SMTP creds are good.</p>")
        st.success(f"Test email sent ✅ to {rcpt or default_rcpt or '(no default set)'}")

with col2:
    disabled = latest is None
    if st.button("Email latest daily PDF", disabled=disabled):
        send_email(to_addrs=rcpt or None,
                   subject="Vega – Daily Report",
                   html_body=f"<p>Attached: {os.path.basename(latest)}</p>",
                   attachments=[latest] if latest else None)
        st.success(f"Report emailed ✅ to {rcpt or default_rcpt or '(no default set)'}")

with col3:
    if st.button("Resend last report", disabled=latest is None):
        send_email(to_addrs=rcpt or None,
                   subject="Vega – Daily Report (resend)",
                   html_body=f"<p>Re-sending: {os.path.basename(latest)}</p>",
                   attachments=[latest] if latest else None)
        st.success("Resent ✅")

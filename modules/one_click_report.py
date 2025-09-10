# tools/emailer.py
import os, smtplib, mimetypes, time
from email.message import EmailMessage

HOST = os.getenv("MAIL_HOST") or os.getenv("VEGA_EMAIL_HOST") or "smtp.gmail.com"
PORT = int(os.getenv("MAIL_PORT") or os.getenv("VEGA_EMAIL_PORT") or "587")
USER = os.getenv("MAIL_USER") or os.getenv("VEGA_EMAIL_USER")
PASS = os.getenv("MAIL_APP_PASSWORD") or os.getenv("VEGA_EMAIL_PASS")
FROM = os.getenv("MAIL_FROM") or (USER and f"Vega Cockpit <{USER}>")
DEFAULT_TO = os.getenv("VEGA_EMAIL_TO")

MAX_RETRIES = int(os.getenv("MAIL_MAX_RETRIES", "1"))
RETRY_BASE = float(os.getenv("MAIL_RETRY_BASE_S", "1.0"))

def send_email(to_addrs=None, subject="", html_body="", attachments=None, cc=None, bcc=None):
    if to_addrs is None:
        to_addrs = [DEFAULT_TO] if DEFAULT_TO else []
    if isinstance(to_addrs, str):
        to_addrs = [to_addrs]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM or USER
    msg["To"] = ", ".join([a for a in to_addrs if a])
    if cc:
        cc_list = cc if isinstance(cc, list) else [cc]
        msg["Cc"] = ", ".join(cc_list)
        to_addrs += cc_list
    if bcc:
        bcc_list = bcc if isinstance(bcc, list) else [bcc]
        to_addrs += bcc_list

    msg.set_content("HTML email. Please view in an HTML-capable client.")
    msg.add_alternative(html_body or "<p>(no body)</p>", subtype="html")

    for path in (attachments or []):
        ctype, _ = mimetypes.guess_type(path)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(path))

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with smtplib.SMTP(HOST, PORT, timeout=30) as s

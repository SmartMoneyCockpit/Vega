# tools/emailer.py
import os, smtplib, mimetypes, time, re
from email.message import EmailMessage

# Prefer MAIL_*; fall back to VEGA_EMAIL_* (Render setup)
HOST = os.getenv("MAIL_HOST") or os.getenv("VEGA_EMAIL_HOST") or "smtp.gmail.com"
PORT = int(os.getenv("MAIL_PORT") or os.getenv("VEGA_EMAIL_PORT") or "587")
USER = os.getenv("MAIL_USER") or os.getenv("VEGA_EMAIL_USER")
PASS = os.getenv("MAIL_APP_PASSWORD") or os.getenv("VEGA_EMAIL_PASS")
FROM = os.getenv("MAIL_FROM") or (USER and f"Vega Cockpit <{USER}>")
DEFAULT_TO = os.getenv("VEGA_EMAIL_TO")
MAIL_BCC_ARCHIVE = os.getenv("MAIL_BCC_ARCHIVE")

MAX_RETRIES = int(os.getenv("MAIL_MAX_RETRIES", "1"))
RETRY_BASE  = float(os.getenv("MAIL_RETRY_BASE_S", "1.0"))
DEBUG_SMTP  = int(os.getenv("MAIL_DEBUG", "0"))  # set to 1 to print SMTP transcript

def smtp_diag():
    """Safe diagnostics (no secrets)."""
    return {
        "host": HOST,
        "port": PORT,
        "user_set": bool(USER),
        "pass_set": bool(PASS),
        "from_set": bool(FROM),
    }

def _normalize_addrs(x):
    if not x:
        return []
    if isinstance(x, str):
        return [p.strip() for p in re.split(r"[;,]+", x) if p.strip()]
    return list(x)

def _attach_files(msg: EmailMessage, attachments):
    for path in (attachments or []):
        ctype, _ = mimetypes.guess_type(path)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        with open(path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(path),
            )

def _send_starttls(msg: EmailMessage):
    with smtplib.SMTP(HOST, PORT, timeout=30) as s:
        s.set_debuglevel(DEBUG_SMTP)
        s.ehlo()
        s.starttls()
        s.ehlo()
        if USER and PASS:
            s.login(USER, PASS)
        s.send_message(msg)

def _send_ssl(msg: EmailMessage):
    with smtplib.SMTP_SSL(HOST, 465, timeout=30) as s:
        s.set_debuglevel(DEBUG_SMTP)
        s.ehlo()
        if USER and PASS:
            s.login(USER, PASS)
        s.send_message(msg)

def send_email(to_addrs=None, subject="", html_body="", attachments=None, cc=None, bcc=None):
    # Recipient list
    to_addrs = _normalize_addrs(to_addrs or DEFAULT_TO)
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM or USER
    msg["To"] = ", ".join([a for a in to_addrs if a])

    if cc:
        cc_list = _normalize_addrs(cc)
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)
            to_addrs += cc_list
    if bcc:
        to_addrs += _normalize_addrs(bcc)
    if MAIL_BCC_ARCHIVE:
        to_addrs += _normalize_addrs(MAIL_BCC_ARCHIVE)

    msg.set_content("HTML email. Please view in an HTML-capable client.")
    msg.add_alternative(html_body or "<p>(no body)</p>", subtype="html")
    _attach_files(msg, attachments)

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # If user explicitly set 465 → SSL. Else try STARTTLS then fallback to SSL.
            if PORT == 465:
                _send_ssl(msg)
            else:
                try:
                    _send_starttls(msg)
                except (smtplib.SMTPServerDisconnected, OSError):
                    _send_ssl(msg)
            return
        except Exception as e:
            last_err = e
            if attempt == MAX_RETRIES:
                raise
            time.sleep(RETRY_BASE * (2 ** (attempt - 1)))
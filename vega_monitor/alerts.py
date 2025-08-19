# vega_monitor/alerts.py
import os, json, smtplib, ssl
from email.mime.text import MIMEText

try:
    import requests  # optional; only for webhook if available
except Exception:
    requests = None

def send_webhook(payload: dict):
    url = os.getenv("VEGA_WEBHOOK_URL", "").strip()
    if not url or not requests:
        return False
    try:
        requests.post(url, json=payload, timeout=5)
        return True
    except Exception:
        return False

def send_email(subject: str, message: str):
    host = os.getenv("VEGA_EMAIL_HOST", "").strip()
    user = os.getenv("VEGA_EMAIL_USER", "").strip()
    pw   = os.getenv("VEGA_EMAIL_PASS", "").strip()
    port = int(os.getenv("VEGA_EMAIL_PORT", "465"))
    to   = os.getenv("VEGA_EMAIL_TO", "").strip()
    if not (host and user and pw and to):
        return False

    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to

        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=ctx, timeout=10) as s:
            s.login(user, pw)
            s.sendmail(user, [to], msg.as_string())
        return True
    except Exception:
        return False

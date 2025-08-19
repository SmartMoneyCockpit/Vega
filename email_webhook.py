\
import os, smtplib, ssl, requests
from email.mime.text import MIMEText

def send_webhook(text):
    url = os.getenv("WEBHOOK_URL","").strip()
    if not url: 
        return False
    try:
        requests.post(url, json={"text": text}, timeout=10)
        return True
    except Exception:
        return False

def send_email(subject, text):
    EMAIL_TO=os.getenv("EMAIL_TO"); EMAIL_FROM=os.getenv("EMAIL_FROM")
    SMTP_HOST=os.getenv("SMTP_HOST"); SMTP_PORT=os.getenv("SMTP_PORT","587")
    SMTP_USER=os.getenv("SMTP_USER"); SMTP_PASS=os.getenv("SMTP_PASS")
    if not all([EMAIL_TO, EMAIL_FROM, SMTP_HOST, SMTP_USER, SMTP_PASS]):
        return False
    msg = MIMEText(text)
    msg["Subject"]=subject
    msg["From"]=EMAIL_FROM; msg["To"]=EMAIL_TO
    try:
        ctx=ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as s:
            s.starttls(context=ctx)
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        return True
    except Exception:
        return False

def broadcast(subject, text):
    ok_webhook = send_webhook(text)
    ok_email = send_email(subject, text)
    return ok_webhook or ok_email

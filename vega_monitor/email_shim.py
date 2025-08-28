import os, smtplib, ssl
from email.mime.text import MIMEText

def send_mail(subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST")      # e.g. smtp.gmail.com
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("SMTP_FROM") or user
    to      = os.getenv("SMTP_TO")

    missing = [k for k,v in {
        "SMTP_HOST":host, "SMTP_PORT":port, "SMTP_USER":user,
        "SMTP_PASS":password, "SMTP_FROM":sender, "SMTP_TO":to
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing vars: {', '.join(missing)}")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=15) as s:
        s.starttls(context=ctx)
        s.login(user, password)
        s.send_message(msg)

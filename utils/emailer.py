# utils/emailer.py
import os, smtplib, ssl
from email.mime.text import MIMEText
from email.utils import formataddr

def send_email(subject: str, body: str):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    pwd  = os.getenv("SMTP_PASS")
    from_name = os.getenv("SMTP_FROM_NAME", "Vega Cockpit")
    from_addr = os.getenv("SMTP_FROM")
    to_addr   = os.getenv("SMTP_TO")

    missing = [k for k,v in {
        "SMTP_HOST":host,"SMTP_PORT":port,"SMTP_USER":user,"SMTP_PASS":pwd,
        "SMTP_FROM":from_addr,"SMTP_TO":to_addr}.items() if not v]
    if missing:
        raise RuntimeError(f"Missing required SMTP env vars: {', '.join(missing)}")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"]    = formataddr((from_name, from_addr))
    msg["To"]      = to_addr

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=30) as server:
        # STARTTLS on 587; for 465 use SMTP_SSL instead
        server.ehlo()
        if port == 587:
            server.starttls(context=context)
            server.ehlo()
        server.login(user, pwd)
        server.sendmail(from_addr, [to_addr], msg.as_string())

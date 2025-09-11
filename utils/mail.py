# utils/mail.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDER = os.getenv("ALERTS_SENDER", "alerts@example.com")
TO = os.getenv("ALERTS_TO", "you@example.com")
SG_KEY = os.getenv("SENDGRID_API_KEY", "")

def send_email(subject: str, body: str):
    if not SG_KEY:
        print(f"[EMAIL-DRYRUN] {subject}\n{body}\n")
        return
    message = Mail(from_email=SENDER, to_emails=TO, subject=subject, plain_text_content=body)
    sg = SendGridAPIClient(SG_KEY)
    sg.send(message)

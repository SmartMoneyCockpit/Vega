# utils/mailer.py
import os
from typing import Optional, Sequence
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def _env(k): 
    v = os.environ.get(k)
    return v.strip() if isinstance(v, str) else None

def send_email(subject:str, text_body:str, html_body:Optional[str]=None,
               to:Optional[Sequence[str]]=None, from_addr:Optional[str]=None):
    api = _env("SENDGRID_API_KEY"); frm = from_addr or _env("EMAIL_FROM")
    tos = list(to) if to else [x.strip() for x in (_env("EMAIL_TO") or "").split(",") if x.strip()]
    if not (api and frm and tos): raise RuntimeError("Missing SENDGRID_API_KEY/EMAIL_FROM/EMAIL_TO")
    msg = Mail(from_email=frm, to_emails=tos, subject=subject,
               plain_text_content=text_body, html_content=(html_body or text_body))
    SendGridAPIClient(api).send(msg)

def send_alert(title:str, body:str, html:Optional[str]=None):
    send_email(f"[VEGA][ALERT] {title}", body, html)

# utils/mailer.py
import os
from typing import Optional, Sequence
import requests

def _env(k: str) -> str:
    v = os.environ.get(k)
    return v.strip() if isinstance(v, str) else ""

def send_email(
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    to: Optional[Sequence[str]] = None,
    from_addr: Optional[str] = None,
) -> None:
    api_key = _env("SENDGRID_API_KEY")
    frm     = (from_addr or _env("EMAIL_FROM")).lower()
    tos     = list(to) if to else [x.strip() for x in _env("EMAIL_TO").split(",") if x.strip()]
    if not (api_key and frm and tos):
        raise RuntimeError("Missing SENDGRID_API_KEY/EMAIL_FROM/EMAIL_TO")

    data = {
        "personalizations": [{"to": [{"email": e} for e in tos]}],
        "from": {"email": frm},
        "subject": subject,
        "content": [{"type": "text/plain", "value": text_body}],
    }
    if html_body:
        data["content"].append({"type": "text/html", "value": html_body})

    r = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=data,
        timeout=15,
    )
    print("[sendgrid]", r.status_code, r.text[:300])
    r.raise_for_status()

def send_alert(title: str, body: str, html: Optional[str] = None) -> None:
    send_email(f"[VEGA][ALERT] {title}", body, html)

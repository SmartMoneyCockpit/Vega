# utils/mailer.py
import os
from typing import Optional, Sequence
from sendgrid import SendGridAPIClient
from python_http_client.exceptions import HTTPError

def _env(k: str) -> Optional[str]:
    v = os.environ.get(k)
    return v.strip() if isinstance(v, str) else None

def send_email(
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    to: Optional[Sequence[str]] = None,
    from_addr: Optional[str] = None,
) -> None:
    api_key = _env("SENDGRID_API_KEY")
    from_addr = from_addr or _env("EMAIL_FROM")
    to_list = list(to) if to else [x.strip() for x in (_env("EMAIL_TO") or "").split(",") if x.strip()]
    if not (api_key and from_addr and to_list):
        raise RuntimeError("Missing SENDGRID_API_KEY/EMAIL_FROM/EMAIL_TO")

    # Build the exact payload your cURL used (which returned 202)
    data = {
        "personalizations": [{"to": [{"email": e} for e in to_list]}],
        "from": {"email": from_addr},
        "subject": subject,
        "content": [{"type": "text/plain", "value": text_body}],
    }
    if html_body:
        data["content"].append({"type": "text/html", "value": html_body})

    sg = SendGridAPIClient(api_key)
    try:
        resp = sg.client.mail.send.post(request_body=data)
        print(f"[sendgrid] status={resp.status_code}")  # Expect 202
    except HTTPError as e:
        body = getattr(e, "body", None)
        try:
            body = body.decode() if hasattr(body, "decode") else body
        except Exception:
            pass
        print(f"[sendgrid] error status={getattr(e, 'status_code', '?')} body={body}")
        raise

def send_alert(title: str, body: str, html: Optional[str] = None) -> None:
    send_email(f"[VEGA][ALERT] {title}", body, html)


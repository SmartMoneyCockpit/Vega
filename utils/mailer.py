# utils/mailer.py
import os, unicodedata, re
from typing import Optional, Sequence
import requests

VERIFIED_SENDER = "blainedares@gmail.com"  # your verified Single Sender

def _env(k: str) -> str:
    v = os.environ.get(k)
    return v if isinstance(v, str) else ""

def _clean_email(s: str) -> str:
    # Normalize unicode, drop non-ASCII zero-width/etc, strip spaces, lower-case
    s = unicodedata.normalize("NFKC", (s or ""))
    s = "".join(ch for ch in s if ord(ch) < 128)
    s = re.sub(r"\s+", "", s).strip().lower()
    return s

def send_email(
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    to: Optional[Sequence[str]] = None,
    from_addr: Optional[str] = None,
) -> None:
    api_key = _clean_email(_env("SENDGRID_API_KEY"))
    # Clean envs
    env_from = _clean_email(_env("EMAIL_FROM"))
    to_list = list(to) if to else [
        _clean_email(x) for x in _env("EMAIL_TO").split(",") if _clean_email(x)
    ]
    if not (api_key and to_list):
        raise RuntimeError("Missing SENDGRID_API_KEY or EMAIL_TO")

    # Force FROM to your verified sender (eliminates any mismatch)
    frm = VERIFIED_SENDER

    data = {
        "personalizations": [{"to": [{"email": e} for e in to_list]}],
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

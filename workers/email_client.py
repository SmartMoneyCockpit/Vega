# workers/email_client.py
import os
import json
import requests

class EmailClient:
    def __init__(self, api_key: str | None = None, sender: str | None = None):
        self.api_key = api_key or os.environ["SENDGRID_API_KEY"]
        self.sender = sender or os.environ.get("ALERTS_FROM", "noreply@vega.local")

    def send(self, to: str, subject: str, body: str) -> None:
        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": self.sender},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }
        r = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=20,
        )
        r.raise_for_status()

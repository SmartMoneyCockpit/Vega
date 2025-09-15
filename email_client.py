import os
from typing import Optional

class EmailClient:
    """Dead-simple SendGrid wrapper; avoids fancy deps/HTML by default."""
    def __init__(self, api_key: str, from_addr: str, to_addr: str):
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        self._sg = SendGridAPIClient(api_key)
        self._from = from_addr
        self._to = to_addr
        self._Mail = Mail

    def send(self, subject: str, body: str, html: Optional[str] = None):
        msg = self._Mail(from_email=self._from, to_emails=self._to,
                         subject=subject, plain_text_content=body,
                         html_content=html or None)
        self._sg.send(msg)

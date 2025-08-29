# scripts/notify.py
import sys
from utils.emailer import send_email

if __name__ == "__main__":
    subject = sys.argv[1] if len(sys.argv) > 1 else "Vega Action Notice"
    body    = sys.argv[2] if len(sys.argv) > 2 else "(no body)"
    send_email(subject, body)

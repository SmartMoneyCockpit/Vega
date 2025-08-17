# jobs/test_alert.py
import datetime as dt, socket, os, json
from vega_monitor.alerts import send_email, send_webhook

def main():
    now = dt.datetime.now().isoformat(timespec="seconds")
    host = socket.gethostname()

    # Email test
    subject = "VEGA ALERT — Test Trigger (Email OK)"
    body = (
        f"Test alert from Vega at {now}\n"
        f"Host: {host}\n\n"
        "This is a simulated notification to confirm Gmail SMTP works.\n"
        "If you see this, your VEGA_EMAIL_* env vars are correct.\n\n"
        f"Env check:\n"
        f"VEGA_EMAIL_HOST={os.getenv('VEGA_EMAIL_HOST')}\n"
        f"VEGA_EMAIL_USER={os.getenv('VEGA_EMAIL_USER')}\n"
        f"VEGA_EMAIL_TO={os.getenv('VEGA_EMAIL_TO')}\n"
    )
    send_email(subject, body)

    # Optional: webhook test (safe if no webhook set)
    send_webhook({
        "type": "test_alert",
        "message": "Vega webhook channel reachable",
        "timestamp": now,
        "host": host,
    })

if __name__ == "__main__":
    main()

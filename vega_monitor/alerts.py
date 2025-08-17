import smtplib, os, requests

def send_webhook(payload):
    url = os.getenv("VEGA_WEBHOOK_URL")
    if not url: return
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def send_email(subj, body):
    host=os.getenv("VEGA_EMAIL_HOST"); port=int(os.getenv("VEGA_EMAIL_PORT","465"))
    user=os.getenv("VEGA_EMAIL_USER"); pwd=os.getenv("VEGA_EMAIL_PASS"); to=os.getenv("VEGA_EMAIL_TO")
    if not (host and user and pwd and to): return
    msg=f"From: {user}\nTo: {to}\nSubject: {subj}\n\n{body}"
    with smtplib.SMTP_SSL(host, port, timeout=10) as s:
        s.login(user, pwd); s.sendmail(user, [to], msg)

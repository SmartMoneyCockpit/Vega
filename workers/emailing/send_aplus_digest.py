import os
from datetime import datetime
from modules.emailing.aplus_digest import build_digest

def get_setups():
    if datetime.utcnow().minute % 2 == 0:
        return []
    return [{
        "ticker":"SPY",
        "entry":"$500.00",
        "stop":"$495.00",
        "rr":"3.0",
        "reason":"Momentum + RS breadth confluence"
    }]

def send_email(subject, body):
    key = os.getenv("SENDGRID_API_KEY")
    to = os.getenv("ALERTS_TO")
    from_ = os.getenv("ALERTS_FROM")
    if not key or not to or not from_:
        print("[digest] Email not configured; printing only.")
        print(subject); print(body)
        return False
    try:
        import requests
        data = {
          "personalizations":[{"to":[{"email":to}]}],
          "from":{"email":from_},
          "subject":subject,
          "content":[{"type":"text/plain","value":body}]
        }
        r = requests.post("https://api.sendgrid.com/v3/mail/send", json=data, headers={"Authorization": f"Bearer {key}"})
        print("[digest] SendGrid:", r.status_code, r.text[:200])
        return r.status_code in (200,202)
    except Exception as e:
        print("[digest] email error:", e)
        return False

def main():
    setups = get_setups()
    if not setups:
        print("[digest] No A+ setups; silent.")
        return
    body = build_digest(setups)
    send_email("A+ Setups Digest", body)

if __name__ == "__main__":
    main()

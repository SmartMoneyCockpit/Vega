# alerts/digest.py
import os, datetime as dt
from utils.store import list_fired_alerts  # your DB/sheets/logs
from utils.mail import send_email

def build_digest(lookback="1d"):
    rows = list_fired_alerts(lookback=lookback)
    if not rows:
        return "No actionable alerts in the last 24h."
    out = ["Actionable Alerts Digest", ""]
    for r in rows:
        out.append(f"- {r['ts']} | {r['id']} | {r['summary']}")
    return "\n".join(out)

if __name__ == "__main__":
    body = build_digest(os.getenv("DIGEST_LOOKBACK","1d"))
    print(body)
    # only send when you ask; keep this print-only by default

import os, yaml
from datetime import datetime
from pathlib import Path
import pandas as pd

SETTINGS = yaml.safe_load(Path("config/settings.yaml").read_text()) if Path("config/settings.yaml").exists() else {}

def region_open_now():
    now = datetime.utcnow()
    if now.weekday() >= 5:
        return False
    return 13 <= now.hour <= 20

def load_sector_df():
    sectors = ["Technology","Financials","Healthcare","Energy","Consumer","Industrials","Utilities","Materials","Real Estate","Communication"]
    import random
    return pd.DataFrame({"Sector": sectors, "Change%":[round(random.uniform(-1.2,1.2),2) for _ in sectors]})

def detect_flips(df, threshold):
    flips = []
    for _, row in df.iterrows():
        chg = row.get("Change%", 0)/100 if abs(row.get("Change%",0))>1 else row.get("Change%",0)
        if chg >= threshold:
            flips.append((row["Sector"], "BUY"))
        elif chg <= -threshold:
            flips.append((row["Sector"], "AVOID"))
    return flips

def send_email(subject, body):
    key = os.getenv("SENDGRID_API_KEY")
    to = os.getenv("ALERTS_TO")
    from_ = os.getenv("ALERTS_FROM")
    if not key or not to or not from_:
        print("[alerts] Email not configured; logs only.")
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
        print("[alerts] SendGrid:", r.status_code, r.text[:200])
        return r.status_code in (200,202)
    except Exception as e:
        print("[alerts] email error:", e)
        return False

def main():
    if not region_open_now():
        print("[alerts] Region closed.")
        return
    thr = SETTINGS.get("alerts",{}).get("sector_flip",{}).get("rel_change_threshold",0.006)
    df = load_sector_df()
    flips = detect_flips(df, thr)
    if not flips:
        print("[alerts] No flips.")
        return
    ts = datetime.utcnow().isoformat()
    body = "\n".join([f"{ts} — {s}: {status}" for s,status in flips])
    send_email("Sector Flip Alerts", body)

if __name__ == "__main__":
    main()

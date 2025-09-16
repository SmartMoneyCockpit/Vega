import os, json, yaml
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

SETTINGS = yaml.safe_load(Path("config/settings.yaml").read_text()) if Path("config/settings.yaml").exists() else {}
STATE_PATH = Path(".state/sector_flips.json")
STATE = {"history": {}, "last_sent": {}}
if STATE_PATH.exists():
    try: STATE = json.loads(STATE_PATH.read_text())
    except Exception: pass

def region_open_now():
    now = datetime.utcnow()
    if now.weekday() >= 5: return False
    return (now.hour > 13 or (now.hour == 13 and now.minute >= 30)) and now.hour <= 20

def load_sector_df():
    sectors = ["Technology","Financials","Healthcare","Energy","Consumer","Industrials","Utilities","Materials","Real Estate","Communication"]
    import random
    return pd.DataFrame({"Sector": sectors, "Change%":[round(random.uniform(-1.5,1.5),2) for _ in sectors]})

def ema(series, span): return series.ewm(span=span, adjust=False).mean()

def detect_flips(df):
    thr = SETTINGS.get("alerts",{}).get("sector_flip",{}).get("rel_change_threshold",0.006)
    confirm_min = SETTINGS.get("alerts",{}).get("sector_flip",{}).get("confirm_minutes", 15)
    fast = SETTINGS.get("alerts",{}).get("sector_flip",{}).get("momentum_ema_fast",10)
    slow = SETTINGS.get("alerts",{}).get("sector_flip",{}).get("momentum_ema_slow",30)

    flips = []
    now = datetime.now(timezone.utc)
    for _, row in df.iterrows():
        sector = row["Sector"]
        chg = row.get("Change%", 0)/100 if abs(row.get("Change%",0))>1 else row.get("Change%",0)
        hist = STATE["history"].get(sector, [])
        hist.append({"ts": now.isoformat(), "chg": chg})
        hist = hist[-36:]
        STATE["history"][sector] = hist

        import pandas as pd
        ser = pd.Series([h["chg"] for h in hist])
        if len(ser) >= slow:
            momentum_cross = (ema(ser, fast).iloc[-1] - ema(ser, slow).iloc[-1]) > 0
        else:
            momentum_cross = False

        confirm_points = max(1, confirm_min // 5)
        sustained = len(hist) >= confirm_points and (all(x["chg"] >= thr for x in hist[-confirm_points:]) or all(x["chg"] <= -thr for x in hist[-confirm_points:]))
        status = None
        if sustained or momentum_cross:
            if chg >= thr or momentum_cross: status = "🟢 Buy Today"
            if chg <= -thr or (momentum_cross and chg < 0): status = "🔴 Avoid"
        if status:
            last_sent = STATE["last_sent"].get(sector, {})
            last_time = last_sent.get(status)
            if not last_time or (now - datetime.fromisoformat(last_time)) >= timedelta(minutes=30):
                flips.append((sector, status))
                last_sent[status] = now.isoformat()
                STATE["last_sent"][sector] = last_sent
    STATE_PATH.write_text(json.dumps(STATE))
    return flips

def send_email(subject, body):
    key, to, frm = os.getenv("SENDGRID_API_KEY"), os.getenv("ALERTS_TO"), os.getenv("ALERTS_FROM")
    if not key or not to or not frm:
        print("[alerts] Email not configured; logs only."); print(subject); print(body); return False
    try:
        import requests
        r = requests.post("https://api.sendgrid.com/v3/mail/send",
                          json={"personalizations":[{"to":[{"email":to}]}],
                                "from":{"email":frm},
                                "subject":subject,
                                "content":[{"type":"text/plain","value":body}]},
                          headers={"Authorization": f"Bearer {key}"})
        print("[alerts] SendGrid:", r.status_code, r.text[:200]); return r.status_code in (200,202)
    except Exception as e:
        print("[alerts] email error:", e); return False

def main():
    if not region_open_now(): print("[alerts] Region closed."); return
    df = load_sector_df(); flips = detect_flips(df)
    if not flips: print("[alerts] No flips."); return
    ts = datetime.now(timezone.utc).isoformat()
    body = "\n".join([f"{ts} — {s}: {status}" for s,status in flips])
    send_email("Sector Flip Alerts", body)

if __name__ == "__main__": main()

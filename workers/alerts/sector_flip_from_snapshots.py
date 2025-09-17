import json, os
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import requests

STATE = Path(".state/sector_flips.json"); STATE.parent.mkdir(parents=True, exist_ok=True)

def load_df(region):
    p = Path(f"data/snapshots/{region}_indices.csv")
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

def compute_status(df):
    out = {}
    for _, r in df.iterrows():
        sym = str(r.get("symbol",""))
        try:
            rs = float(r.get("rs",0) or 0)
        except Exception:
            rs = 0.0
        try:
            chg = float(r.get("chg_1d",0) or 0)/100.0
        except Exception:
            chg = 0.0
        status = "WAIT"
        if chg >= 0.006 or rs > 0.0:
            status = "BUY"
        if chg <= -0.006 and rs < 0.0:
            status = "AVOID"
        out[sym] = status
    return out

def send(subject, body):
    key=os.getenv("SENDGRID_API_KEY"); to=os.getenv("ALERTS_TO"); frm=os.getenv("ALERTS_FROM")
    if not key or not to or not frm:
        print("[flips] Missing email secrets; printing only."); print(body); return False
    r = requests.post("https://api.sendgrid.com/v3/mail/send",
                      json={"personalizations":[{"to":[{"email":to}]}],
                            "from":{"email":frm},"subject":subject,
                            "content":[{"type":"text/plain","value":body}]},
                      headers={"Authorization": f"Bearer {key}"})
    print("[flips] status:", r.status_code, r.text[:200]); return r.status_code in (200,202)

def main():
    old = json.loads(STATE.read_text()) if STATE.exists() else {}
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    messages = []

    for region in ["na","eu","apac"]:
        df = load_df(region)
        if df.empty: continue
        cur = compute_status(df)
        prev = old.get(region, {})
        for sym, status in cur.items():
            if prev.get(sym) != status and status in ("BUY","AVOID"):
                emoji = "🟢" if status=="BUY" else "🔴"
                messages.append(f"{ts} — {region.upper()} {sym}: {emoji} {status}")
        old[region] = cur

    if messages:
        body="\n".join(messages)
        send("Sector Flip Alerts (Hourly)", body)
    STATE.write_text(json.dumps(old))

if __name__ == "__main__":
    main()

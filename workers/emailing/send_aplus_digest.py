import os, pandas as pd
from pathlib import Path
from modules.emailing.aplus_digest import build_digest

SOURCE = "data/aplus_setups.csv"
cfg_path = Path("config/settings.yaml")
if cfg_path.exists():
    import yaml
    cfg = yaml.safe_load(cfg_path.read_text()) or {}
    SOURCE = cfg.get("email",{}).get("aplus_digest",{}).get("source_csv", SOURCE)

def get_setups_from_csv():
    if not Path(SOURCE).exists(): return []
    try:
        df = pd.read_csv(SOURCE)
        df = df[df.get("grade","").astype(str).str.upper().str.contains("A\+")]
        return [{
            "ticker": str(r.get("ticker","")).strip(),
            "entry": str(r.get("entry","")).strip(),
            "stop": str(r.get("stop","")).strip(),
            "rr": str(r.get("rr","")).strip(),
            "reason": str(r.get("reason","")).strip(),
        } for _, r in df.iterrows()]
    except Exception as e:
        print("[digest] CSV read error:", e); return []

def send_email(subject, body):
    key, to, frm = os.getenv("SENDGRID_API_KEY"), os.getenv("ALERTS_TO"), os.getenv("ALERTS_FROM")
    if not key or not to or not frm:
        print("[digest] Email not configured; printing only."); print(subject); print(body); return False
    try:
        import requests
        r = requests.post("https://api.sendgrid.com/v3/mail/send",
                          json={"personalizations":[{"to":[{"email":to}]}],
                                "from":{"email":frm},
                                "subject":subject,
                                "content":[{"type":"text/plain","value":body}]},
                          headers={"Authorization": f"Bearer {key}"})
        print("[digest] SendGrid:", r.status_code, r.text[:200]); return r.status_code in (200,202)
    except Exception as e:
        print("[digest] email error:", e); return False

def main():
    setups = get_setups_from_csv()
    if not setups: print("[digest] No A+ setups; silent."); return
    body = build_digest(setups); send_email("A+ Setups Digest", body)

if __name__ == "__main__": main()

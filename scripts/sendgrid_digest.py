
from __future__ import annotations
import os, json, datetime as dt

def build_digest():
    p = os.path.join("data","aplus_setups.csv")
    if not os.path.exists(p):
        return None
    try:
        import pandas as pd
        df = pd.read_csv(p)
        if df.empty:
            return None
        # Minimal HTML
        rows = "".join([f"<tr><td>{r.symbol}</td><td>{r.entry}</td><td>{r.stop}</td><td>{r.rr}</td><td>{r.reason}</td></tr>" for r in df.itertuples(index=False)])
        return f"""<h2>A+ Setups — {dt.date.today()}</h2>
        <table border='1' cellspacing='0' cellpadding='6'>
          <tr><th>Ticker</th><th>Entry</th><th>Stop</th><th>R/R</th><th>Reason</th></tr>
          {rows}
        </table>"""
    except Exception:
        return None

def send_via_sendgrid(html: str) -> bool:
    api_key = os.getenv("SENDGRID_API_KEY")
    to_email = os.getenv("DIGEST_TO_EMAIL")
    from_email = os.getenv("DIGEST_FROM_EMAIL", to_email or "no-reply@vega.local")
    if not api_key or not to_email:
        return False
    try:
        import requests
        r = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type":"application/json"},
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": from_email},
                "subject": f"A+ Setups — {dt.date.today()}",
                "content": [{"type":"text/html", "value": html}]
            }
        )
        return 200 <= r.status_code < 300
    except Exception:
        return False

def main():
    html = build_digest()
    if not html:
        return 0
    ok = send_via_sendgrid(html)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())

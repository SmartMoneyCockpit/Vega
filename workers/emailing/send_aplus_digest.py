import os, pandas as pd, requests

SOURCE = "data/aplus_setups.csv"

def send(subject, body):
    key=os.getenv("SENDGRID_API_KEY"); to=os.getenv("ALERTS_TO"); frm=os.getenv("ALERTS_FROM")
    if not key or not to or not frm:
        print("[digest] Missing email secrets; printing only."); print(body); return False
    r = requests.post("https://api.sendgrid.com/v3/mail/send",
                      json={"personalizations":[{"to":[{"email":to}]}],
                            "from":{"email":frm},"subject":subject,
                            "content":[{"type":"text/plain","value":body}]},
                      headers={"Authorization": f"Bearer {key}"})
    print("[digest] status:", r.status_code, r.text[:200]); return r.status_code in (200,202)

def main():
    if not os.path.exists(SOURCE):
        print("[digest] no CSV; exit."); return
    df=pd.read_csv(SOURCE)
    if df.empty: print("[digest] empty CSV; exit."); return
    df = df[df.get("grade","").astype(str).upper().str.contains("A\+")]
    if df.empty: print("[digest] no A+ rows; silent."); return
    lines=[f"- {r['symbol']}: entry {r.get('entry','?')} stop {r.get('stop','?')} R/R {r.get('rr','?')}" for _,r in df.iterrows()]
    body="\n".join(lines)
    send("A+ Setups Digest", body)

if __name__ == "__main__":
    main()

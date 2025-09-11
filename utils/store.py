# utils/store.py
from pathlib import Path
import json, time, datetime as dt

LOG = Path(".state/fired_alerts.jsonl")
LOG.parent.mkdir(parents=True, exist_ok=True)

def log_fired(rule_id: str, summary: str):
    row = {"ts": dt.datetime.utcnow().isoformat(timespec="seconds")+"Z",
           "id": rule_id, "summary": summary, "t": time.time()}
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row)+"\n")

def list_fired_alerts(lookback="1d"):
    # simple parser: supports "Nh" or "Nd"
    n = int(lookback[:-1]); unit = lookback[-1].lower()
    horizon = time.time() - (n*3600 if unit=="h" else n*86400)
    rows = []
    if LOG.exists():
        with LOG.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    j = json.loads(line)
                    if j.get("t", 0) >= horizon:
                        rows.append(j)
                except: pass
    return rows

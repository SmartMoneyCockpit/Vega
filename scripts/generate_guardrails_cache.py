import os, json, time
base = os.path.join("vault","cache")
os.makedirs(base, exist_ok=True)
payload = {
  "ts": time.time(),
  "exposure": {"Technology": 0.28, "Financials": 0.18, "Energy": 0.12},
  "alerts": [
    {"type":"sector_overweight","sector":"Technology","threshold":0.25,"value":0.28}
  ]
}
with open(os.path.join(base,"guardrails.json"),"w") as f:
  json.dump(payload, f, indent=2)
print("Guardrails cache generated.")

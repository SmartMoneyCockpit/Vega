import os, json, time
out = os.path.join("vault","cache","rotation_triggers.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
payload = {"ts": time.time(), "preferred_income_basket":"HOLD", "notes":"Yield stable; no cross-basket reversal."}
json.dump(payload, open(out,"w"), indent=2)
print("Capital rotation triggers updated.")

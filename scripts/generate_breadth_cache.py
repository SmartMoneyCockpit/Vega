import os, json, time
base = os.path.join("vault","cache")
os.makedirs(base, exist_ok=True)
with open(os.path.join(base,"breadth_adv.json"),"w") as f:
    json.dump({"value": 1800, "ts": time.time()}, f)
with open(os.path.join(base,"breadth_dec.json"),"w") as f:
    json.dump({"value": 1600, "ts": time.time()}, f)
with open(os.path.join(base,"breadth_hilo.json"),"w") as f:
    json.dump({"value": "52H: 120 / 52L: 85", "ts": time.time()}, f)
with open(os.path.join(base,"breadth_sector.json"),"w") as f:
    json.dump({"rows":[["Technology",52,0.98],["Financials",48,0.92],["Energy",55,1.04]]}, f)
print("Breadth cache generated.")

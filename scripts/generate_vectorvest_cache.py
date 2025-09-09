import os, json, time
base = os.path.join("vault","cache")
os.makedirs(base, exist_ok=True)
with open(os.path.join(base,"vectorvest_signals.json"),"w") as f:
    json.dump({"signals":[{"ticker":"SPY","status":"WAIT"},{"ticker":"SQQQ","status":"READY"},{"ticker":"RWM","status":"WATCH"}], "ts":time.time()}, f)
print("VectorVest cache generated.")

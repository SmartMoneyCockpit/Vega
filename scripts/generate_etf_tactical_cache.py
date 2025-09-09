import os, json, time
base = os.path.join("vault","cache")
os.makedirs(base, exist_ok=True)
with open(os.path.join(base,"etf_tactical.json"),"w") as f:
    json.dump({"signals":[{"ticker":"SPXU","action":"ALERT"},{"ticker":"SQQQ","action":"ALERT"},{"ticker":"RWM","action":"WATCH"}], "ts":time.time()}, f)
print("ETF Tactical cache generated.")

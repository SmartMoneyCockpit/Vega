import os, json, time
# Simple logic using risk flag; expand later
risk_off = os.path.exists(os.path.join("vault","cache","risk_off.flag"))
ideas = []
if risk_off:
    ideas = [{"ticker":"SPXU","action":"ALERT"},{"ticker":"SQQQ","action":"ALERT"},{"ticker":"RWM","action":"WATCH"}]
out = {"ts": time.time(), "status":"SHOW" if risk_off else "HIDE", "ideas": ideas}
json.dump(out, open(os.path.join("vault","cache","hedge_ideas.json"),"w"), indent=2)
print("Hedging engine output written.")

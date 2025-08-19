\
import os, yaml
from datetime import timedelta
from utils import now_pt, pct_from_prev_close, last_price, fmt_num
from email_webhook import broadcast

def pct(t): 
    try: return pct_from_prev_close(t)
    except: return None

now = now_pt()

# Benchmarks & FX
data = {
    "SPY": pct("SPY"),
    "QQQ": pct("QQQ"),
    "DIA": pct("DIA"),
    "IWM": pct("IWM"),
    "^GSPTSE": pct("^GSPTSE"),
    "^MXX": pct("^MXX"),
    "UVXY": pct("UVXY"),
    "SVIX": pct("SVIX"),
    "^VIX":  last_price("^VIX"),
    "CAD=X": pct("CAD=X"),
    "MXN=X": pct("MXN=X"),
    "DXY":   last_price("DX-Y.NYB") or last_price("DXY"),
    "^TNX":  last_price("^TNX"),  # 10y yield *10
}

# Breadth proxy
spy = pct("SPY"); rsp = pct("RSP")
breadth_note = "OK"
if spy is not None and rsp is not None:
    if (spy * rsp < 0) or (abs(spy - rsp) > 0.50):
        breadth_note = "Divergence"

# Volatility sentiment
vol_label = "Neutral"
uvxy = data["UVXY"]; svix = data["SVIX"]
if uvxy is not None and uvxy>0 and svix is not None and svix<0:
    vol_label = "Rising"
elif uvxy is not None and uvxy<0 and svix is not None and svix>0:
    vol_label = "Easing"

# Optional Calendar (manual)
calendar = []
try:
    with open("calendar.yaml","r") as f:
        payload = yaml.safe_load(f) or {}
    for ev in payload.get("events",[]):
        if str(ev.get("date")) == now.strftime("%Y-%m-%d"):
            calendar.append(f"- {ev.get('time','')} {ev.get('title','')} ({ev.get('region','')})")
except Exception:
    pass

def line(label, val):
    return f"- {label}: {val}"

report = []
report.append(f"# 📊 North American Morning Report\n**Date:** {now.strftime('%a, %b %d, %Y')} — **Time:** {now.strftime('%H:%M %Z')}\n")
report.append("## 🌍 Global Macro\n- Tone: Cautious into events; oil/gold watch; volatility checkpoint.\n")

report.append("## 🇺🇸 USA\n" + "\n".join([
    line("SPY %", fmt_num(data['SPY'])),
    line("QQQ %", fmt_num(data['QQQ'])),
    line("^VIX", fmt_num(data['^VIX'])),
]))

report.append("## 🇨🇦 Canada\n" + "\n".join([
    line("TSX (^GSPTSE) %", fmt_num(data['^GSPTSE'])),
]))

report.append("## 🇲🇽 Mexico\n" + "\n".join([
    line("IPC (^MXX) %", fmt_num(data['^MXX'])),
]))

report.append("## 🌎 Latin America (ex‑Mexico)\n- Use EWZ/EWC/EWW as quick proxies when needed.\n")

report.append("## 🔍 Sector & Thematic Pulse\n- Tech leadership bias; energy/defensives per oil/VIX.\n")

report.append("## 💱 FX & Rates\n" + "\n".join([
    line("USD/CAD %", fmt_num(data['CAD=X'])),
    line("USD/MXN %", fmt_num(data['MXN=X'])),
    line("DXY", fmt_num(data['DXY'])),
    line("U.S. 10Y (^TNX/10)", fmt_num(data['^TNX'])),
]))

report.append("## ⚡ Volatility Sentiment (UVXY vs SVIX)\n" + f"- {vol_label} — UVXY {fmt_num(uvxy)}% / SVIX {fmt_num(svix)}%\n")

report.append("## 📈 Breadth & Internals\n" + f"- {breadth_note} (SPY vs RSP)\n")

report.append("## 🛡️ Risk & Hedge Dashboard\n- VIX bands: >20 🔴, <15 🟢. Hedges: SPXU/SQQQ/RWM (size per breadth).\n")

report.append("## 🔎 Benchmark Relative Strength\n- SPY vs QQQ vs DIA vs IWM; TSX & IPC for region.\n")

report.append("## 📅 Today’s Key Events\n" + ("\n".join(calendar) if calendar else "- (Add items in calendar.yaml)\n"))

# Verdict logic (simple, event‑aware)
verdict_usa = "🟡 Wait / stock‑specific"
if data["^VIX"] and data["^VIX"]>20: verdict_usa = "🔴 Avoid broad; hedge"
if vol_label == "Easing" and breadth_note == "OK": verdict_usa = "🟢 Tradable (light)"

verdict_can = "🟡 Wait"
verdict_mex = "🟡 Wait"

report.append("## 🟢🟡🔴 Smart Money Verdict\n" + "\n".join([
    f"- USA: {verdict_usa}",
    f"- Canada: {verdict_can}",
    f"- Mexico: {verdict_mex}",
]))

text = "\n".join(report)
print(text)
broadcast("North American Morning Report", text)

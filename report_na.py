\
import os, yaml
from datetime import timedelta
from utils import now_pt, pct_from_prev_close, last_price, fmt_num
from email_webhook import broadcast

def pct(t): 
    try: return pct_from_prev_close(t)
    except: return None

1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
\
import os, yaml
from utils import now_pt, pct_from_prev_close, last_price, fmt_num
from email_webhook import broadcast

def pct(t): 
    try: return pct_from_prev_close(t)
    except: return None

PT = pytz.timezone('UTC')
now = now_pt()

# Benchmarks & FX
data = {
    "^N225": pct("^N225"),      # Nikkei 225
    "^AXJO": pct("^AXJO"),      # ASX 200
    "000300.SS": pct("000300.SS"),  # CSI 300
    "^HSI": pct("^HSI"),        # Hang Seng
    "^KS11": pct("^KS11"),      # KOSPI
    "USDJPY": pct("JPY=X"),
    "AUDUSD": pct("AUDUSD=X"),
    "USDCNH": pct("CNH=X"),
    "USDKRW": pct("KRW=X"),
}

# Volatility link: use USDJPY swings as primary macro proxy
vol_label = "Neutral"
if data["USDJPY"] is not None and abs(data["USDJPY"]) >= 1.0:
    vol_label = "Rising" if data["USDJPY"]>0 else "Easing"

report = []
report.append(f"# 🌏 Asia‑Pacific Afternoon Report\n**Date:** {now.strftime('%a, %b %d, %Y')} — **Time:** {now.strftime('%H:%M %Z')}\n")

report.append("## 🌍 Global/Overnight Macro\n- NY close tone, yields, and any cross‑over drivers.\n")

report.append("## 🇯🇵 Japan\n" + "\n".join([
    f"- Nikkei (^N225) %: {fmt_num(data['^N225'])}",
    f"- USD/JPY %: {fmt_num(data['USDJPY'])}",
]))

report.append("## 🇦🇺 Australia\n" + "\n".join([
    f"- ASX 200 (^AXJO) %: {fmt_num(data['^AXJO'])}",
    f"- AUD/USD %: {fmt_num(data['AUDUSD'])}",
]))

report.append("## 🇨🇳 China & 🇭🇰 Hong Kong\n" + "\n".join([
    f"- CSI 300 (000300.SS) %: {fmt_num(data['000300.SS'])}",
    f"- Hang Seng (^HSI) %: {fmt_num(data['^HSI'])}",
    f"- USD/CNH %: {fmt_num(data['USDCNH'])}",
]))

report.append("## 🇰🇷 South Korea\n" + "\n".join([
    f"- KOSPI (^KS11) %: {fmt_num(data['^KS11'])}",
    f"- USD/KRW %: {fmt_num(data['USDKRW'])}",
]))

report.append("## 🔍 Sector & Thematic Pulse\n- Tech/semis vs commodities; consumer tone by FX.\n")

report.append("## 💱 FX & Rates\n- USDJPY, AUDUSD, USDCNH, USDKRW checkpoints.\n")

report.append("## ⚡ Volatility Sentiment\n" + f"- {vol_label} — USDJPY %: {fmt_num(data['USDJPY'])}\n")

report.append("## 📈 Breadth & Internals\n- Use local A/D when available; otherwise price/volume proxies.\n")

report.append("## 🛡️ Risk & Hedge Dashboard\n- USDJPY vol spike → risk‑off. Hedge via region‑appropriate ETFs.\n")

report.append("## 🔎 Benchmark Relative Strength\n- Nikkei vs ASX vs CSI 300 vs Hang Seng vs KOSPI.\n")

report.append("## 📅 Today’s Key Events\n- See country calendars; optionally extend via APIs.\n")

verdict = "🟡 Wait / stock‑specific"
if vol_label == "Rising":
    verdict = "🔴 Defensive / risk‑off"
elif vol_label == "Easing":
    verdict = "🟢 Tactical long bias (light)"

report.append("## 🟢🟡🔴 Smart Money Verdict\n" + f"- APAC: {verdict}\n")

text = "\n".join(report)
print(text)
broadcast("Asia‑Pacific Afternoon Report", text)

Use Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc 
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

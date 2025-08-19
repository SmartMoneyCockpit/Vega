\
import os, datetime as dt, pytz, requests, yfinance as yf

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

def now_pt():
    return dt.datetime.now(PT)

def in_us_window(ts=None):
    """US trading window 06:00–14:00 PT Mon–Fri"""
    ts = ts or now_pt()
    return ts.weekday() <= 4 and 6 <= ts.hour < 14

def in_apac_window(ts=None):
    """APAC window 18:00–22:00 PT daily"""
    ts = ts or now_pt()
    return 18 <= ts.hour < 22

def last_price(ticker):
    df = yf.download(ticker, period="1d", interval="1m", progress=False, auto_adjust=False)
    if df.empty: return None
    return float(df["Close"].dropna().iloc[-1])

def prev_close(ticker):
    df = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
    if df.empty or len(df["Close"]) < 2: return None
    return float(df["Close"].iloc[-2])

def pct_from_prev_close(ticker):
    p0 = prev_close(ticker); p = last_price(ticker)
    if p0 is None or p is None: return None
    return (p/p0 - 1.0) * 100.0

def fmt_num(x, n=2):
    return "n/a" if x is None else f"{x:.{n}f}"

def fetch_gist(gist_id, token):
    try:
        r = requests.get(f"https://api.github.com/gists/{gist_id}", headers={"Authorization": f"token {token}"} ,timeout=10)
        if r.status_code != 200: return None
        data = r.json()
        files = data.get("files",{})
        if "alerts_log.txt" in files and "content" in files["alerts_log.txt"]:
            return files["alerts_log.txt"]["content"]
    except Exception:
        return None
    return None

def append_gist(gist_id, token, line):
    try:
        existing = fetch_gist(gist_id, token) or ""
        new_content = (existing + ("\n" if existing else "") + line)
        payload = {"files": {"alerts_log.txt": {"content": new_content}}}
        r = requests.patch(f"https://api.github.com/gists/{gist_id}", headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }, json=payload, timeout=10)
        return r.status_code in (200,201)
    except Exception:
        return False

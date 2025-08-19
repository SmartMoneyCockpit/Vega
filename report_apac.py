\
import os, yaml
from utils import now_pt, pct_from_prev_close, last_price, fmt_num
from email_webhook import broadcast

def pct(t): 
    try: return pct_from_prev_close(t)
    except: return None

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

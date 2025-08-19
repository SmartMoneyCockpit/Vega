\
import os
from datetime import datetime
import pytz
import yfinance as yf
from utils import now_pt, in_us_window, in_apac_window, pct_from_prev_close, last_price, fmt_num, append_gist
from email_webhook import broadcast

PT = pytz.timezone(os.getenv("TZ_PREF","America/Los_Angeles"))
now = now_pt()

# Only act during target windows to reduce noise
if not (in_us_window(now) or in_apac_window(now)):
    print("Outside trading windows; exiting.")
    raise SystemExit(0)

def get_pct(t):
    try:
        return pct_from_prev_close(t)
    except Exception:
        return None

uvxy = get_pct("UVXY")
svix = get_pct("SVIX")
vix  = last_price("^VIX")
usdjpy = get_pct("JPY=X")

# Breadth proxy: SPY vs RSP
spy = get_pct("SPY")
rsp = get_pct("RSP")
breadth_div = None
if spy is not None and rsp is not None:
    breadth_div = (spy * rsp < 0) or (abs(spy - rsp) > 0.50)

trigs = []
if uvxy is not None and uvxy >= 5.0: trigs.append("UVXY ≥ +5%")
if svix is not None and svix <= -3.0: trigs.append("SVIX ≤ −3%")
if vix is not None and vix > 20: trigs.append("VIX > 20 (flip 🔴 Defensive)")
if vix is not None and vix < 15: trigs.append("VIX < 15 (flip 🟢 Calm)")
if usdjpy is not None and abs(usdjpy) >= 1.0: trigs.append("USDJPY ≥ ±1.0% (APAC link)")
if breadth_div: trigs.append("Breadth divergence (SPY vs RSP)")

if not trigs:
    print("No triggers.")
    raise SystemExit(0)

def suggestion():
    if (vix and vix>20) or (uvxy and uvxy>5) or (svix and svix<-3) or breadth_div:
        return "Tighten risk; consider SPXU/SQQQ/RWM per plan."
    if (vix and vix<15) and (svix and svix>0):
        return "Vol easing; relax hedges; tactical longs OK."
    return "Mixed; wait for breadth confirmation."

summary = (
    f"Vol/Hedge Monitor — {now.strftime('%Y-%m-%d %H:%M PT')}\n"
    f"Triggers: {', '.join(trigs)}\n"
    f"UVXY %: {fmt_num(uvxy)} | SVIX %: {fmt_num(svix)} | VIX: {fmt_num(vix)} | USDJPY %: {fmt_num(usdjpy)}\n"
    f"Breadth proxy (SPY vs RSP) %: {fmt_num(spy)} vs {fmt_num(rsp)}\n"
    f"Action: {suggestion()}"
)

# Optional gist logging
GIST_ID=os.getenv("GIST_ID"); GIST_TOKEN=os.getenv("GIST_TOKEN")
if GIST_ID and GIST_TOKEN:
    ts = now.strftime('%Y-%m-%d %H:%M:%S %Z')
    append_gist(GIST_ID, GIST_TOKEN, f"{ts} | {summary.replace(chr(10),' | ')}")

print(summary)
broadcast("Vol/Hedge Monitor Alert", summary)

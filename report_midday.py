# Vega — North American Midday Verdict
from utils import now_pt, pct_from_prev_close, last_price, fmt_num
from email_webhook import broadcast

UVXY_TRIG = 5.0
SVIX_TRIG = -3.0
VIX_DEFENSIVE = 20.0
VIX_CALM = 15.0
BREADTH_DELTA = 0.50  # SPY vs RSP divergence threshold (pct pts)

def pct(t):
    try:
        return pct_from_prev_close(t)
    except Exception:
        return None

now = now_pt()

# Snapshot
data = {
    "SPY": pct("SPY"),
    "QQQ": pct("QQQ"),
    "IWM": pct("IWM"),
    "RSP": pct("RSP"),         # equal-weight S&P (breadth proxy)
    "UVXY": pct("UVXY"),
    "SVIX": pct("SVIX"),
    "^VIX": last_price("^VIX"),
}

# Volatility tone
uvxy, svix, vix = data["UVXY"], data["SVIX"], data["^VIX"]
vol_note = "Neutral"
if uvxy is not None and uvxy >= UVXY_TRIG: vol_note = "Vol spike"
elif svix is not None and svix <= SVIX_TRIG: vol_note = "Vol-of-vol stress"
elif vix is not None and vix < VIX_CALM: vol_note = "Calm"
elif vix is not None and vix > VIX_DEFENSIVE: vol_note = "Defensive"

# Breadth (SPY vs RSP)
spy, rsp = data["SPY"], data["RSP"]
breadth_note = "n/a"
if spy is not None and rsp is not None:
    sign_diverge = (spy > 0 and rsp < 0) or (spy < 0 and rsp > 0)
    gap_diverge = abs(spy - rsp) > BREADTH_DELTA
    breadth_note = "Diverging" if (sign_diverge or gap_diverge) else "Aligned"

# Verdict
verdict = "🟡 Wait / stock-specific — mixed signals."
if vix is not None and vix > VIX_DEFENSIVE:
    verdict = "🔴 Defensive — keep hedges (SPXU/SQQQ/RWM), trim beta."
elif uvxy is not None and uvxy >= UVXY_TRIG or (svix is not None and svix <= SVIX_TRIG):
    verdict = "🟡/🔴 Caution — volatility rising; avoid new cap-weighted adds."
elif breadth_note == "Aligned" and vix is not None and vix < VIX_CALM:
    verdict = "🟢 Tradable (light) — breadth aligned & vol calm."

# Compose
lines = []
lines.append(f"# 🕛 North American Midday Verdict\n**Time:** {now.strftime('%a, %b %d %H:%M %Z')}\n")
lines.append(f"**Verdict:** {verdict}")
lines.append("\n**Snapshot**")
lines.append(f"- SPY %: {fmt_num(data['SPY'])} | QQQ %: {fmt_num(data['QQQ'])} | IWM %: {fmt_num(data['IWM'])}")
lines.append(f"- RSP % (breadth proxy): {fmt_num(data['RSP'])} → {breadth_note}")
lines.append(f"- VIX: {fmt_num(vix)}  |  UVXY %: {fmt_num(uvxy)}  |  SVIX %: {fmt_num(svix)}")
lines.append("\n**Note:** Breadth uses SPY vs RSP; adjust Δ threshold in code if needed.")
text = "\n".join(lines)

print(text)
broadcast("NA Midday Verdict", text)

"""
Vega Cockpit — Volatility & Hedge Monitor
Triggers (ANY):
  1) UVXY up ≥ +5% intraday vs prior close
  2) SVIX down ≤ −3% intraday vs prior close
  3) VIX > 20 (flip 🔴 Defensive) or VIX < 15 (flip 🟢 Calm)
  4) Breadth divergence (SPY vs RSP proxy): index up while breadth down, or vice versa
  5) USDJPY intraday move ≥ 1.0% (abs)

Outputs:
  - UVXY %, SVIX %, VIX level, USDJPY %, breadth quick read
  - One-line hedge / de-risk suggestion (cockpit rules)
"""

from __future__ import annotations
import os
from typing import List

from utils import (
    now_pt,
    in_us_window,
    in_apac_window,
    pct_from_prev_close,
    last_price,
    fmt_num,
    append_gist,
)
from email_webhook import broadcast

# =========================
# Tunables (easy to tweak)
# =========================
UVXY_TRIG = 5.0       # %
SVIX_TRIG = -3.0      # %
VIX_DEFENSIVE = 20.0  # level
VIX_CALM = 15.0       # level
USDJPY_TRIG = 1.0     # % (absolute)
BREADTH_DELTA = 0.50  # % absolute difference between SPY% and RSP% that flags divergence

# Windows: script *runs* anytime but only *acts* inside these (self-limited)
RESPECT_WINDOWS = True

# Force a one-off alert even if no triggers (for testing)
FORCE_ALERT = os.getenv("FORCE_ALERT") == "1"


def pct(ticker: str) -> float | None:
    try:
        return pct_from_prev_close(ticker)
    except Exception:
        return None


def fetch_snapshot():
    """Fetch all numbers we need. Keep network calls minimal."""
    data = {
        # Indices / breadth proxy
        "SPY": pct("SPY"),
        "RSP": pct("RSP"),

        # Volatility sleeve
        "UVXY": pct("UVXY"),
        "SVIX": pct("SVIX"),
        "VIX": last_price("^VIX"),

        # FX — USDJPY (Yahoo: JPY=X)
        "USDJPY": pct("JPY=X"),
    }
    return data


def detect_triggers(d: dict) -> List[str]:
    trigs: List[str] = []

    uvxy = d["UVXY"]
    if uvxy is not None and uvxy >= UVXY_TRIG:
        trigs.append(f"UVXY spike {uvxy:+.2f}% ≥ {UVXY_TRIG:.0f}%")

    svix = d["SVIX"]
    if svix is not None and svix <= SVIX_TRIG:
        trigs.append(f"SVIX drop {svix:+.2f}% ≤ {SVIX_TRIG:.0f}%")

    vix = d["VIX"]
    if vix is not None and (vix > VIX_DEFENSIVE or vix < VIX_CALM):
        if vix > VIX_DEFENSIVE:
            trigs.append(f"VIX {vix:.1f} > {VIX_DEFENSIVE:.0f} → 🔴 Defensive")
        elif vix < VIX_CALM:
            trigs.append(f"VIX {vix:.1f} < {VIX_CALM:.0f} → 🟢 Calm")

    # Breadth divergence via SPY vs RSP proxy
    spy, rsp = d["SPY"], d["RSP"]
    if spy is not None and rsp is not None:
        sign_diverge = (spy > 0 and rsp < 0) or (spy < 0 and rsp > 0)
        gap_diverge = abs(spy - rsp) > BREADTH_DELTA
        if sign_diverge or gap_diverge:
            trigs.append(
                f"Breadth divergence (SPY {spy:+.2f}% vs RSP {rsp:+.2f}%, Δ={abs(spy-rsp):.2f}%)"
            )

    # USDJPY absolute move
    uj = d["USDJPY"]
    if uj is not None and abs(uj) >= USDJPY_TRIG:
        dir_ = "↑" if uj > 0 else "↓"
        trigs.append(f"USDJPY {dir_} {uj:+.2f}% (≥ {USDJPY_TRIG:.1f}%)")

    return trigs


def hedge_suggestion(d: dict, trigs: List[str]) -> str:
    """Compact one-liner based on most severe condition."""
    vix = d["VIX"]
    uvxy, svix = d["UVXY"], d["SVIX"]
    spy, rsp = d["SPY"], d["RSP"]
    uj = d["USDJPY"]

    # Priority order
    if vix is not None and vix > VIX_DEFENSIVE:
        return "Flip dashboard to 🔴 Defensive — add/size hedges (SPXU/SQQQ/RWM), cut net, tighten stops."
    if uvxy is not None and uvxy >= UVXY_TRIG:
        return "Vol spike — trim beta, add tactical hedge, avoid new cap-weighted index adds."
    if svix is not None and svix <= SVIX_TRIG:
        return "Vol-of-vol stress — keep hedges on; bias stock-specific over broad beta."
    if spy is not None and rsp is not None and ((spy > 0 and rsp < 0) or (spy < 0 and rsp > 0) or abs(spy - rsp) > BREADTH_DELTA):
        return "Breadth diverging — favor equal-weight/quality; avoid chasing cap-weighted moves."
    if uj is not None and abs(uj) >= USDJPY_TRIG:
        return "USDJPY swing — watch APAC risk; de-risk semis/JP-linked exposure; keep hedges light-on."

    return "No action required — maintain positioning, monitor for follow-through."


def main():
    now = now_pt()

    # Respect market windows to avoid noisy hours (still allow FORCE_ALERT)
    if RESPECT_WINDOWS and not FORCE_ALERT:
        if not (in_us_window(now) or in_apac_window(now)):
            print("Outside monitoring windows — skipping.")
            return

    d = fetch_snapshot()
    trigs = detect_triggers(d)

    if not trigs and not FORCE_ALERT:
        print("No triggers.")
        return

    # Compose message
    lines = []
    lines.append("**Volatility & Hedge Monitor**")
    lines.append(f"**Time:** {now.strftime('%Y-%m-%d %H:%M %Z')}")
    if trigs:
        for t in trigs:
            lines.append(f"• **Trigger:** {t}")
    else:
        lines.append("• **Trigger:** (forced test alert)")

    lines.append("\n**Snapshot**")
    lines.append(f"- UVXY: {fmt_num(d['UVXY'])}%")
    lines.append(f"- SVIX: {fmt_num(d['SVIX'])}%")
    lines.append(f"- VIX:  {fmt_num(d['VIX'])}")
    lines.append(f"- USDJPY %: {fmt_num(d['USDJPY'])}")
    if d['SPY'] is not None and d['RSP'] is not None:
        lines.append(f"- Breadth proxy (SPY vs RSP): {fmt_num(d['SPY'])}% vs {fmt_num(d['RSP'])}%")

    suggestion = hedge_suggestion(d, trigs)
    lines.append(f"\n**Action:** {suggestion}")

    body = "\n".join(lines)

    # Send
    subject = "Vega Alert: Volatility/Hedge Monitor"
    try:
        broadcast(subject, body)
    except Exception as e:
        # Always print to logs so GH Actions shows content even if email/webhook fails
        print(f"[broadcast failed: {e}]")
        print(body)

    # Optional: append to gist for rolling history
    gid = os.getenv("GIST_ID")
    gtok = os.getenv("GIST_TOKEN")
    if gid and gtok:
        one_line = f"{now.isoformat()} | {'; '.join(trigs) if trigs else 'FORCED'} | UVXY {fmt_num(d['UVXY'])}% | SVIX {fmt_num(d['SVIX'])}% | VIX {fmt_num(d['VIX'])} | USDJPY {fmt_num(d['USDJPY'])}% | SPY {fmt_num(d['SPY'])}% vs RSP {fmt_num(d['RSP'])}%"
        try:
            append_gist(gid, gtok, one_line)
        except Exception:
            pass


if __name__ == "__main__":
    main()

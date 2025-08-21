"""
Vega Cockpit — Volatility & Hedge Monitor (with ENTER/EXIT + cooldown + state)

Triggers (ANY):
  1) UVXY up ≥ +5% intraday vs prior close
  2) SVIX down ≤ −3% intraday vs prior close
  3) VIX > 20 (flip 🔴 Defensive) or VIX < 15 (flip 🟢 Calm)
  4) Breadth divergence (SPY vs RSP proxy)
  5) USDJPY intraday move ≥ 1.0% (abs)

Env knobs (optional):
  WATCH_STATE_DIR       default ".vega_state"
  ALERT_COOLDOWN_MIN    default "15"  (minutes)
  FORCE_ALERT           "1" to force a test alert
"""

from __future__ import annotations
import os, json, time, pathlib
from typing import List, Dict, Any

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
# Tunables
# =========================
UVXY_TRIG = 5.0       # %  (>=)
SVIX_TRIG = -3.0      # %  (<=)
VIX_DEFENSIVE = 20.0  # level
VIX_CALM = 15.0       # level
USDJPY_TRIG = 1.0     # % (absolute)
BREADTH_DELTA = 0.50  # % abs gap between SPY% and RSP% flags divergence
RESPECT_WINDOWS = True

FORCE_ALERT = os.getenv("FORCE_ALERT") == "1"

STATE_DIR = pathlib.Path(os.getenv("WATCH_STATE_DIR", ".vega_state"))
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "defense_state.json"
ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_MIN", "15")) * 60  # default 15 min

def pct(ticker: str) -> float | None:
    try:
        return pct_from_prev_close(ticker)
    except Exception:
        return None

def fetch_snapshot() -> Dict[str, Any]:
    return {
        "SPY": pct("SPY"),
        "RSP": pct("RSP"),
        "UVXY": pct("UVXY"),
        "SVIX": pct("SVIX"),
        "VIX":  last_price("^VIX"),
        "USDJPY": pct("JPY=X"),
    }

def detect_triggers(d: dict) -> List[str]:
    trigs: List[str] = []
    uvxy = d.get("UVXY")
    if uvxy is not None and uvxy >= UVXY_TRIG:
        trigs.append(f"UVXY spike {uvxy:+.2f}% ≥ {UVXY_TRIG:.0f}%")
    svix = d.get("SVIX")
    if svix is not None and svix <= SVIX_TRIG:
        trigs.append(f"SVIX drop {svix:+.2f}% ≤ {SVIX_TRIG:.0f}%")
    vix = d.get("VIX")
    if vix is not None:
        if vix > VIX_DEFENSIVE:
            trigs.append(f"VIX {vix:.1f} > {VIX_DEFENSIVE:.0f} → 🔴 Defensive")
        elif vix < VIX_CALM:
            trigs.append(f"VIX {vix:.1f} < {VIX_CALM:.0f} → 🟢 Calm")
    spy, rsp = d.get("SPY"), d.get("RSP")
    if spy is not None and rsp is not None:
        sign_diverge = (spy > 0 and rsp < 0) or (spy < 0 and rsp > 0)
        gap_diverge = abs(spy - rsp) > BREADTH_DELTA
        if sign_diverge or gap_diverge:
            trigs.append(
                f"Breadth divergence (SPY {spy:+.2f}% vs RSP {rsp:+.2f}%, Δ={abs(spy-rsp):.2f}%)"
            )
    uj = d.get("USDJPY")
    if uj is not None and abs(uj) >= USDJPY_TRIG:
        dir_ = "↑" if uj > 0 else "↓"
        trigs.append(f"USDJPY {dir_} {uj:+.2f}% (≥ {USDJPY_TRIG:.1f}%)")
    return trigs

def is_defensive(d: dict, trigs: List[str]) -> bool:
    vix = d.get("VIX")
    uvxy, svix = d.get("UVXY"), d.get("SVIX")
    spy, rsp = d.get("SPY"), d.get("RSP")
    uj = d.get("USDJPY")
    if vix is not None and vix > VIX_DEFENSIVE:
        return True
    if uvxy is not None and uvxy >= UVXY_TRIG:
        return True
    if svix is not None and svix <= SVIX_TRIG:
        return True
    if spy is not None and rsp is not None:
        diverge = ((spy > 0 and rsp < 0) or (spy < 0 and rsp > 0) or abs(spy - rsp) > BREADTH_DELTA)
        if diverge and (spy < 0 or rsp < 0):
            return True
    if uj is not None and abs(uj) >= USDJPY_TRIG and (spy is not None and spy < 0):
        return True
    return False

def hedge_suggestion(d: dict, trigs: List[str]) -> str:
    vix = d.get("VIX")
    uvxy, svix = d.get("UVXY"), d.get("SVIX")
    spy, rsp = d.get("SPY"), d.get("RSP")
    uj = d.get("USDJPY")
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

def _load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"mode": "normal", "last_alert": 0}

def _save_state(state: Dict[str, Any]) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state))
    except Exception:
        pass

def _compose_body(now, d: dict, trigs: List[str], suggestion: str) -> str:
    lines = []
    lines.append("**Volatility & Hedge Monitor**")
    lines.append(f"**Time:** {now.strftime('%Y-%m-%d %H:%M %Z')}")
    if trigs:
        for t in trigs:
            lines.append(f"• **Trigger:** {t}")
    else:
        lines.append("• **Trigger:** (forced test alert)")
    lines.append("\n**Snapshot**")
    lines.append(f"- UVXY: {fmt_num(d.get('UVXY'))}%")
    lines.append(f"- SVIX: {fmt_num(d.get('SVIX'))}%")
    lines.append(f"- VIX:  {fmt_num(d.get('VIX'))}")
    lines.append(f"- USDJPY %: {fmt_num(d.get('USDJPY'))}")
    if d.get('SPY') is not None and d.get('RSP') is not None:
        lines.append(f"- Breadth proxy (SPY vs RSP): {fmt_num(d.get('SPY'))}% vs {fmt_num(d.get('RSP'))}%")
    lines.append(f"\n**Action:** {suggestion}")
    return "\n".join(lines)

def main():
    now = now_pt()
    if RESPECT_WINDOWS and not FORCE_ALERT:
        if not (in_us_window(now) or in_apac_window(now)):
            print("Outside monitoring windows — skipping.")
            return

    d = fetch_snapshot()
    trigs = detect_triggers(d)

    state = _load_state()
    was_mode = state.get("mode", "normal")
    now_def = is_defensive(d, trigs)
    now_ts = int(time.time())

    should_send_enter = False
    should_send_exit = False

    if now_def and was_mode != "defensive":
        should_send_enter = True
    elif now_def and was_mode == "defensive":
        if (now_ts - int(state.get("last_alert", 0))) >= ALERT_COOLDOWN_SEC:
            should_send_enter = True
    elif (not now_def) and was_mode == "defensive":
        should_send_exit = True

    if not (should_send_enter or should_send_exit or FORCE_ALERT or trigs):
        state["mode"] = "defensive" if now_def else "normal"
        _save_state(state)
        print("No triggers and no mode change.")
        return

    suggestion = hedge_suggestion(d, trigs)
    body = _compose_body(now, d, trigs, suggestion)

    try:
        if should_send_enter:
            subject = "[VEGA] Defensive Mode ENTER — Volatility Monitor"
            broadcast(subject, body)
            state["last_alert"] = now_ts
        elif should_send_exit:
            subject = "[VEGA] Defensive Mode EXIT — Volatility Monitor"
            broadcast(subject, body)
            state["last_alert"] = now_ts
        elif FORCE_ALERT or trigs:
            subject = "Vega Alert: Volatility/Hedge Monitor"
            broadcast(subject, body)
            state["last_alert"] = now_ts
    except Exception as e:
        print(f"[broadcast failed: {e}]")
        print(body)

    state["mode"] = "defensive" if now_def else "normal"
    _save_state(state)

    gid = os.getenv("GIST_ID")
    gtok = os.getenv("GIST_TOKEN")
    if gid and gtok:
        one_line = (
            f"{now.isoformat()} | "
            f"{'ENTER' if should_send_enter else ('EXIT' if should_send_exit else ('FORCED' if FORCE_ALERT else ('; '.join(trigs) if trigs else 'NO-TRIG')))} | "
            f"UVXY {fmt_num(d.get('UVXY'))}% | SVIX {fmt_num(d.get('SVIX'))}% | "
            f"VIX {fmt_num(d.get('VIX'))} | USDJPY {fmt_num(d.get('USDJPY'))}% | "
            f"SPY {fmt_num(d.get('SPY'))}% vs RSP {fmt_num(d.get('RSP'))}%"
        )
        try:
            append_gist(gid, gtok, one_line)
        except Exception:
            pass

if __name__ == "__main__":
    main()

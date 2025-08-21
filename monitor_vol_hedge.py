"""
Vega Cockpit — Volatility & Hedge Monitor (rewritten with state & cooldown)

Triggers (ANY):
  1) UVXY up ≥ +5% intraday vs prior close
  2) SVIX down ≤ −3% intraday vs prior close
  3) VIX > 20 (flip 🔴 Defensive) or VIX < 15 (flip 🟢 Calm)
  4) Breadth divergence (SPY vs RSP proxy): index up while breadth down, or vice versa
  5) USDJPY intraday move ≥ 1.0% (abs)

New:
  - ENTER/EXIT Defensive Mode with cooldown
  - State persisted to disk (Actions cache via WATCH_STATE_DIR)

Env knobs:
  WATCH_STATE_DIR       default ".vega_state"
  ALERT_COOLDOWN_MIN    default "15"  (minutes)
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
# Tunables (easy to tweak)
# =========================
UVXY_TRIG = 5.0       # %  (>=)
SVIX_TRIG = -3.0      # %  (<=)
VIX_DEFENSIVE = 20.0  # level
VIX_CALM = 15.0       # level
USDJPY_TRIG = 1.0     # % (absolute)
BREADTH_DELTA = 0.50  # % absolute difference between SPY% and RSP% that flags divergence

# Windows: script *runs* anytime but only *acts* inside these (self-limited)
RESPECT_WINDOWS = True

# Force a one-off alert even if no triggers (for testing)
FORCE_ALERT = os.getenv("FORCE_ALERT") == "1"

# State & cooldown
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
    """Fetch all numbers we need. Keep network calls minimal."""
    return {
        # Indices / breadth proxy
        "SPY": pct("SPY"),
        "RSP": pct("RSP"),

        # Volatility sleeve
        "UVXY": pct("UVXY"),
        "SVIX": pct("SVIX"),
        "VIX":  last_price("^VIX"),

        # FX — USDJPY (Yahoo: JPY=X; pct change)
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

    # Breadth divergence via SPY vs RSP proxy
    spy, rsp = d.get("SPY"), d.get("RSP")
    if spy is not None and rsp is not None:
        sign_diverge = (spy > 0 and rsp < 0) or (spy < 0 and rsp > 0)
        gap_diverge = abs(spy - rsp) > BREADTH_DELTA
        if sign_diverge or gap_diverge:
            trigs.append(
                f"Breadth divergence (SPY {spy:+.2f}% vs RSP {rsp:+.2f}%, Δ={abs(spy-rsp):.2f}%)"
            )

    # USDJPY absolute move
    uj = d.get("USDJPY")
    if uj is not None and abs(uj) >= USDJPY_TRIG:
        dir_ = "↑" if uj > 0 else "↓"
        trigs.append(f"USDJPY {dir_} {uj:+.2f}% (≥ {USDJPY_TRIG:.1f}%)")

    return trigs


def is_defensive(d: dict, trigs: List[str]) -> bool:
    """
    Define when to flip to Defensive Mode.
    Priority: VIX > threshold OR strong vol stress OR breadth diverging in a down tape.
    """
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
    # Big JPY shock can be a heads-up but not necessarily full defensive
    if uj is not None and abs(uj) >= USDJPY_TRIG and (spy is not None and spy < 0):
        return True
    return False


def hedge_suggestion(d: dict, trigs: List[str]) -> str:
    """Compact one-liner based on most severe condition."""
    vix = d.get("VIX")
    uvxy, svix = d.get("UVXY"), d.get("SVIX")
    spy, rsp = d.get("SPY"), d.get("RSP")
    uj = d.get("USDJPY")

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

    # Respect market windows to avoid noisy hours (still allow FORCE_ALERT)
    if RESPECT_WINDOWS and not FORCE_ALERT:
        if not (in_us_window(now) or in_apac_window(now)):
            print("Outside monitoring windows — skipping.")
            return

    d = fetch_snapshot()
    trigs = detect_triggers(d)

    # If no triggers and not forcing, we may still want to EXIT if we were defensive and now normalized.
    state = _load_state()
    was_mode = state.get("mode", "normal")
    now_def = is_defensive(d, trigs)

    # Decide whether to alert (ENTER/EXIT) with cooldown
    now_ts = int(time.time())
    should_send_enter = False
    should_send_exit = False

    if now_def and was_mode != "defensive":
        # New ENTER
        should_send_enter = True
    elif now_def and was_mode == "defensive":
        # Still defensive; only ENTER again if cooldown passed (status heartbeat)
        if (now_ts - int(state.get("last_alert", 0))) >= ALERT_COOLDOWN_SEC:
            should_send_enter = True
    elif (not now_def) and was_mode == "defensive":
        # EXIT
        should_send_exit = True
    else:
        # normal -> normal; do nothing unless FORCE_ALERT or explicit triggers exist
        pass

    # If nothing to send and not forced, quit early (but still update state)
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
            # Non-mode-changing informational alert (on manual test or mild triggers)
            subject = "Vega Alert: Volatility/Hedge Monitor"
            broadcast(subject, body)
            state["last_alert"] = now_ts
    except Exception as e:
        # Always print to logs so GH Actions shows content even if email/webhook fails
        print(f"[broadcast failed: {e}]")
        print(body)

    # Update and persist mode
    state["mode"] = "defensive" if now_def else "normal"
    _save_state(state)

    # Append a compact history line to gist (optional)
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

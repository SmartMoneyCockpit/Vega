import os, hashlib, time
from alerts.alert_state import get_state, fire, rearm
from utils.data import get_price, get_breakout_close, get_vix, news_since
from utils.mail import send_email
from utils.rules import load_rules, check_rearm_condition
from utils.store import log_fired   # logs fired alerts for digest

# Config from environment
ON_TRUE_ONLY = os.getenv("ALERTS_EMAIL_MODE", "on_true_only") == "on_true_only"
SUPPRESS_NOCHANGE = os.getenv("ALERTS_SUPPRESS_NOCHANGE", "true") == "true"
RATE_LIMIT = int(os.getenv("ALERTS_RATE_LIMIT_SECONDS", "60"))

# In-memory cache for rate limiting
LAST_SEND_AT = {}

def state_hash(val: str) -> str:
    """Make a short hash to track alert state changes."""
    return hashlib.sha256(val.encode()).hexdigest()[:8]

def allowed(rule_id: str) -> bool:
    """Rate limit duplicate sends within RATE_LIMIT seconds."""
    now = time.time()
    t = LAST_SEND_AT.get(rule_id, 0)
    if now - t >= RATE_LIMIT:
        LAST_SEND_AT[rule_id] = now
        return True
    return False

def maybe_send(rule_id, subject, body, s_hash):
    """Send an alert once, log it, and update state."""
    st = get_state(rule_id)
    if st.armed and st.last_state_hash != s_hash and allowed(rule_id):
        send_email(subject, body)
        log_fired(rule_id, f"{subject} — {body[:120]}")  # save for digest
        fire(rule_id, s_hash)

def run_once():
    """Check all rules once and fire alerts if needed."""
    for r in load_rules():
        st = get_state(r["id"])

        # ---- Price Cross
        if r["type"] == "price_cross":
            px = get_price(r["ticker"])
            cond = (px >= r["level"]) if r["direction"] == "above" else (px <= r["level"])
            s_hash = state_hash(f'{r["id"]}:{int(cond)}:{round(px,2)}')
            if cond and st.armed:
                maybe_send(r["id"], f'{r["ticker"]} trigger: {r["level"]}',
                           f'{r["ticker"]} crossed {r["level"]} (last={px:.2f}).', s_hash)

        # ---- Breakout Close
        elif r["type"] == "breakout_close":
            ok = get_breakout_close(
                r["ticker"],
                r["period"],
                confirm_breadth=r.get("confirm", {}).get("breadth", False)
            )
            s_hash = state_hash(f'{r["id"]}:{int(ok)}')
            if ok and st.armed:
                maybe_send(r["id"], f'{r["ticker"]} breakout {r["period"]}d',
                           'Breakout confirmed on close.', s_hash)

        # ---- Regime Flip
        elif r["type"] == "regime":
            vix = get_vix()
            cond = vix >= r["level"] if r["direction"] == "above" else vix <= r["level"]
            s_hash = state_hash(f'{r["id"]}:{int(cond)}:{round(vix,2)}')
            if cond and st.armed:
                maybe_send(r["id"],
                           f'Regime flip: {r["metric"]} {r["direction"]} {r["level"]}',
                           f'VIX={vix:.2f}', s_hash)

        # ---- News Keyword
        elif r["type"] == "news_keyword":
            items = news_since(lookback="1h",
                               tickers=r["tickers"],
                               keywords=r["keywords"])
            for it in items:
                s_hash = state_hash(f'{r["id"]}:{it["id"]}')
                if st.armed:
                    maybe_send(r["id"], f'News: {it["ticker"]}', it["title"], s_hash)

        # ---- Rearm if condition met
        if check_rearm_condition(r):
            rearm(r["id"])

if __name__ == "__main__":
    run_once()

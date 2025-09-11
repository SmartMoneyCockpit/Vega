import os, hashlib
from alerts.alert_state import get_state, fire, rearm
from utils.data import get_price, get_breakout_close, get_vix, news_since
from utils.mail import send_email
from utils.rules import load_rules, check_rearm_condition

ON_TRUE_ONLY = os.getenv("ALERTS_EMAIL_MODE","on_true_only")=="on_true_only"
SUPPRESS_NOCHANGE = os.getenv("ALERTS_SUPPRESS_NOCHANGE","true")=="true"

def state_hash(val: str) -> str:
    return hashlib.sha256(val.encode()).hexdigest()[:8]

def maybe_send(rule_id, subject, body, s_hash):
    st = get_state(rule_id)
    if st.armed and st.last_state_hash != s_hash:
        send_email(subject, body)     # one-shot
        fire(rule_id, s_hash)

def run_once():
    for r in load_rules():
        st = get_state(r["id"])
        # ---- evaluate condition_true + compute s_hash
        if r["type"]=="price_cross":
            px = get_price(r["ticker"])
            cond = (px >= r["level"]) if r["direction"]=="above" else (px <= r["level"])
            s_hash = state_hash(f'{r["id"]}:{int(cond)}:{round(px,2)}')
            if cond and st.armed:
                maybe_send(r["id"], f'{r["ticker"]} trigger: {r["level"]}', f'{r["ticker"]} crossed {r["level"]}.', s_hash)
        elif r["type"]=="breakout_close":
            ok = get_breakout_close(r["ticker"], r["period"], confirm_breadth=r.get("confirm",{}).get("breadth",False))
            s_hash = state_hash(f'{r["id"]}:{int(ok)}')
            if ok and st.armed:
                maybe_send(r["id"], f'{r["ticker"]} breakout {r["period"]}d', 'Breakout confirmed on close.', s_hash)
        elif r["type"]=="regime":
            vix = get_vix()
            cond = vix >= r["level"] if r["direction"]=="above" else vix <= r["level"]
            s_hash = state_hash(f'{r["id"]}:{int(cond)}:{round(vix,2)}')
            if cond and st.armed:
                maybe_send(r["id"], f'Regime flip: {r["metric"]} {r["direction"]} {r["level"]}', f'VIX={vix:.2f}', s_hash)
        elif r["type"]=="news_keyword":
            items = news_since(lookback="1h", tickers=r["tickers"], keywords=r["keywords"])
            for it in items:
                s_hash = state_hash(f'{r["id"]}:{it["id"]}')
                if st.armed:
                    maybe_send(r["id"], f'News: {it["ticker"]}', it["title"], s_hash)

        # ---- re-arm logic
        if check_rearm_condition(r):
            rearm(r["id"])

if __name__ == "__main__":
    run_once()

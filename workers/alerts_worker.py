import os, sys, argparse, logging, datetime as dt, yaml
from pathlib import Path
import pandas as pd

from email_client import EmailClient
from workers.providers.polygon_client import Polygon
from workers.scan_rules import ema, atr, rs_against, rr_ok, build_df

LOG = logging.getLogger("alerts-worker")
REQ = ["SENDGRID_API_KEY","ALERTS_TO","ALERTS_FROM"]

def need(keys):
    miss = [k for k in keys if not os.getenv(k)]
    if miss: raise RuntimeError(f"Missing required env: {miss}")

def load_cfg():
    p = Path("config/watchlists/us.yaml")
    if not p.exists(): raise RuntimeError("Missing config/watchlists/us.yaml")
    return yaml.safe_load(p.read_text())

def pull_df(poly, ticker, days=60):
    bars = poly.aggregates_day(ticker, limit=days)
    return build_df(bars)

def check_earnings_ok(ticker, earnings_hint=None):
    """
    Return True if next earnings >= 30d away or unknown (we fail safe if unknown).
    You can tighten later by sourcing your cockpit calendar instead.
    """
    next_ok = True
    try:
        ej = earnings_hint or {}
        # placeholder: if ej has 'days_to_earnings', enforce:
        dte = ej.get("days_to_earnings")
        if dte is not None:
            next_ok = (dte >= 30)
    except Exception:
        pass
    return next_ok

def scan_us(poly, cfg):
    tickers = cfg["universe"]
    rules   = cfg["rules"]

    # prefetch SPY for RS
    spy_df = pull_df(poly, "SPY")
    out = []

    for t in tickers:
        try:
            df = pull_df(poly, t)
            if df.empty or len(df) < 30: 
                LOG.info("Skip %s: not enough data", t); continue

            # liquidity / price floors
            px = float(df["close"].iloc[-1])
            if px < rules["min_price"]: 
                continue

            avgv = poly.avg_volume_30d(t)
            if avgv < rules["min_avg_volume"]: 
                continue

            # indicators
            df["ema21"] = ema(df["close"], rules["ema_period"])
            df["atr14"] = atr(df, rules["atr_period"])
            in_momo = px > float(df["ema21"].iloc[-1])

            rs = rs_against(df, spy_df, rules["rs_lookback_days"])
            rs_ok = (rs > 1.0)

            # simple stop/target using ATR and recent swing (here: 1x ATR stop, 3.5x target from entry)
            entry = px
            stop  = entry - float(df["atr14"].iloc[-1]) * 1.0
            target = entry + float(df["atr14"].iloc[-1]) * 3.5

            rr_ok_flag = rr_ok(entry, stop, target, rr_min=rules["rr_min"])
            earnings_ok = check_earnings_ok(t)

            if in_momo and rs_ok and rr_ok_flag and earnings_ok:
                out.append({
                    "ticker": t,
                    "price": round(px, 2),
                    "ema21": round(float(df["ema21"].iloc[-1]), 2),
                    "atr": round(float(df["atr14"].iloc[-1]), 2),
                    "rs20_vs_SPY": round(rs, 3),
                    "entry": round(entry, 2),
                    "stop": round(stop, 2),
                    "target": round(target, 2),
                    "rr": round((target-entry)/(entry-stop), 2)
                })
        except Exception as e:
            LOG.exception("Scan error %s", t)
            continue

    return out

def compose_email(picks):
    if not picks:
        return ("Vega Alerts: 0 setups", "No tradable setups (daily rules).")
    lines = []
    for p in picks:
        lines.append(
            f"{p['ticker']}: ${p['price']} | EMA21 {p['ema21']} | ATR {p['atr']} | "
            f"RS20 {p['rs20_vs_SPY']} | Entry {p['entry']} Stop {p['stop']} "
            f"Target {p['target']} (R/R {p['rr']})"
        )
    body = "Smart Money (Daily) — Green / Tradable Today\n\n" + "\n".join(lines)
    return (f"Vega Alerts: {len(picks)} setups", body)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log-level", default=os.getenv("LOG_LEVEL","INFO"))
    args = ap.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    try:
        need(REQ)
        cfg = load_cfg()
        client = EmailClient(os.environ["SENDGRID_API_KEY"], os.environ["ALERTS_FROM"], os.environ["ALERTS_TO"])
    except Exception:
        LOG.exception("Startup failed"); return 2

    if args.dry_run:
        try:
            client.send("Vega Alerts Worker: DRY-RUN OK", "Email pipe verified.")
            LOG.info("Dry run sent.")
            return 0
        except Exception:
            LOG.exception("Dry-run email failed")
            return 2

    poly_key = os.getenv("POLYGON_API_KEY")
    if not poly_key:
        LOG.error("POLYGON_API_KEY missing; cannot scan."); 
        client.send("Vega Alerts Worker: missing POLYGON_API_KEY", "Set the secret and re-run.")
        return 2

    poly = Polygon(poly_key)

    try:
        picks = scan_us(poly, cfg)
    except Exception:
        LOG.exception("Scan crashed")
        client.send("Vega Alerts Worker: scan crashed", "Check Actions logs.")
        return 1

    subj, body = compose_email(picks)
    try:
        client.send(subj, body)
        LOG.info("Email sent: %s", subj)
        return 0
    except Exception:
        LOG.exception("Failed to send email")
        return 1

if __name__ == "__main__":
    sys.exit(main())

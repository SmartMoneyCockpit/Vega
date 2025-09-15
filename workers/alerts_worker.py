import os, sys, argparse, logging, json
from pathlib import Path

import pandas as pd

from workers.email_client import EmailClient
from workers.providers.polygon_client import Polygon
from workers.providers.csv_sources import load_tradingview_universe, load_earnings_calendar
from workers.providers.yfinance_sector import SectorResolver
from workers.scan_rules import ema, atr, rs_against, rr_ok, build_df

LOG = logging.getLogger("alerts-worker")
REQ = ["SENDGRID_API_KEY","ALERTS_TO","ALERTS_FROM","POLYGON_API_KEY","TRADINGVIEW_CSV_URL","COCKPIT_EARNINGS_CSV_URL"]

def need(keys):
    miss = [k for k in keys if not os.getenv(k)]
    if miss: 
        raise RuntimeError(f"Missing required env: {miss}")

def sector_allowlist():
    raw = (os.getenv("SECTOR_ALLOWLIST") or "").strip()
    if not raw:
        return set()
    return {s.strip() for s in raw.split(",") if s.strip()}

def to_df(poly, ticker):
    bars = poly.aggregates_day(ticker, limit=60)
    return build_df(bars)

def earnings_ok(ticker, earn_map):
    dte = earn_map.get(ticker.upper())
    return (dte is None) or (dte >= 30)

def compose_json(picks):
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    outp = Path("artifacts/alerts.json")
    outp.write_text(json.dumps({"generated_by":"alerts-worker","picks":picks}, indent=2))
    return str(outp)

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
        client = EmailClient(
            os.environ["SENDGRID_API_KEY"], 
            os.environ["ALERTS_FROM"], 
            os.environ["ALERTS_TO"]
        )
    except Exception:
        LOG.exception("Startup failed")
        return 2

    if args.dry_run:
        try:
            client.send("Vega Alerts Worker: DRY-RUN OK", "Email pipe verified.")
            LOG.info("Dry run email sent.")
            return 0
        except Exception:
            LOG.exception("Dry-run email failed")
            return 2

    poly = Polygon(os.environ["POLYGON_API_KEY"])
    earn_map = load_earnings_calendar()
    allow = sector_allowlist()
    sectorer = SectorResolver()

    # 1) Pull universe from TradingView CSV
    tv_rows = load_tradingview_universe()

    # 2) Keep US-listed issues for Polygon (skip TSX etc.)
    def is_us(ex):
        return (ex or "").upper() in {"NYSE","NASDAQ","AMEX","NMS","NYS"} or not ex
    tickers = [ r["symbol"].upper() for r in tv_rows if is_us(r.get("exchange")) ]

    # 3) Scan
    spy_df = to_df(poly, "SPY")
    picks = []
    for t in tickers:
        try:
            df = to_df(poly, t)
            if df.empty or len(df) < 30:
                continue

            price = float(df["close"].iloc[-1])
            if price < 5:
                continue

            # Simple liquidity gate
            vols = df["vol"].tail(30)
            if vols.mean() < 500_000:
                continue

            df["ema21"] = ema(df["close"], 21)
            df["atr14"] = atr(df, 14)

            in_momo = price > float(df["ema21"].iloc[-1])
            rs = rs_against(df, spy_df, 20)
            rs_ok = rs > 1.0
            if not (in_momo and rs_ok):
                continue

            # Enforce earnings rule
            if not earnings_ok(t, earn_map):
                continue

            # Optional: sector allowlist
            if allow:
                s = sectorer.sector(t)
                if (s is None) or (s not in allow):
                    continue

            entry  = price
            stop   = entry - float(df["atr14"].iloc[-1]) * 1.0
            target = entry + float(df["atr14"].iloc[-1]) * 3.5

            if not rr_ok(entry, stop, target, rr_min=3.0):
                continue

            picks.append({
                "ticker": t,
                "price": round(price, 2),
                "ema21": round(float(df["ema21"].iloc[-1]), 2),
                "atr": round(float(df["atr14"].iloc[-1]), 2),
                "rs20_vs_SPY": round(rs, 3),
                "entry": round(entry, 2),
                "stop": round(stop, 2),
                "target": round(target, 2),
                "rr": round((target-entry)/(entry-stop), 2)
            })
        except Exception:
            LOG.exception("Scan error for %s", t)
            continue

    # 4) Persist JSON for cockpit
    json_path = compose_json(picks)

    # 5) Email (only if there are picks)
    if picks:
        lines = [
            f"{p['ticker']}: ${p['price']} | EMA21 {p['ema21']} | ATR {p['atr']} | "
            f"RS20 {p['rs20_vs_SPY']} | Entry {p['entry']} Stop {p['stop']} Target {p['target']} (R/R {p['rr']})"
            for p in picks
        ]
        body = "Smart Money (Daily) — Green / Tradable Today\n\n" + "\n".join(lines) + f"\n\nJSON: {json_path}"
        client.send(f"Vega Alerts: {len(picks)} setups", body)
        LOG.info("Email sent with %d picks; JSON at %s", len(picks), json_path)
        return 0
    else:
        LOG.info("No green setups today; JSON at %s", json_path)
        # Optional: quiet day → no email
        return 0

if __name__ == "__main__":
    sys.exit(main())

# workers/alerts_worker.py
"""
Vega Alerts Worker (single-file, self-contained)
- Email sending is optional (uses SENDGRID_API_KEY if present)
- Includes fallbacks for scan_rules (ema, atr, rs_against, rr_ok, build_df)
- Emits artifacts/alerts.json with {"email": "...", "picks": [...]}
Run via:
  python -m workers.alerts_worker
or:
  python workers/alerts_worker.py
"""

import os, sys, argparse, logging, json
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterable

# --- import shim so running as a script still finds 'workers' package ---
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
# --- end shim ---

import pandas as pd
import numpy as np
import requests

# Providers you already have in your repo:
from workers.providers.polygon_client import Polygon
from workers.providers.csv_sources import load_tradingview_universe, load_earnings_calendar
from workers.providers.yfinance_sector import SectorResolver

LOG = logging.getLogger("alerts-worker")

# Only hard requirements (email is optional)
REQ = ["POLYGON_API_KEY", "TRADINGVIEW_CSV_URL", "COCKPIT_EARNINGS_CSV_URL"]

# -----------------------------
# Try to import scan_rules; if missing, provide fallbacks
# -----------------------------
try:
    from workers.scan_rules import ema, atr, rs_against, rr_ok, build_df  # type: ignore
except Exception:
    LOG.warning("workers.scan_rules not found. Using built-in fallback implementations.")

    def ema(series: pd.Series, n: int) -> pd.Series:
        """Exponential moving average."""
        return series.ewm(span=n, adjust=False, min_periods=n).mean()

    def atr(df: pd.DataFrame, n: int) -> pd.Series:
        """
        Average True Range. If high/low not present, approximate with
        rolling std of close * sqrt(1) as a conservative proxy.
        """
        if all(col in df.columns for col in ("high", "low", "close")):
            prev_close = df["close"].shift(1)
            tr = pd.concat(
                [
                    (df["high"] - df["low"]).abs(),
                    (df["high"] - prev_close).abs(),
                    (df["low"] - prev_close).abs(),
                ],
                axis=1,
            ).max(axis=1)
            return tr.rolling(n, min_periods=n).mean()
        # Fallback: proxy ATR from close volatility
        return df["close"].pct_change().abs().rolling(n, min_periods=n).mean() * df["close"]

    def rs_against(df: pd.DataFrame, bench: pd.DataFrame, lookback: int) -> float:
        """
        Simple relative strength vs SPY over lookback:
        (price / price[-lookback]) / (bench / bench[-lookback])
        """
        if len(df) < lookback + 1 or len(bench) < lookback + 1:
            return 1.0
        p0, p1 = float(df["close"].iloc[-lookback - 1]), float(df["close"].iloc[-1])
        b0, b1 = float(bench["close"].iloc[-lookback - 1]), float(bench["close"].iloc[-1])
        if p0 == 0 or b0 == 0:
            return 1.0
        return (p1 / p0) / (b1 / b0)

    def rr_ok(entry: float, stop: float, target: float, rr_min: float = 3.0) -> bool:
        """Risk/Reward sanity."""
        if not (stop < entry < target):
            return False
        rr = (target - entry) / (entry - stop) if (entry - stop) != 0 else 0.0
        return rr >= rr_min

    def _poly_agg_to_df(bars: Iterable[Dict[str, Any] | Any]) -> pd.DataFrame:
        """
        Convert Polygon aggregates list to a standard DataFrame.
        Tries keys: c/o/h/l/v (Polygon) or close/open/high/low/volume.
        """
        if isinstance(bars, pd.DataFrame):
            df = bars.copy()
        else:
            rows = []
            for b in bars or []:
                # allow object with attributes or dict
                get = (lambda k: getattr(b, k, None)) if not isinstance(b, dict) else (lambda k: b.get(k))
                rows.append(
                    {
                        "ts": get("t") or get("timestamp") or get("time"),
                        "open": get("o") or get("open"),
                        "high": get("h") or get("high"),
                        "low": get("l") or get("low"),
                        "close": get("c") or get("close"),
                        "vol": get("v") or get("volume"),
                    }
                )
            df = pd.DataFrame(rows)

        # standardize and clean
        rename_map = {"volume": "vol"}
        df = df.rename(columns=rename_map)
        for col in ["open", "high", "low", "close", "vol"]:
            if col not in df.columns:
                df[col] = np.nan
        df = df.dropna(subset=["close"]).reset_index(drop=True)
        return df

    def build_df(bars: Iterable[Dict[str, Any] | Any]) -> pd.DataFrame:
        """Public wrapper used by worker."""
        return _poly_agg_to_df(bars)

# -----------------------------
# Built-in lightweight EmailClient
# -----------------------------
class EmailClient:
    """
    Minimal SendGrid client.
    - If 'to' not provided on send(), falls back to ALERTS_TO env.
    - Uses ALERTS_FROM for sender (default 'noreply@vega.local').
    """
    def __init__(self, api_key: Optional[str] = None,
                 sender: Optional[str] = None,
                 default_to: Optional[str] = None):
        self.api_key = api_key or os.environ["SENDGRID_API_KEY"]
        self.sender = sender or os.environ.get("ALERTS_FROM", "noreply@vega.local")
        self.default_to = default_to or os.environ.get("ALERTS_TO")

    def send(self, subject: str, body: str, to: Optional[str] = None) -> None:
        dest = to or self.default_to
        if not dest:
            raise ValueError("Destination email missing (set ALERTS_TO or pass 'to=').")

        payload = {
            "personalizations": [{"to": [{"email": dest}]}],
            "from": {"email": self.sender},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }
        r = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=20,
        )
        r.raise_for_status()

# -----------------------------
# Helpers
# -----------------------------
def need(keys: List[str]) -> None:
    miss = [k for k in keys if not os.getenv(k)]
    if miss:
        raise RuntimeError(f"Missing required env: {miss}")

def sector_allowlist() -> set:
    raw = (os.getenv("SECTOR_ALLOWLIST") or "").strip()
    if not raw:
        return set()
    return {s.strip() for s in raw.split(",") if s.strip()}

def to_df(poly: Polygon, ticker: str) -> pd.DataFrame:
    bars = poly.aggregates_day(ticker, limit=60)
    return build_df(bars)

def earnings_ok(ticker: str, earn_map: Dict[str, Optional[int]]) -> bool:
    dte = earn_map.get(ticker.upper())
    return (dte is None) or (dte >= 30)

def compose_json(picks: List[Dict[str, Any]], email_status: str) -> str:
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    outp = Path("artifacts/alerts.json")
    outp.write_text(json.dumps(
        {"generated_by": "alerts-worker", "email": email_status, "picks": picks},
        indent=2
    ))
    return str(outp)

# -----------------------------
# Main
# -----------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Send a test email if enabled, skip scanning.")
    ap.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    args = ap.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    try:
        need(REQ)
    except Exception:
        LOG.exception("Startup failed")
        return 2

    # Email is optional
    email_enabled = bool(os.getenv("SENDGRID_API_KEY"))
    alerts_to = os.getenv("ALERTS_TO")
    alerts_from = os.getenv("ALERTS_FROM")

    client: Optional[EmailClient] = None
    if email_enabled:
        try:
            client = EmailClient(os.environ["SENDGRID_API_KEY"], alerts_from, alerts_to)
        except Exception:
            email_enabled = False
            LOG.exception("Email client init failed; continuing without email")

    if args.dry_run:
        status = "disabled"
        if email_enabled and client:
            try:
                client.send("Vega Alerts Worker: DRY-RUN OK", "Email pipe verified.")
                LOG.info("Dry run email sent.")
                status = "sent"
            except Exception:
                status = "failed"
                LOG.exception("Dry-run email failed; continuing")
        else:
            LOG.info("Dry run OK (email disabled)")
        compose_json([], status)
        return 0

    poly = Polygon(os.environ["POLYGON_API_KEY"])
    earn_map = load_earnings_calendar()
    allow = sector_allowlist()
    sectorer = SectorResolver()

    # 1) Universe from TradingView CSV
    tv_rows = load_tradingview_universe()

    # 2) Keep US-listed issues for Polygon (skip TSX etc.)
    def is_us(ex: Optional[str]) -> bool:
        return (ex or "").upper() in {"NYSE", "NASDAQ", "AMEX", "NMS", "NYS"} or not ex

    tickers = [r["symbol"].upper() for r in tv_rows if is_us(r.get("exchange"))]

    # 3) Scan
    spy_df = to_df(poly, "SPY")
    picks: List[Dict[str, Any]] = []
    for t in tickers:
        try:
            df = to_df(poly, t)
            if df.empty or len(df) < 30:
                continue

            price = float(df["close"].iloc[-1])
            if price < 5:
                continue

            # Simple liquidity gate
            vols = df["vol"].tail(30) if "vol" in df.columns else pd.Series(dtype=float)
            if len(vols) >= 10 and float(vols.mean()) < 500_000:
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

            entry = price
            stop = entry - float(df["atr14"].iloc[-1]) * 1.0
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
                "rr": round((target - entry) / (entry - stop), 2),
            })
        except Exception:
            LOG.exception("Scan error for %s", t)
            continue

    # 4) Persist JSON for cockpit
    email_status = "disabled"
    json_path = compose_json(picks, email_status)

    # 5) Email (only if enabled and there are picks)
    if picks and email_enabled and client:
        try:
            lines = [
                f"{p['ticker']}: ${p['price']} | EMA21 {p['ema21']} | ATR {p['atr']} | "
                f"RS20 {p['rs20_vs_SPY']} | Entry {p['entry']} Stop {p['stop']} Target {p['target']} (R/R {p['rr']})"
                for p in picks
            ]
            body = "Smart Money (Daily) — Green / Tradable Today\n\n" + "\n".join(lines) + f"\n\nJSON: {json_path}"
            client.send(f"Vega Alerts: {len(picks)} setups", body)
            email_status = "sent"
            LOG.info("Email sent with %d picks; JSON at %s", len(picks), json_path)
        except Exception:
            email_status = "failed"
            LOG.exception("Email send failed; continuing without email")
        compose_json(picks, email_status)
    else:
        why = "no picks" if not picks else "email disabled"
        LOG.info("No email sent (%s); JSON at %s", why, json_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())

import os, io, csv, requests
from datetime import datetime, timezone
from dateutil import parser

def fetch_csv(url: str) -> list[dict]:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    text = r.text
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(text.splitlines()[0] + "\n")
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    return [ {k.strip(): (v.strip() if isinstance(v, str) else v) for k,v in row.items()} for row in reader ]

def load_tradingview_universe() -> list[dict]:
    url = os.environ["TRADINGVIEW_CSV_URL"]
    rows = fetch_csv(url)
    out = []
    for r in rows:
        sym = (r.get("Symbol") or r.get("Ticker") or "").strip()
        exch = (r.get("Exchange") or "").strip()
        if not sym:
            continue
        out.append({"symbol": sym, "exchange": exch})
    return out

def parse_days_to_earnings(earn_on: str) -> int | None:
    try:
        dt_earn = parser.parse(earn_on)
        now = datetime.now(timezone.utc)
        return max(0, int((dt_earn - now).days))
    except Exception:
        return None

def load_earnings_calendar() -> dict[str, int]:
    """
    Returns: { 'TICKER': days_to_earnings, ... }
    Accepts either DaysToEarnings column, or EarningsDate parsable string.
    """
    url = os.environ["COCKPIT_EARNINGS_CSV_URL"]
    rows = fetch_csv(url)
    out = {}
    for r in rows:
        t = (r.get("Ticker") or r.get("Stock Ticker") or r.get("Symbol") or "").strip().upper()
        if not t:
            continue
        dte = r.get("DaysToEarnings")
        if dte is not None and str(dte).strip() != "":
            try:
                out[t] = int(float(dte))
                continue
            except Exception:
                pass
        edate = r.get("EarningsDate") or r.get("Next Earnings") or r.get("Earnings")
        if edate:
            dcalc = parse_days_to_earnings(edate)
            if dcalc is not None:
                out[t] = dcalc
    return out

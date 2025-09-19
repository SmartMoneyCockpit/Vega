from pathlib import Path
from urllib.parse import urlencode
from typing import Iterable, Dict, Optional

TV_BASE = "https://www.tradingview.com/chart/"

# Common exchange codes for TradingView (normalization)
EXCHANGE_ALIASES = {
    # US
    "NYSE": "NYSE", "NASD": "NASDAQ", "NASDAQ": "NASDAQ",
    # Canada
    "TSX": "TSX", "TSE": "TSX", "TSXV": "TSXV", "VENTURE": "TSXV",
    # Mexico
    "BMV": "BMV",
    # Japan
    "TSE": "TSE", "TOKYO": "TSE",
    # Germany
    "XETR": "XETR", "FWB": "XETR",
    # UK
    "LSE": "LSE",
}

def normalize_exchange(exchange: Optional[str]) -> Optional[str]:
    if not exchange:
        return None
    return EXCHANGE_ALIASES.get(exchange.strip().upper(), exchange.strip().upper())

def tv_symbol(symbol: str, exchange: Optional[str] = None) -> str:
    """Return TradingView symbol format EXCHANGE:SYMBOL when exchange is provided (normalized)."""
    symbol = symbol.strip().upper()
    nex = normalize_exchange(exchange)
    if nex:
        return f"{nex}:{symbol}"
    return symbol

def tv_deeplink(symbol: str, exchange: Optional[str] = None, interval: str = "D") -> str:
    q = {"symbol": tv_symbol(symbol, exchange), "interval": interval}
    return f"{TV_BASE}?{urlencode(q)}"

def export_watchlist(symbols: Iterable[str], export_path: str) -> str:
    p = Path(export_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join([s.strip().upper() for s in symbols if s]) + "\n", encoding="utf-8")
    return str(p)

def export_trades(rows: Iterable[Dict], export_path: str) -> str:
    """Write trades CSV with a tv_url column automatically added."""
    import csv
    p = Path(export_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "symbol","exchange","side","entry","stop","target1","target2",
        "rr","reason_tags","notes","interval","tv_url"
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            link = tv_deeplink(r.get("symbol",""), r.get("exchange"), r.get("interval","D"))
            row = {k: r.get(k, "") for k in fieldnames}
            row["tv_url"] = link
            w.writerow(row)
    return str(p)

def export_links(symbols: Iterable[str], export_path: str, exchange: Optional[str] = None, interval: str = "D") -> str:
    import csv
    p = Path(export_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol","interval","tv_url"])
        w.writeheader()
        for s in symbols:
            w.writerow({
                "symbol": s,
                "interval": interval,
                "tv_url": tv_deeplink(s, exchange, interval)
            })
    return str(p)

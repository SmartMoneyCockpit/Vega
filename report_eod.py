"""
Vega Cockpit — North America End-of-Day Wrap
Outputs:
  - Index performance (USA, Canada, Mexico, LatAm proxy)
  - FX & Commodities quick wrap
  - Leaders/Laggards snapshot from sample lists
"""

from __future__ import annotations
from typing import Dict, Any, List
import os

from utils import now_pt, pct_from_prev_close, last_price, fmt_num
from email_webhook import broadcast

def pct(tk: str) -> float | None:
    try:
        return pct_from_prev_close(tk)
    except Exception:
        return None

def val(tk: str) -> float | None:
    try:
        return last_price(tk)
    except Exception:
        return None

def main():
    now = now_pt()

    data = {
        "SPY%": pct("SPY"),
        "DIA%": pct("DIA"),
        "QQQ%": pct("QQQ"),
        "^GSPTSE%": pct("^GSPTSE"),   # Canada TSX
        "^MXX%": pct("^MXX"),         # Mexico IPC
        "^SPLAC%": pct("^SPLAC"),     # S&P Latin America 40 (proxy; may be delayed)
        "USDMXN": val("MXN=X"),
        "USDCAD": val("CAD=X"),
        "GOLD": val("GC=F"),
        "SILVER": val("SI=F"),
        "COPPER": val("HG=F"),
        "WTI": val("CL=F"),
        "VIX": val("^VIX"),
    }

    leaders_watch: List[str] = ["AAPL","MSFT","NVDA","AMZN","META","PEP","WMT","GOOGL"]
    laggards_watch: List[str] = ["TSLA","AMD","NFLX","COST","ORCL","AVGO","JPM","UNH"]

    def rows(names: List[str]) -> List[str]:
        out = []
        for n in names:
            p = pct(n)
            out.append(f"- {n}: {fmt_num(p)}%")
        return out

    lines: List[str] = []
    lines.append("**North America — End of Day Wrap**")
    lines.append(f"**Time:** {now.strftime('%Y-%m-%d %H:%M %Z')}\n")

    lines.append("**Index Performance**")
    lines.append(f"- USA: SPY {fmt_num(data['SPY%'])}% | QQQ {fmt_num(data['QQQ%'])}% | DIA {fmt_num(data['DIA%'])}%")
    lines.append(f"- Canada (TSX): {fmt_num(data['^GSPTSE%'])}%   | Mexico (IPC): {fmt_num(data['^MXX%'])}%")
    lines.append(f"- LatAm (S&P LA40 proxy): {fmt_num(data['^SPLAC%'])}%\n")

    lines.append("**FX & Commodities**")
    lines.append(f"- USDMXN: {fmt_num(data['USDMXN'])} | USDCAD: {fmt_num(data['USDCAD'])}")
    lines.append(f"- Gold: {fmt_num(data['GOLD'])} | Silver: {fmt_num(data['SILVER'])} | Copper: {fmt_num(data['COPPER'])} | WTI: {fmt_num(data['WTI'])}")
    lines.append(f"- VIX: {fmt_num(data['VIX'])}\n")

    lines.append("**Leaders (watchlist sample)**")
    lines += rows(leaders_watch)
    lines.append("\n**Laggards (watchlist sample)**")
    lines += rows(laggards_watch)

    body = "\n".join(lines)
    subject = "Vega — End of Day Wrap (North America)"

    try:
        broadcast(subject, body)
    except Exception as e:
        print(f"[broadcast failed: {e}]")
        print(body)

if __name__ == "__main__":
    main()

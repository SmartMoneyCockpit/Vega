"""
Vega Cockpit — North America End-of-Day Wrap (watchlists-enabled)
- Index performance (USA, Canada, Mexico, LatAm proxy)
- FX & Commodities quick wrap
- Regional movers from watchlists.yml (Canada TSX, Mexico BMV/ADRs, LatAm)
"""

from __future__ import annotations
from typing import Dict, Any, List, Tuple
from pathlib import Path
import os
try:
    import yaml
except Exception:
    class _YamlShim:
        def safe_load(self, *a, **k):
            return {}
    yaml = _YamlShim()  # requires pyyaml
from utils import now_pt, pct_from_prev_close, last_price, fmt_num
from email_webhook import broadcast

# ---------- helpers ----------
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

def load_watchlists(path: str = "watchlists.yml") -> Dict[str, List[str]]:
    """Load YAML watchlists. Returns empty dict if missing/invalid."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = yaml.safe_load(p.read_text()) or {}
        # normalize to lists of strings
        out = {}
        for k, v in data.items():
            if isinstance(v, list):
                out[k] = [str(x).strip() for x in v if str(x).strip()]
        return out
    except Exception:
        return {}

def top_bottom(tickers: List[str], n: int = 5) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    """Return top and bottom n by % change; skips symbols that return None."""
    vals: List[Tuple[str, float]] = []
    for t in tickers:
        p = pct(t)
        if p is not None:
            vals.append((t, p))
    if not vals:
        return [], []
    vals.sort(key=lambda x: x[1], reverse=True)
    top = vals[:n]
    bot = vals[-n:] if len(vals) >= n else vals[-len(vals):]
    return top, bot

def section_movers(title: str, tickers: List[str], n: int = 5) -> List[str]:
    lines: List[str] = []
    if not tickers:
        return lines
    top, bot = top_bottom(tickers, n=n)
    if not top and not bot:
        return lines
    lines.append(f"**{title} — Movers**")
    if top:
        lines.append("Top:")
        for t, p in top:
            lines.append(f"- {t}: {fmt_num(p)}%")
    if bot:
        lines.append("Bottom:")
        for t, p in bot:
            lines.append(f"- {t}: {fmt_num(p)}%")
    lines.append("")  # spacer
    return lines

# ---------- main ----------
def main():
    now = now_pt()

    # Core indices & macros
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

    # Load regional watchlists
    wl = load_watchlists("watchlists.yml")
    canada = wl.get("canada_tsx", [])
    mexico_bmv = wl.get("mexico_bmv", [])
    mexico_adrs = wl.get("mexico_adrs", [])
    latam = wl.get("latam", [])

    # Build body
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

    # Regional movers from YAML
    if canada or mexico_bmv or mexico_adrs or latam:
        lines += section_movers("Canada (TSX)", canada, n=5)
        lines += section_movers("Mexico (BMV)", mexico_bmv, n=5)
        lines += section_movers("Mexico (ADRs/OTC)", mexico_adrs, n=5)
        lines += section_movers("LatAm (ADRs)", latam, n=5)
    else:
        # Fallback if YAML missing
        lines.append("_No watchlists.yml found — using default sample lists._\n")
        sample_can = ["ABX.TO","NTR.TO","RY.TO","TD.TO","SHOP.TO"]
        sample_mx  = ["WALMEX.MX","AMXL.MX","GMEXICOB.MX","CEMEXCPO.MX","FEMSAUBD.MX"]
        sample_la  = ["PBR","VALE","ITUB","MELI","CIB"]
        lines += section_movers("Canada (TSX)", sample_can, n=5)
        lines += section_movers("Mexico (BMV)", sample_mx, n=5)
        lines += section_movers("LatAm (ADRs)", sample_la, n=5)

    body = "\n".join(lines)
    subject = "Vega — End of Day Wrap (North America)"

    try:
        broadcast(subject, body)
    except Exception as e:
        print(f"[broadcast failed: {e}]")
        print(body)

if __name__ == "__main__":
    main()

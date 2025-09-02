# Vega • North American Midday Verdict
# -----------------------------------
# Copy this file to repo root as: report_midday.py
# The script:
#  - Pulls % change from previous close for SPY/QQQ/IWM/DIA/RSP/VIX
#  - Produces a short "midday verdict" with volatility + breadth notes
#  - Sends via email_webhook.broadcast() if available, otherwise prints

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

# -------- Time helper (works with either utils.now or utils.get_now) --------
try:
    from utils import now as _now  # preferred new name
except Exception:
    try:
        from utils import get_now as _now  # backward-compat
    except Exception:
        def _now(tz: str = "America/Phoenix"):
            return datetime.now(ZoneInfo(tz))
now = _now

# -------- Data/format helpers (use utils if present, else light fallbacks) ---
try:
    from utils import get_from_prev_close, last_price, fmt_pct  # type: ignore
except Exception:
    import yfinance as yf

    def last_price(ticker: str) -> float | None:
        try:
            h = yf.Ticker(ticker).history(period="2d")["Close"]
            return float(h.iloc[-1])
        except Exception:
            return None

    def get_from_prev_close(ticker: str) -> float | None:
        """Return fractional % change vs previous close (0.0123 = +1.23%)."""
        try:
            h = yf.Ticker(ticker).history(period="2d")["Close"]
            prev, cur = float(h.iloc[-2]), float(h.iloc[-1])
            return (cur - prev) / prev
        except Exception:
            return None

    def fmt_pct(x: float | None) -> str:
        if x is None:
            return "—"
        return f"{x*100:+.2f}%"

# -------- Optional outbound (email_webhook). Falls back to print -------------
try:
    from email_webhook import broadcast  # type: ignore
except Exception:
    def broadcast(subject: str, body: str) -> None:  # pragma: no cover
        print(f"\n=== {subject} ===\n{body}\n")

# =============================== Tunables ===================================
# You can adjust these or move them to config later if you want.
VIX_DEFENSIVE_LVL = 20.0          # VIX >= this → "defensive"
SPY_VIX_DIVERGENCE = 1.50         # percentage-point gap: VIX% - SPY% >= this
BREADTH_WEAK_GAP = -0.20 / 100.0  # RSP% - SPY% ≤ this → breadth weak

TICKERS = ["SPY", "QQQ", "IWM", "DIA", "RSP", "VIX"]

# ============================== Core Logic ==================================
def pct(tkr: str) -> float | None:
    return get_from_prev_close(tkr)

def collect() -> dict[str, float | None]:
    return {t: pct(t) for t in TICKERS}

def build_verdict(data: dict[str, float | None]) -> tuple[str, list[str]]:
    notes: list[str] = []

    spy = data.get("SPY")
    vix = data.get("VIX")
    rsp = data.get("RSP")

    # --- Volatility lens
    vol_note = "neutral"
    if vix is not None and vix * 100.0 >= VIX_DEFENSIVE_LVL:
        vol_note = "defensive"
    elif vix is not None and spy is not None and (vix * 100.0 - spy * 100.0) >= SPY_VIX_DIVERGENCE:
        vol_note = "risk-off stress"

    notes.append(f"Volatility: VIX {fmt_pct(vix)} → {vol_note}")

    # --- Breadth lens (RSP ~ equal-weight S&P)
    breadth_note = "n/a"
    if rsp is not None and spy is not None:
        gap = rsp - spy
        breadth_note = "weak" if gap <= BREADTH_WEAK_GAP else "aligned"
        notes.append(f"Breadth: RSP–SPY gap {fmt_pct(gap)} → {breadth_note}")
    else:
        notes.append("Breadth: (insufficient data)")

    # --- Verdict
    verdict = "⚠️ Defensive" if vol_note in {"defensive", "risk-off stress"} else "✅ Aligned / Neutral"
    return verdict, notes

def compose_text(verdict: str, notes: list[str], data: dict[str, float | None]) -> str:
    tz = "America/Phoenix"
    ts = now(tz).strftime("%a, %b %d %I:%M %p %Z")
    lines: list[str] = []
    lines.append(f"{ts} • North America Midday Verdict")
    lines.append("")
    lines.append(f"Verdict: **{verdict}**")
    lines.append("")
    lines.extend(notes)
    lines.append("")
    lines.append("Indices:")
    for k in ["SPY", "QQQ", "IWM", "DIA", "RSP", "VIX"]:
        lines.append(f"  • {k}: {fmt_pct(data.get(k))}")
    return "\n".join(lines)

def main() -> int:
    data = collect()
    verdict, notes = build_verdict(data)
    text = compose_text(verdict, notes, data)
    print(text)
    broadcast("NA Midday Verdict", text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

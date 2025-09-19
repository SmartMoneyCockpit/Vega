#!/usr/bin/env python3
import argparse, pathlib, datetime as dt
p=argparse.ArgumentParser(); p.add_argument("--tz",default="Europe/London"); p.add_argument("--out",default="output/morning_report_europe.md")
a=p.parse_args()
pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
now=dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
body=f"""# Morning Report — Europe
_Timezone: {a.tz} • Generated: {now}_

## Today’s Focus
- Placeholder bullets until real logic is wired.

## Market Internals
- Breadth: —
- Volatility: —
- RS vs STOXX/FTSE/DAX: —

## Watchlist
- (add tickers)
"""
pathlib.Path(a.out).write_text(body, encoding="utf-8")
print(f"[morning_report_europe] wrote {a.out}")

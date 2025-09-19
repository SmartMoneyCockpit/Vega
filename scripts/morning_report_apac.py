#!/usr/bin/env python3
import argparse, pathlib, datetime as dt
p=argparse.ArgumentParser(); p.add_argument("--tz",default="America/Los_Angeles"); p.add_argument("--out",default="output/morning_report_apac.md")
a=p.parse_args()
pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
now=dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
body=f"""# Afternoon Report — APAC
_Timezone: {a.tz} • Generated: {now}_

## Today’s Focus
- Placeholder bullets until real logic is wired.

## Market Internals
- Breadth: —
- Volatility: —
- RS vs Nikkei/ASX/HSI/KOSPI: —

## Watchlist
- (add tickers)
"""
pathlib.Path(a.out).write_text(body, encoding="utf-8")
print(f"[morning_report_apac] wrote {a.out}")

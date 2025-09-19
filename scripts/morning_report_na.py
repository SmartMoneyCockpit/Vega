#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Region Morning Report (real-ish)"""
import argparse, pathlib, datetime as dt
from typing import List, Tuple

def try_fetch(tickers: List[str]) -> Tuple[bool, str]:
    try:
        import pandas as pd  # noqa
        import yfinance as yf
        end = dt.datetime.utcnow()
        start = end - dt.timedelta(days=200)
        rows = []
        for t in tickers:
            hist = yf.download(t, start=start.date().isoformat(), end=end.date().isoformat(), progress=False, auto_adjust=True)
            if hist.empty or 'Close' not in hist:
                rows.append((t, 'n/a', 'n/a')); continue
            closes = hist['Close'].dropna()
            if len(closes) >= 2:
                last = float(closes.iloc[-1]); prev = float(closes.iloc[-2])
                chg = (last/prev - 1.0)*100.0
                rows.append((t, f"{last:.2f}", f"{chg:+.2f}%"))
            else:
                last = float(closes.iloc[-1]) if len(closes) else float('nan')
                rows.append((t, f"{last:.2f}", 'n/a'))
        md = ['| Ticker | Last | 1D % |', '|---|---:|---:|']
        for t,last,chg in rows: md.append(f"| {t} | {last} | {chg} |")
        return True, "\n".join(md)
    except Exception as e:
        return False, f"(Data fetch unavailable: {e})"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--tz", default="America/Los_Angeles")
    p.add_argument("--out", default="output/morning_report_na.md")
    a=p.parse_args()
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    now=dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    tickers = ["SPY","QQQ","DIA","IWM","^VIX"]
    ok, table = try_fetch(tickers)
    body=f"# Morning Report — NA\n_Timezone: {a.tz} • Generated: {now}_\n\n## Today’s Focus\n- Replace these bullets with your real catalysts list.\n\n## Market Snapshot\n{table}\n\n## Watchlist\n- (add tickers)\n"
    pathlib.Path(a.out).write_text(body, encoding="utf-8")
    print(f"[morning_report_na] wrote {a.out}")

if __name__ == "__main__":
    main()

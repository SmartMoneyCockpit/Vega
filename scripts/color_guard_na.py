#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Color Guard NA using 50DMA + VIX with fallback"""
import json, pathlib, datetime as dt
def compute_color(tickers, vix="^VIX"):
    try:
        import pandas as pd  # noqa
        import yfinance as yf
        end = dt.datetime.utcnow(); start = end - dt.timedelta(days=260)
        signals = []
        for t in tickers:
            hist = yf.download(t, start=start.date().isoformat(), end=end.date().isoformat(), progress=False, auto_adjust=True)
            closes = hist['Close'].dropna()
            if len(closes) < 60: signals.append(False); continue
            ma50 = closes.rolling(50).mean().iloc[-1]; last = closes.iloc[-1]
            signals.append(last > ma50)
        vix_hist = yf.download(vix, period="5d", progress=False)
        vix_last = float(vix_hist['Close'].dropna().iloc[-1]) if not vix_hist.empty else 20.0
        above = sum(1 for x in signals if x)
        if above >= 3 and vix_last < 20: color="green"
        elif above <= 1 or vix_last >= 25: color="red"
        else: color="yellow"
        return True, {"above_50dma": above, "vix": vix_last, "color": color}
    except Exception as e:
        return False, {"error": str(e), "color": "ok"}
payload = {"region": "NA", "generated_at_utc": dt.datetime.utcnow().isoformat(timespec="seconds")+"Z"}
ok, data = compute_color(["SPY","QQQ","DIA","IWM"])
payload.update(data)
out = pathlib.Path("alerts")/"color_guard_na.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"[color_guard_na] wrote {out}")

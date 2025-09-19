#!/usr/bin/env python3
import pathlib, datetime as dt
out = pathlib.Path("output/uptime_ping/ping.txt")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(f"pong {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}Z\n", encoding="utf-8")
print(f"[uptime_ping] wrote {out}")

#!/usr/bin/env python3
import csv, pathlib, datetime as dt, os
tz = os.environ.get("TZ","Europe/London")
out = pathlib.Path("assets")/ "econ_calendar_europe.csv"
out.parent.mkdir(parents=True, exist_ok=True)
today = dt.date.today().isoformat()
rows = [
  ["date","time_tz","region","event","impact"],
  [today,"08:00",tz,"Placeholder: PMI/CPI/IFO","–"],
]
with open(out, "w", newline="", encoding="utf-8") as f:
  csv.writer(f).writerows(rows)
print(f"[econ_calendar_europe] wrote {out}")

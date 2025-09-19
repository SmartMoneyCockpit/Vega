#!/usr/bin/env python3
import csv, pathlib, datetime as dt, os
tz = os.environ.get("TZ","America/Los_Angeles")
out = pathlib.Path("assets")/ "econ_calendar_apac.csv"
out.parent.mkdir(parents=True, exist_ok=True)
today = dt.date.today().isoformat()
rows = [
  ["date","time_tz","region","event","impact"],
  [today,"18:00",tz,"Placeholder: BoJ/Trade/Inflation","–"],
]
with open(out, "w", newline="", encoding="utf-8") as f:
  csv.writer(f).writerows(rows)
print(f"[econ_calendar_apac] wrote {out}")

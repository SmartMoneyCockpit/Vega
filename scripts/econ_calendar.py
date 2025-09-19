#!/usr/bin/env python3
import os, csv, pathlib, datetime as dt
region = os.getenv("REGION","NA")
tz = os.getenv("TZ","UTC")
rmap = {"EU":"europe","NA":"na","APAC":"apac"}
sfx = rmap.get(region, region.lower())
outdir = pathlib.Path("assets"); outdir.mkdir(parents=True, exist_ok=True)
out = outdir / f"econ_calendar_{sfx}.csv"
today = dt.date.today().isoformat()
rows = [
  ["date","time_tz","region","event","impact"],
  [today,"08:30",tz,"Placeholder generic econ calendar","–"],
]
with open(out,"w", newline="", encoding="utf-8") as f:
  csv.writer(f).writerows(rows)
print(f"[econ_calendar_fallback] wrote {out}")

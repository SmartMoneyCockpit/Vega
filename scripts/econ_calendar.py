#!/usr/bin/env python3
import os, csv, pathlib, datetime as dt
region = os.getenv("REGION","NA")
mapr = {"EU":"europe","NA":"na","APAC":"apac"}
sfx = mapr.get(region, region.lower())
tz = os.getenv("TZ","UTC")
out = pathlib.Path("assets")/f"econ_calendar_{sfx}.csv"
out.parent.mkdir(parents=True, exist_ok=True)
today = dt.date.today().isoformat()
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["date","time_tz","region","event","impact"]); w.writerow([today,"08:30",tz,"Placeholder","–"])
print(f"[econ_calendar_fallback] wrote {out}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Econ Calendar Europe: prefer data/, then data/templates/, else placeholder"""
import csv, pathlib, datetime as dt, os
def try_copy(srcs, out):
    for src in srcs:
        p = pathlib.Path(src)
        if p.exists() and p.stat().st_size > 0:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(p.read_bytes())
            return True, str(p)
    return False, None

def main():
    tz = os.environ.get("TZ","Europe/London")
    out = pathlib.Path("assets")/"econ_calendar_europe.csv"
    preferred = ["data/econ_calendar_europe.csv","data/templates/econ_calendar_europe.csv"]
    ok, used = try_copy(preferred, out)
    if not ok:
        today = dt.date.today().isoformat()
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["date","time_tz","region","event","impact"])
            w.writerow([today,"08:00",tz,"Placeholder: PMI/CPI/IFO","–"])
    print(f"[econ_calendar_europe] wrote {out}" + (f" (from {used})" if used else ""))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
'''
Minimal Economic Calendar builder.
Writes a CSV with a couple of placeholder events for the chosen region.
Usage: python scripts/econ_calendar_build.py --region NA --out outputs/econ_calendar/file.csv
'''
import argparse, csv, os, datetime

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--region", default="NA")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date_utc","region","event","importance","notes"])
        today = datetime.datetime.utcnow().date()
        w.writerow([today.isoformat(), args.region, "CPI (YoY)", "High", "Placeholder data"])
        w.writerow([(today + datetime.timedelta(days=1)).isoformat(), args.region, "FOMC Minutes", "High", "Placeholder data"])
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import datetime, os, csv

def main():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    os.makedirs("output/econ_calendar", exist_ok=True)
    out = f"output/econ_calendar/econ_calendar_{now.replace(' ','_').replace(':','-')}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp","region","event","note"])
        w.writerow([now,"NA","CPI Release","Placeholder"])
        w.writerow([now,"CA","BoC Rate Decision","Placeholder"])
        w.writerow([now,"MX","Banxico Statement","Placeholder"])
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()

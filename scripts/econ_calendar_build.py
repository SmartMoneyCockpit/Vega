#!/usr/bin/env python3
import datetime, os, csv

def main():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("output/econ_calendar", exist_ok=True)

    out_file = f"output/econ_calendar/econ_calendar_{now}.csv"
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "region", "event", "note"])
        writer.writerow([now, "NA", "CPI Release", "Placeholder"])
        writer.writerow([now, "CA", "BoC Rate Decision", "Placeholder"])
        writer.writerow([now, "MX", "Banxico Statement", "Placeholder"])

    print(f"[Econ Calendar] wrote {out_file}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import datetime, os

def main():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("output/europe/uptime_ping", exist_ok=True)
    out_file = f"output/europe/uptime_ping/uptime_ping_{now}.txt"
    with open(out_file, "w") as f:
        f.write("uptime_ping europe stub run at " + now + "\n")
    print(f"Wrote {out_file}")

if __name__ == "__main__":
    main()

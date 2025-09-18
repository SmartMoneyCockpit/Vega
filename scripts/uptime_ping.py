#!/usr/bin/env python3
import datetime, os

def main():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("output/uptime_ping", exist_ok=True)

    out_file = f"output/uptime_ping/uptime_{now}.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"Uptime Ping check at {now}\n")
        f.write("Placeholder: no real URLs checked.\n")

    print(f"[Uptime Ping] wrote {out_file}")

if __name__ == "__main__":
    main()

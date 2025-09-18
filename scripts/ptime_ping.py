#!/usr/bin/env python3
import datetime, os

def main():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    os.makedirs("output/uptime_ping", exist_ok=True)
    out = f"output/uptime_ping/uptime_{now.replace(' ','_').replace(':','-')}.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"Uptime Ping check at {now}\n")
        f.write("Placeholder: no real URLs checked.\n")
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import datetime, os

def main():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("output/na/econ_calendar", exist_ok=True)
    out_file = f"output/na/econ_calendar/econ_calendar_{now}.txt"
    with open(out_file, "w") as f:
        f.write("econ_calendar na stub run at " + now + "\n")
    print(f"Wrote {out_file}")

if __name__ == "__main__":
    main()

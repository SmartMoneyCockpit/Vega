#!/usr/bin/env python3
import datetime, os

def main():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("output/europe/color_guard", exist_ok=True)
    out_file = f"output/europe/color_guard/color_guard_{now}.txt"
    with open(out_file, "w") as f:
        f.write("color_guard europe stub run at " + now + "\n")
    print(f"Wrote {out_file}")

if __name__ == "__main__":
    main()

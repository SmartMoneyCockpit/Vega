#!/usr/bin/env python3
'''
Minimal Color Guard snapshot builder.
Emits a JSON file with a timestamp and dummy signals.
Usage: python scripts/color_guard_build.py --out outputs/color_guard/file.json
'''
import argparse, os, json, datetime, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    args = p.parse_args()

    data = {
        "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "dashboard": [
            {"symbol": "SPY", "signal": random.choice(["green","yellow","red"])},
            {"symbol": "QQQ", "signal": random.choice(["green","yellow","red"])},
            {"symbol": "IWM", "signal": random.choice(["green","yellow","red"])},
        ],
        "notes": "Replace this stub with real Color Guard logic when ready."
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        import json as _json
        _json.dump(data, f, indent=2)
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()

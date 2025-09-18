#!/usr/bin/env python3
import argparse, datetime, os

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tz", default=os.environ.get("TZ","America/Los_Angeles"))
    p.add_argument("--out", required=True)
    args = p.parse_args()

    now = datetime.datetime.utcnow()
    ts = now.strftime("%Y-%m-%d %H:%M UTC")

    md = f"""# Morning Report — North America

**Generated:** {ts}  
**Timezone (requested):** `{args.tz}`

---

## Macro & Calendar
- Placeholder for CPI/Fed/earnings.

## Breadth & Internals
- Placeholder internals.

## Sector Rotation
- Placeholder.

## Watchlist Highlights
- Placeholder.

## Actionables
- Buy Today / Wait / Avoid.
"""

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()

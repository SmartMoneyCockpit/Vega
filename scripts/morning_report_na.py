#!/usr/bin/env python3
import argparse, datetime, os, csv, io, urllib.request

def fetch_csv(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        data = r.read().decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(data)))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tz", default=os.environ.get("TZ","America/Los_Angeles"))
    p.add_argument("--out", required=True)
    args = p.parse_args()

    now = datetime.datetime.utcnow()
    ts = now.strftime("%Y-%m-%d %H:%M UTC")

    # Earnings list from repo variable COCKPIT_EARNINGS_CSV_URL (optional)
    earnings_md = "- (no items)"
    csv_url = os.environ.get("COCKPIT_EARNINGS_CSV_URL")
    if csv_url:
        try:
            rows = fetch_csv(csv_url)[:10]
            items = [f"- {r.get('ticker','?')} — {r.get('date','?')} {r.get('time','')}".strip() for r in rows]
            earnings_md = "\n".join(items) if items else earnings_md
        except Exception as e:
            earnings_md = f"- (error loading earnings: {e})"

    md = f"""# Morning Report — North America

**Generated:** {ts}  
**Timezone (requested):** `{args.tz}`

---

## Macro & Calendar
- CPI / FOMC / Jobs: (placeholder)
- **Upcoming earnings (top 10)**  
{earnings_md}

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

import argparse, csv, pathlib, datetime, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--region', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Minimal demo CSV headers (replace with your real earnings logic)
    rows = [
        ["date","ticker","company","region"],
    ]
    today = datetime.date.today().isoformat()
    sample = [("AAPL","Apple"),("MSFT","Microsoft"),("GOOGL","Alphabet"),("AMZN","Amazon")]
    for t,c in random.sample(sample, k=2):
        rows.append([today, t, c, args.region])

    with out.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"Wrote {out}")
if __name__ == "__main__":
    main()

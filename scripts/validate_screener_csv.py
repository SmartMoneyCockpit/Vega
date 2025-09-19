#!/usr/bin/env python3
import sys, os, glob, pandas as pd

REQUIRED_ANY = ["ticker", "symbol", "name"]
SEARCH_GLOBS = [
    "data/snapshots/*/*screener*.csv",
    "data/*screener*.csv",
    "reports/*screener*.csv",
    "output/*screener*.csv",
    "*screener*.csv",
]

def find_csv():
    for pattern in SEARCH_GLOBS:
        for path in glob.glob(pattern, recursive=True):
            try:
                if not os.path.isfile(path):
                    continue
                df = pd.read_csv(path)
                if not df.empty and len(df.columns) > 0:
                    return df, path
            except Exception as e:
                print(f"WARN: failed to read {path}: {e}", file=sys.stderr)
    return pd.DataFrame(), None

def coerce_str(s):
    if s is None:
        return ""
    try:
        if pd.isna(s):
            return ""
    except Exception:
        pass
    return str(s).strip()

def main():
    df, path = find_csv()
    if path is None:
        print("::error::No screener CSV found in expected locations.")
        sys.exit(2)

    have = [c for c in REQUIRED_ANY if c in df.columns]
    if not have:
        print(f"::error::Screener CSV missing all of expected columns: {REQUIRED_ANY}. Columns present: {list(df.columns)}")
        sys.exit(3)

    for col in REQUIRED_ANY:
        if col in df.columns:
            df[col] = df[col].apply(coerce_str)

    os.makedirs("out", exist_ok=True)
    out_path = "out/screener_clean.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Screener CSV validated and cleaned. Source: {path}. Rows: {len(df)}. Saved: {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

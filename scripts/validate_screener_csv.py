#!/usr/bin/env python3
import sys, os, glob, re
import pandas as pd

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
            if not os.path.isfile(path):
                continue
            try:
                df = pd.read_csv(path)
                if not df.empty and len(df.columns) > 0:
                    return df, path
            except Exception as e:
                print(f"::warning::Failed to read {path}: {e}")
    return pd.DataFrame(), None

def coerce_str(x):
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()

def parse_from_name(name):
    # (TICKER) pattern
    m = re.search(r"\(([A-Z.]{1,10})\)", name)
    if m:
        return m.group(1)
    # TICKER - Company pattern
    m = re.match(r"^([A-Z.]{1,10})\s+-\s+", name)
    if m:
        return m.group(1)
    return ""

def main():
    df, path = find_csv()
    if path is None:
        print("::error::No screener CSV found in expected locations.")
        return 2

    present = [c for c in REQUIRED_ANY if c in df.columns]
    if not present:
        print(f"::error::Screener CSV missing all expected columns: {REQUIRED_ANY}. Found: {list(df.columns)}")
        return 3

    # Coerce stringy columns
    for col in REQUIRED_ANY:
        if col in df.columns:
            df[col] = df[col].apply(coerce_str)

    # Build a derived ticker column to validate integrity
    if "ticker" not in df.columns:
        df["ticker"] = ""

    # Fill ticker from symbol if empty
    mask = df["ticker"].eq("")
    if "symbol" in df.columns:
        df.loc[mask, "ticker"] = df.loc[mask, "symbol"]

    # Parse from name if still empty
    if "name" in df.columns:
        still = df["ticker"].eq("")
        df.loc[still, "ticker"] = df.loc[still, "name"].apply(parse_from_name)

    # Final check: at least 1 non-empty ticker
    non_empty = df["ticker"].str.len() > 0
    if not non_empty.any():
        print("::error::All ticker values are empty after cleaning/derivation. CSV is malformed.")
        return 4

    os.makedirs("out", exist_ok=True)
    out_path = "out/screener_clean.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Screener CSV validated. Source: {path}. Rows: {len(df)}. Non-empty tickers: {int(non_empty.sum())}. Saved: {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

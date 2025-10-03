# scripts/verify_health.py
# Prints a quick health summary: DB path, row counts, latest snapshot files.

import os, glob, pandas as pd
import db_adapter as db

def count(df): return 0 if df is None else int(len(df))

def newest(pattern):
    files = glob.glob(pattern)
    if not files: return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def main():
    db_path = os.getenv("VEGA_DB_PATH", "data/vega.db")
    print("DB PATH:", db_path)
    print("Positions:", count(db.load_positions()))
    print("Signals:", count(db.load_signals()))
    print("Breadth:", count(db.load_breadth()))
    print("RS:", count(db.load_rs()))
    print("Latest positions CSV:", newest("snapshots/positions_*.csv"))
    print("Latest digest ZIP:", newest("snapshots/digest_*.zip"))
    print("Latest sector flips:", newest("alerts/sector_flips.json"))

if __name__ == "__main__":
    main()

# scripts/seed_db.py
# Idempotent seeder with robust error logging.

import os, sys, sqlite3, contextlib, traceback
import pandas as pd

# Ensure repo root on path so we can import db_adapter when running from scripts/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

DB_PATH = os.getenv("VEGA_DB_PATH", "data/vega.db")

def import_db():
    try:
        import db_adapter as db
        return db
    except Exception as e:
        print("FATAL: failed to import db_adapter:", e)
        traceback.print_exc()
        sys.exit(1)

def _wipe_tables():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with contextlib.closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.cursor()
        for table in ("positions","signals","breadth","rs"):
            try:
                cur.execute(f"DELETE FROM {table}")
            except Exception:
                # table may not exist yet; ignore
                pass
        con.commit()

# Starter rows
positions = pd.DataFrame([
    {"Ticker":"HPR.TO","Qty":1000,"Avg Cost":25.0,"Last":25.4},
    {"Ticker":"ZPR.TO","Qty":1000,"Avg Cost":9.50,"Last":9.55},
    {"Ticker":"HSAV.TO","Qty":200,"Avg Cost":29.0,"Last":29.02},
])
signals = pd.DataFrame([
    {"Ticker":"SPXU","Setup":"Buy Today","Reason":"Hedge basket","Country":"USA"},
    {"Ticker":"SQQQ","Setup":"Buy Today","Reason":"NDX RS down","Country":"USA"},
    {"Ticker":"RWM","Setup":"Wait","Reason":"Risk-off fading","Country":"USA"},
])
breadth = pd.DataFrame([
    {"Metric":"VIX","Value":"18.7","Status":"Neutral"},
    {"Metric":"%>50DMA (SPX)","Value":"47%","Status":"Caution"},
    {"Metric":"%>200DMA (SPX)","Value":"62%","Status":"Healthy"},
    {"Metric":"ADV/DEC (NYSE)","Value":"0.82","Status":"Risk-Off"},
])
rs = pd.DataFrame([
    {"Bucket":"USA","RS Trend":"🟡"},
    {"Bucket":"Canada","RS Trend":"🟡"},
    {"Bucket":"Mexico","RS Trend":"🟢"},
    {"Bucket":"Tech","RS Trend":"🟠"},
    {"Bucket":"Industrials","RS Trend":"🟢"},
])

def main():
    print("Seeding to:", DB_PATH)
    db = import_db()
    try:
        _wipe_tables()
        db.upsert_positions(positions)
        db.upsert_signals(signals)
        db.upsert_breadth(breadth)
        db.upsert_rs(rs)
        print("Seed complete.")
        print("Counts -> positions:", len(db.load_positions()),
              "signals:", len(db.load_signals()),
              "breadth:", len(db.load_breadth()),
              "rs:", len(db.load_rs()))
    except Exception as e:
        print("Seed FAILED:", e)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

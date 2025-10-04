# scripts/seed_db.py
# One-shot: idempotent seeder. Force‑clears tables then inserts starter rows.
# Uses VEGA_DB_PATH if set; defaults to data/vega.db

import os, sys, sqlite3, contextlib
import pandas as pd

# Ensure repo root on sys.path so db_adapter is importable from scripts/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import db_adapter as db

DB_PATH = os.getenv("VEGA_DB_PATH", "data/vega.db")

def _wipe_tables():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with contextlib.closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.cursor()
        cur.execute("DELETE FROM positions")
        cur.execute("DELETE FROM signals")
        cur.execute("DELETE FROM breadth")
        cur.execute("DELETE FROM rs")
        # keep rs_history intact (it's your time series)
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
    _wipe_tables()
    db.upsert_positions(positions)
    db.upsert_signals(signals)
    db.upsert_breadth(breadth)
    db.upsert_rs(rs)
    print("Seed complete.")
    # Echo counts
    print("Counts -> positions:", len(db.load_positions()),
          "signals:", len(db.load_signals()),
          "breadth:", len(db.load_breadth()),
          "rs:", len(db.load_rs()))

if __name__ == "__main__":
    main()

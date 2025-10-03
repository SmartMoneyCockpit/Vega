# scripts/seed_db.py
# One-shot: seeds SQLite with starter rows for positions, signals, breadth, and RS.
# Where the DB lives:
#   VEGA_DB_PATH (recommended on Render) or falls back to data/vega.db

import os
import pandas as pd
import db_adapter as db

# Starter rows (edit as you like)
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
    db.upsert_positions(positions)
    db.upsert_signals(signals)
    db.upsert_breadth(breadth)
    db.upsert_rs(rs)
    print("Seed complete. You can now open Admin / RS Dashboard immediately.")

if __name__ == "__main__":
    main()

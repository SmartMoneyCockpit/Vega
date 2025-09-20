
from __future__ import annotations
import os, json, datetime as dt
import pandas as pd

DEFAULT_RULES = {
  "rel_move_thresh": 0.006,   # 0.6%
  "momentum_cross": True,
  "min_vol_mult": 1.2,
  "hold_minutes": 15
}

def evaluate_flips(df_sector: pd.DataFrame, df_index: pd.DataFrame) -> list[dict]:
    """Return list of flip events.
    Expect columns: time, ret, vol for both sector and index (intraday 5-15m bars).
    """
    out = []
    if df_sector.empty or df_index.empty:
        return out
    merged = pd.merge_asof(df_sector.sort_values("time"), df_index.sort_values("time"), on="time", suffixes=("_sec","_idx"))
    rel = merged["ret_sec"] - merged["ret_idx"]
    # Sign change + magnitude threshold
    sign = (rel > 0).astype(int) - (rel < 0).astype(int)
    flip = (sign != sign.shift(1)) & (rel.abs() >= DEFAULT_RULES["rel_move_thresh"])
    for i, row in merged[flip].iterrows():
        out.append({
            "time": row["time"].isoformat() if hasattr(row["time"], "isoformat") else str(row["time"]),
            "rel_move": float(rel.iloc[i]),
            "note": "Sector flip relative to index"
        })
    return out

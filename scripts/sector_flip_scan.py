# scripts/sector_flip_scan.py
# Schedules: run hourly (or your cadence) on Render.
# Reads latest sector returns (placeholder/demo) and writes alerts/sector_flips.json
# You can replace `get_sector_data()` with a real data source later.

import os, json, time
from datetime import datetime, timezone

ALERTS_DIR = os.getenv("ALERTS_DIR", "alerts")
os.makedirs(ALERTS_DIR, exist_ok=True)

# ---- CONFIG (defaults per your standing rules) ----
RELATIVE_CHANGE_THRESHOLD = float(os.getenv("SECTOR_REL_CHANGE", "0.6"))  # % vs country index
MOMENTUM_CROSS = True  # placeholder; you can tie to a real EMA(10/30) later

def get_sector_data():
    """Return demo sector data. Replace with TradingView/VectorVest pulls later.
    Expected format: list of dicts with keys: name, country, rel_change (float), momentum_cross (bool)
    """
    return [
        {"name": "Technology", "country": "USA", "rel_change": 0.7, "momentum_cross": True},
        {"name": "Industrials", "country": "USA", "rel_change": -0.8, "momentum_cross": True},
        {"name": "Materials", "country": "USA", "rel_change": 0.1, "momentum_cross": False},
        {"name": "Financials", "country": "USA", "rel_change": -0.2, "momentum_cross": False},
        {"name": "Staples", "country": "USA", "rel_change": 0.9, "momentum_cross": True},
    ]

def classify_flip(item):
    # Rule: flip if rel_change magnitude >= threshold OR momentum_cross True
    rc = item.get("rel_change", 0.0)
    mc = bool(item.get("momentum_cross", False))
    flip = abs(rc) >= RELATIVE_CHANGE_THRESHOLD or mc
    direction = "UP" if rc >= 0 else "DOWN"
    return flip, direction

def main():
    ts = datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d_%H%M%S')
    data = get_sector_data()
    flips = []
    for it in data:
        do_flip, direction = classify_flip(it)
        if do_flip:
            flips.append({
                "timestamp": ts,
                "sector": it["name"],
                "country": it.get("country","USA"),
                "direction": direction,
                "rel_change": it.get("rel_change",0.0),
                "momentum_cross": bool(it.get("momentum_cross", False)),
            })
    out = {
        "generated_at": ts,
        "threshold": RELATIVE_CHANGE_THRESHOLD,
        "flips": flips
    }
    with open(os.path.join(ALERTS_DIR, 'sector_flips.json'), 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {len(flips)} flips to {ALERTS_DIR}/sector_flips.json at {ts}")

if __name__ == "__main__":
    main()

"""
Local IBKR scan runner (template).
- Run on your laptop/VM where IB Gateway/TWS is reachable.
- Writes CSV: reports/scanner/ibkr_latest.csv then you can commit it to vega-data.
"""
import time, csv
from pathlib import Path

def main():
    out = Path("reports/scanner"); out.mkdir(parents=True, exist_ok=True)
    # TODO: integrate ib_insync + your scan logic here
    # For now, write a mock CSV so the UI can render
    rows = [
        {"symbol":"AAPL","last":230.11,"vol":"34.5M","notes":"Large-cap tech"},
        {"symbol":"MSFT","last":410.22,"vol":"22.1M","notes":"Mega-cap tech"},
    ]
    with open(out/"ibkr_latest.csv","w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print("Wrote", out/"ibkr_latest.csv")

if __name__ == "__main__":
    main()

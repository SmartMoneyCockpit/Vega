
# src/jobs/refresh_ibkr.py
import os, json
from services.ibkr_sync import fetch_ibkr_symbols
from filters.tradable import filter_tradable

DATA_DIR = os.getenv("DATA_DIR", "data")
APPROVED_JSON = os.path.join(DATA_DIR, "approved_tickers.json")
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    symbols = fetch_ibkr_symbols()
    approved = filter_tradable(symbols)
    with open(APPROVED_JSON, "w", encoding="utf-8") as f:
        json.dump({"approved": approved}, f, indent=2)
    print(f"[refresh_ibkr] wrote {len(approved)} -> {APPROVED_JSON}")

if __name__ == "__main__":
    main()

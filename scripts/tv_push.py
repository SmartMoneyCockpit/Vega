import os, sys, json, argparse, time
from pathlib import Path
import requests

TV_BASE = "https://www.tradingview.com"
SESSION = os.getenv("TV_SESSION", "").strip()
USER    = os.getenv("TV_USER", "").strip()  # optional

def headers():
    return {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": TV_BASE + "/",
        "Origin": TV_BASE,
    }

def http():
    s = requests.Session()
    if not SESSION:
        raise SystemExit("Missing TV_SESSION env var.")
    s.headers.update(headers())
    s.cookies.set("sessionid", SESSION, domain=".tradingview.com", path="/", secure=True)
    return s

def load_candidates(region):
    p = Path(__file__).resolve().parents[1] / "outputs" / f"candidates_{region}.txt"
    if not p.exists():
        # fallback demo if none yet
        p.write_text("AAPL\nMSFT\nNVDA\n", encoding="utf-8")
    syms = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    # Normalize (TV accepts plain tickers for US; add exchange prefixes yourself if needed)
    return syms

def get_lists(session):
    # own lists (when logged in) – username not required
    r = session.get(TV_BASE + "/api/v1/symbols_list/")
    r.raise_for_status()
    return r.json()

def resolve_list_id(session, list_name):
    for lst in get_lists(session):
        if lst.get("name") == list_name:
            return lst.get("id")
    raise SystemExit(f"Watchlist '{list_name}' not found on TradingView.")

def clear_list(session, list_id):
    # fetch symbols currently in the list (if API returns them)
    r = session.get(f"{TV_BASE}/api/v1/symbols_list/{list_id}/")
    r.raise_for_status()
    data = r.json()
    symbols = [s.get("symbol", "") for s in data.get("symbols", [])]
    # remove existing (best-effort)
    for sym in symbols:
        try:
            session.delete(f"{TV_BASE}/api/v1/symbols_list/{list_id}/symbols/", json={"symbol": sym})
        except Exception:
            pass

def add_symbols(session, list_id, symbols):
    # Add in small batches
    for sym in symbols:
        payload = {"symbol": sym}
        r = session.post(f"{TV_BASE}/api/v1/symbols_list/{list_id}/symbols/", json=payload)
        if r.status_code >= 300:
            print(f"Warn: add {sym} -> {r.status_code}: {r.text[:200]}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="US", help="US, CA, MX, ...")
    ap.add_argument("--list", default="candidates", choices=["candidates","monitor"], help="which list to update")
    args = ap.parse_args()

    region = args.region.upper()
    env_key = "TV_WATCHLIST_CANDIDATES_" + region if args.list == "candidates" else "TV_WATCHLIST_MONITOR_" + region
    list_name = os.getenv(env_key)
    if not list_name:
        raise SystemExit(f"Missing env var {env_key} with your watchlist name.")

    syms = load_candidates(region)
    print(f"Loaded {len(syms)} symbols for region {region}: {syms[:10]}{' …' if len(syms)>10 else ''}")

    s = http()
    list_id = resolve_list_id(s, list_name)
    print(f"Resolved watchlist '{list_name}' → id {list_id}")

    clear_list(s, list_id)
    add_symbols(s, list_id, syms)
    print("Done updating TradingView watchlist.")

if __name__ == "__main__":
    main()

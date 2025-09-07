import os, sys, argparse
from pathlib import Path
import requests

WWW = "https://www.tradingview.com"

SESSION      = os.getenv("TV_SESSION", "").strip()
SESSION_SIGN = os.getenv("TV_SESSION_SIGN", "").strip()
DEVICE       = os.getenv("TV_DEVICE", "").strip()   # value of device_t or device_id cookie

def new_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": WWW + "/",
        "Origin": WWW,
        "X-Requested-With": "XMLHttpRequest",
    })
    if not SESSION:
        sys.exit("Missing TV_SESSION env var.")
    # cookies
    s.cookies.set("sessionid", SESSION, domain=".tradingview.com", path="/", secure=True)
    if SESSION_SIGN:
        s.cookies.set("sessionid_sign", SESSION_SIGN, domain=".tradingview.com", path="/", secure=True)
    if DEVICE:
        # some accounts expose device_t, some device_id — set both
        s.cookies.set("device_t", DEVICE, domain=".tradingview.com", path="/", secure=True)
        s.cookies.set("device_id", DEVICE, domain=".tradingview.com", path="/", secure=True)
    return s

def req(s, method, path, json=None):
    """Always hit www; never follow redirects to mm.*"""
    url = WWW + path
    r = s.request(method, url, json=json, allow_redirects=False)
    print(f"[tv_push] {method} {path} -> {r.status_code}")
    return r

def list_watchlists(s):
    for path in ("/api/v1/symbols_list/", "/api/v1/symbols_list/?personal=1"):
        r = req(s, "GET", path)
        if r.status_code == 200:
            return r.json()
    sys.exit(f"Could not list watchlists on www; last status={r.status_code} body={r.text[:200]}")

def resolve_list_id(s, name):
    lists = list_watchlists(s)
    for item in lists:
        if item.get("name") == name:
            return item.get("id")
    print("[tv_push] Available lists (first 10):", [it.get("name") for it in lists][:10])
    sys.exit(f"Watchlist '{name}' not found")

def load_candidates(region):
    p = Path(__file__).resolve().parents[1] / "outputs" / f"candidates_{region}.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("AAPL\nMSFT\nNVDA\n", encoding="utf-8")
    return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]

def update_list(s, list_id, symbols):
    # fetch & clear existing
    r = req(s, "GET", f"/api/v1/symbols_list/{list_id}/")
    if r.status_code == 200:
        try:
            existing = [x.get("symbol","") for x in r.json().get("symbols", [])]
        except Exception:
            existing = []
        for sym in existing:
            _ = req(s, "DELETE", f"/api/v1/symbols_list/{list_id}/symbols/", json={"symbol": sym})
    # add new
    for sym in symbols:
        resp = req(s, "POST", f"/api/v1/symbols_list/{list_id}/symbols/", json={"symbol": sym})
        if resp.status_code >= 300:
            print(f"[tv_push] Warn add {sym} -> {resp.status_code}: {resp.text[:200]}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="US")
    ap.add_argument("--list", default="candidates", choices=["candidates","monitor"])
    args = ap.parse_args()

    region = args.region.upper()
    env_key = "TV_WATCHLIST_CANDIDATES_" + region if args.list == "candidates" else "TV_WATCHLIST_MONITOR_" + region
    list_name = os.getenv(env_key, "").strip()
    if not list_name:
        sys.exit(f"Missing env var {env_key}")

    syms = load_candidates(region)
    print(f"[tv_push] Loaded {len(syms)} symbols for {region}: {syms[:10]}{' …' if len(syms)>10 else ''}")

    s = new_session()
    list_id = resolve_list_id(s, list_name)
    print(f"[tv_push] Resolved '{list_name}' -> id {list_id}")
    update_list(s, list_id, syms)
    print("[tv_push] Done updating TradingView watchlist.")

if __name__ == "__main__":
    main()

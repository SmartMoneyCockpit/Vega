import os, sys, argparse
from pathlib import Path
import requests

WWW = "https://www.tradingview.com"

SESSION      = os.getenv("TV_SESSION", "").strip()
SESSION_SIGN = os.getenv("TV_SESSION_SIGN", "").strip()
DEVICE       = os.getenv("TV_DEVICE", "").strip()   # value from cookie device_t or device_id

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
        s.cookies.set("device_t", DEVICE,  domain=".tradingview.com", path="/", secure=True)
        s.cookies.set("device_id", DEVICE, domain=".tradingview.com", path="/", secure=True)
    return s

def req(s, method, path, json=None):
    url = WWW + path
    r = s.request(method, url, json=json, allow_redirects=False)  # never follow to mm.*
    print("[tv_push] {} {} -> {}".format(method, path, r.status_code))
    return r

def list_watchlists(s):
    for path in ("/api/v1/symbols_list/", "/api/v1/symbols_list/?personal=1"):
        r = req(s, "GET", path)
        if r.status_code == 200:
            return r.json()
    sys.exit("Could not list watchlists on www; last status={} body={}".format(r.status_code, r.text[:200]))

def resolve_list_id(s, name):
    lists = list_watchlists(s)
    for item in lists:
        if item.get("name") == name:
            return item.get("id")
    print("[tv_push] Available lists (first 10):", [it.get("name") for it in lists][:10])
    sys.exit("Watchlist '{}' not found".format(name))

def load_candidates(region):
    p = Path(__file__).resolve().parents[1] / "outputs" / "candidates_{}.txt".format(region)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("AAPL\nMSFT\nNVDA\n", encoding="utf-8")
    return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]

def update_list(s, list_id, symbols):
    r = req(s, "GET", "/api/v1/symbols_list/{}/".format(list_id))
    if r.status_code == 200:
        try:
            existing = [x.get("symbol","") for x in r.json().get("symbols", [])]
        except Exception:
            existing = []
        for sym in existing:
            _ = req(s, "DELETE", "/api/v1/symbols_list/{}/symbols/".format(list_id), json={"symbol": sym})
    for sym in symbols:
        resp = req(s, "POST", "/api/v1/symbols_list/{}/symbols/".format(list_id), json={"symbol": sym})
        if resp.status_code >= 300:
            print("[tv_push] Warn add {} -> {}: {}".format(sym, resp.status_code, resp.text[:200]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="US")
    ap.add_argument("--list", default="candidates", choices=["candidates","monitor"])
    args = ap.parse_args()

    region = args.region.upper()
    env_key = ("TV_WATCHLIST_CANDIDATES_" + region) if args.list == "candidates" else ("TV_WATCHLIST_MONITOR_" + region)
    list_name = os.getenv(env_key, "").strip()
    if not list_name:
        sys.exit("Missing env var {}".format(env_key))

    syms = load_candidates(region)
    print("[tv_push] Loaded {} symbols for {}: {}{}".format(
        len(syms), region, syms[:10], " …" if len(syms) > 10 else "")
    )

    s = new_session()
    list_id = resolve_list_id(s, list_name)
    print("[tv_push] Resolved '{}' -> id {}".format(list_name, list_id))
    update_list(s, list_id, syms)
    print("[tv_push] Done updating TradingView watchlist.")

if __name__ == "__main__":
    main()

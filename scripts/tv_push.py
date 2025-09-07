import os, sys, json, argparse
from pathlib import Path
import requests

WWW = "https://www.tradingview.com"

SESSION       = os.getenv("TV_SESSION", "").strip()
SESSION_SIGN  = os.getenv("TV_SESSION_SIGN", "").strip()
DEVICE        = os.getenv("TV_DEVICE", "").strip()

def session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": WWW + "/",
        "Origin": WWW,
        "X-Requested-With": "XMLHttpRequest",
    })
    if not SESSION:
        raise SystemExit("Missing TV_SESSION env var.")
    s.cookies.set("sessionid", SESSION, domain=".tradingview.com", path="/", secure=True)
    if SESSION_SIGN:
        s.cookies.set("sessionid_sign", SESSION_SIGN, domain=".tradingview.com", path="/", secure=True)
    if DEVICE:
        s.cookies.set("device_id", DEVICE, domain=".tradingview.com", path="/", secure=True)
    return s

def get_www(s, path):
    """GET on www only; never follow redirects to mm.*"""
    r = s.get(WWW + path, allow_redirects=False)
    # If we ever get redirected to mm.*, re-try on www
    if r.is_redirect:
        return s.get(WWW + path, allow_redirects=False)
    return r

def post_www(s, path, json_payload):
    r = s.post(WWW + path, json=json_payload, allow_redirects=False)
    if r.is_redirect:
        return s.post(WWW + path, json=json_payload, allow_redirects=False)
    return r

def delete_www(s, path, json_payload):
    r = s.delete(WWW + path, json=json_payload, allow_redirects=False)
    if r.is_redirect:
        return s.delete(WWW + path, json=json_payload, allow_redirects=False)
    return r

def load_candidates(region):
    p = Path(__file__).resolve().parents[1] / "outputs" / f"candidates_{region}.txt"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("AAPL\nMSFT\nNVDA\n", encoding="utf-8")
    return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]

def list_watchlists(s):
    # Some accounts prefer the query param; try both on WWW
    for path in ("/api/v1/symbols_list/", "/api/v1/symbols_list/?personal=1"):
        r = get_www(s, path)
        if r.status_code == 200:
            return r.json()
    raise SystemExit(f"Could not list watchlists on www; last status={r.status_code}, body={r.text[:200]}")

def resolve_list_id(s, list_name):
    lists = list_watchlists(s)
    for item in lists:
        if item.get("name") == list_name:
            return item.get("id")
    names = [it.get("name") for it in lists]
    raise SystemExit(f"Watchlist '{list_name}' not found. Available (first 10): {names[:10]}")

def clear_and_add(s, list_id, symbols):
    r = get_www(s, f"/api/v1/symbols_list/{list_id}/")
    if r.status_code == 200:
        data = r.json()
        for sym in [x.get("symbol","") for x in data.get("symbols", [])]:
            try:
                delete_www(s, f"/api/v1/symbols_list/{list_id}/symbols/", {"symbol": sym})
            except Exception: pass
    for sym in symbols:
        resp = post_www(s, f"/api/v1/symbols_list/{list_id}/symbols/", {"symbol": sym})
        if resp.status_code >= 300:
            print(f"[tv_push] Warn add {sym} -> {resp.status_code]()

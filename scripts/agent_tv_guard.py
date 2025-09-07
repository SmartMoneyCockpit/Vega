# === TV_GUARD v1 (auto-login + push) ===
import os, sys, json, time, argparse
from pathlib import Path
import requests

WWW = "https://www.tradingview.com"

def load_candidates(region):
    p = Path(__file__).resolve().parents[1] / "outputs" / f"candidates_{region}.txt"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("AAPL\nMSFT\nNVDA\n", encoding="utf-8")
    return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]

def new_session(cookies=None):
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": WWW + "/",
        "Origin": WWW,
        "X-Requested-With": "XMLHttpRequest",
    })
    if cookies:
        for k,v in cookies.items():
            s.cookies.set(k, v, domain=".tradingview.com", path="/", secure=True)
    return s

def req(s, method, path, json_payload=None):
    url = WWW + path
    r = s.request(method, url, json=json_payload, allow_redirects=False)  # refuse mm.* redirects
    print("[TV_GUARD]", method, path, "->", r.status_code)
    return r

def list_watchlists(s):
    for path in ("/api/v1/symbols_list/", "/api/v1/symbols_list/?personal=1"):
        r = req(s, "GET", path)
        if r.status_code == 200:
            return r.json()
    return None

def resolve_list_id(s, name):
    lists = list_watchlists(s)
    if not lists: return None
    for item in lists:
        if item.get("name") == name:
            return item.get("id")
    print("[TV_GUARD] Available lists (first 10):", [it.get("name") for it in lists][:10])
    return None

def update_list(s, list_id, symbols):
    r = req(s, "GET", f"/api/v1/symbols_list/{list_id}/")
    existing = []
    if r.status_code == 200:
        try:
            existing = [x.get("symbol","") for x in r.json().get("symbols", [])]
        except Exception:
            pass
    for sym in existing:
        _ = req(s, "DELETE", f"/api/v1/symbols_list/{list_id}/symbols/", json_payload={"symbol": sym})
    for sym in symbols:
        resp = req(s, "POST", f"/api/v1/symbols_list/{list_id}/symbols/", json_payload={"symbol": sym})
        if resp.status_code >= 300:
            print("[TV_GUARD] WARN add", sym, "->", resp.status_code, resp.text[:200])

# ---------- Headless login (Playwright) ----------
from contextlib import contextmanager
def _get_totp():
    secret = os.getenv("TV_TOTP_SECRET","").replace(" ","").strip()
    if not secret: return None
    try:
        import pyotp
        return pyotp.TOTP(secret).now()
    except Exception:
        return None

@contextmanager
def pw_context():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            yield page, context
        finally:
            context.close()
            browser.close()

def do_headless_login(user, pwd):
    print("[TV_GUARD] Headless login…")
    with pw_context() as (page, ctx):
        page.goto(WWW + "/")
        # Open sign-in
        for sel in ["text=Sign in", "button:has-text('Sign in')", "a[href*='signin']"]:
            try:
                page.locator(sel).first.click(timeout=2500)
                break
            except Exception:
                pass
        # Choose Email if needed
        for sel in ["button:has-text('Email')", "text=Email", "button[aria-label*='Email']"]:
            try:
                page.locator(sel).first.click(timeout=2000)
                break
            except Exception:
                pass
        page.locator("input[name='username'], input[type='email']").first.fill(user)
        page.locator("input[name='password']").first.fill(pwd)
        page.locator("button:has-text('Sign in'), button[type='submit']").first.click()
        # 2FA if prompted
        code = _get_totp()
        if code:
            try:
                page.locator("input[type='tel'], input[name='code']").first.fill(code)
                page.locator("button:has-text('Confirm'), button:has-text('Verify')").first.click()
            except Exception:
                pass
        page.wait_for_load_state("networkidle", timeout=15000)
        cookies = {}
        for c in ctx.cookies(WWW):
            if c.get("name") in ("sessionid","sessionid_sign","device_id","device_t"):
                cookies[c["name"]] = c["value"]
        print("[TV_GUARD] Cookies:", list(cookies.keys()))
        return cookies

# -------------- main --------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="US")
    ap.add_argument("--list", default="candidates", choices=["candidates","monitor"])
    args = ap.parse_args()

    region = args.region.upper()
    key = "TV_WATCHLIST_CANDIDATES_" + region if args.list=="candidates" else "TV_WATCHLIST_MONITOR_" + region
    list_name = os.getenv(key, "").strip()
    if not list_name:
        sys.exit("Missing env var {}".format(key))

    # Try with any existing cookies first (optional)
    ck_env = {}
    for k in ("TV_SESSION","TV_SESSION_SIGN","TV_DEVICE"):
        v = os.getenv(k, "").strip()
        if v:
            if k=="TV_SESSION": ck_env["sessionid"]=v
            elif k=="TV_SESSION_SIGN": ck_env["sessionid_sign"]=v
            elif k=="TV_DEVICE":
                ck_env["device_id"]=v; ck_env["device_t"]=v

    s = new_session(ck_env if ck_env else None)
    list_id = resolve_list_id(s, list_name)
    if not list_id:
        user = os.getenv("TV_LOGIN_USER","").strip()
        pwd  = os.getenv("TV_LOGIN_PASS","").strip()
        if not user or not pwd:
            sys.exit("Missing TV_LOGIN_USER / TV_LOGIN_PASS for auto-login.")
        ck = do_headless_login(user, pwd)
        if not ck or "sessionid" not in ck:
            sys.exit("Auto-login failed (no session cookies).")
        s = new_session(ck)
        list_id = resolve_list_id(s, list_name)
        if not list_id:
            sys.exit("Watchlist '{}' not reachable after login.".format(list_name))

    syms = load_candidates(region)
    print("[TV_GUARD] Loaded", len(syms), "symbols for", region, ":", syms[:10], ("…" if len(syms)>10 else ""))
    print("[TV_GUARD] Resolved '{}' -> id {}".format(list_name, list_id))
    update_list(s, list_id, syms)
    print("[TV_GUARD] Done")

if __name__ == "__main__":
    main()

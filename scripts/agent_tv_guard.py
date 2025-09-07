#!/usr/bin/env python3
"""
TV Guard (TradingView helper)
- Fetches symbols list from your API (with fallbacks)
- Logs into TradingView headlessly (supports iframe form + cookie-based bypass)
- Prints candidate symbols when called with: --region US --list candidates

Drop-in file to replace scripts/agent_tv_guard.py
"""

from __future__ import annotations

import os
import re
import sys
import json
import time
import base64
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


# ------------ Config / ENV ------------

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
TV_USER = os.getenv("TV_USER", "")
TV_PWD = os.getenv("TV_PWD", "")
TV_COOKIES_JSON_B64 = os.getenv("TV_COOKIES_JSON_B64")  # optional base64-encoded Playwright cookies JSON
TIMEZONE = os.getenv("TZ", "America/Los_Angeles")

DEBUG_DIR = Path(os.getenv("TV_DEBUG_DIR", "/opt/render/project/src/_debug"))
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


# ------------ Utilities ------------

def log(msg: str) -> None:
    print(f"[TV_GUARD] {msg}", flush=True)


def safe_json_print(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2), flush=True)


# ------------ Symbols API (with fallbacks) ------------

def get_symbols_list(personal: bool = False) -> List[str]:
    """
    Try a few likely API paths. If none work, return a safe fallback.
    Supports either {"symbols": [...]} or raw list [...]
    """
    params = {"personal": 1} if personal else {}

    candidates = [
        "/api/v1/symbols_list/",
        "/api/v1/symbols",
        "/api/v1/symbols/list",
    ]
    for path in candidates:
        url = f"{API_BASE}{path}"
        try:
            r = requests.get(url, params=params, timeout=20)
            log(f"GET {url}{'?' + 'personal=1' if personal else ''} -> {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and isinstance(data.get("symbols"), list):
                    return data["symbols"]
                if isinstance(data, list):
                    return data
        except Exception as e:
            log(f"GET {url} failed: {e}")

    log("symbols endpoint not found; using fallback: SPY, QQQ, IWM")
    return ["SPY", "QQQ", "IWM"]


# ------------ TradingView Login ------------

def _try_cookie_login(ctx) -> bool:
    """
    If TV_COOKIES_JSON_B64 is set, attempt cookie-based login (skips fragile forms).
    Returns True if landing on tradingview.com as an authenticated session.
    """
    if not TV_COOKIES_JSON_B64:
        return False

    try:
        cookies = json.loads(base64.b64decode(TV_COOKIES_JSON_B64).decode("utf-8"))
    except Exception as e:
        log(f"Bad TV_COOKIES_JSON_B64: {e}")
        return False

    try:
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.goto("https://www.tradingview.com", wait_until="domcontentloaded", timeout=60000)
        # If it doesn't bounce to /accounts/signin, assume cookies are valid enough
        if "accounts/signin" not in page.url:
            log("Cookie login OK")
            page.close()
            return True
        page.close()
    except Exception as e:
        log(f"Cookie login failed: {e}")
    return False


def _save_debug(page) -> None:
    try:
        png_path = DEBUG_DIR / "tvguard_login_fail.png"
        html_path = DEBUG_DIR / "tvguard_login_fail.html"
        page.screenshot(path=str(png_path), full_page=True)
        html = page.content()
        html_path.write_text(html, encoding="utf-8")
        log(f"Saved login debug to {DEBUG_DIR}")
    except Exception as e:
        log(f"Could not save debug artifacts: {e}")


def do_headless_login(user: str, pwd: Optional[str]) -> Dict[str, Any]:
    """
    Robust login that:
      1) Tries cookie-based login if provided
      2) Handles iframe-based sign-in form
      3) Falls back to top-level inputs
      4) Captures screenshot/HTML on failure
    Returns Playwright storage_state dict.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = browser.new_context(
            locale="en-US",
            timezone_id=TIMEZONE,
            viewport={"width": 1366, "height": 900},
            user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"),
        )

        # 1) Try cookies first (if provided)
        if _try_cookie_login(ctx):
            state = ctx.storage_state()
            browser.close()
            return state

        # 2) Form-based login
        page = ctx.new_page()
        try:
            page.goto("https://www.tradingview.com/accounts/signin/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)

            # Try iframe first
            iframe = page.frame_locator("iframe[src*='signin'], iframe[title*='Sign in']").first
            used_iframe = False
            try:
                # placeholder strategy
                iframe.get_by_placeholder(re.compile("Email|Correo", re.I)).fill(user, timeout=15000)
                if pwd:
                    iframe.get_by_placeholder(re.compile("Password|Contraseña", re.I)).fill(pwd, timeout=15000)
                iframe.get_by_role("button", name=re.compile("Sign in|Iniciar", re.I)).click(timeout=15000)
                used_iframe = True
            except PWTimeout:
                # try CSS in iframe (some variants don't use placeholder)
                try:
                    iframe.locator("input[name='username'], input[type='email']").first.fill(user, timeout=15000)
                    if pwd:
                        iframe.locator("input[name='password']").first.fill(pwd, timeout=15000)
                    iframe.locator("button:has-text('Sign in'), button:has-text('Iniciar')").first.click(timeout=15000)
                    used_iframe = True
                except PWTimeout:
                    used_iframe = False

            # If iframe didn't take, use top-level
            if not used_iframe:
                try:
                    page.get_by_placeholder(re.compile("Email|Correo", re.I)).fill(user, timeout=15000)
                    if pwd:
                        page.get_by_placeholder(re.compile("Password|Contraseña", re.I)).fill(pwd, timeout=15000)
                    page.get_by_role("button", name=re.compile("Sign in|Iniciar", re.I)).click(timeout=15000)
                except PWTimeout:
                    # Final fallback: CSS selectors
                    page.locator("input[name='username'], input[type='email']").first.fill(user, timeout=15000)
                    if pwd:
                        page.locator("input[name='password']").first.fill(pwd, timeout=15000)
                    page.locator("button:has-text('Sign in'), button:has-text('Iniciar')").first.click(timeout=15000)

            # Wait to land anywhere *except* the signin page
            page.wait_for_url(re.compile(r"tradingview\.com/(?!accounts/signin)"), timeout=120000)
            state = ctx.storage_state()
            browser.close()
            return state

        except Exception as e:
            log(f"Login error: {e}")
            _save_debug(page)
            browser.close()
            raise


# ------------ CLI / Main ------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TV Guard")
    parser.add_argument("--region", default="US", help="Region code (default US)")
    # Keep compatibility with your call: --list candidates
    parser.add_argument("--list", choices=["candidates"], help="List entities (currently supports: candidates)")
    # Optional: include/exclude personal symbols via flag
    parser.add_argument("--include-personal", action="store_true", help="Include personal symbols=1")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 1) Get symbols (with fallbacks)
    base_syms = get_symbols_list(personal=False)
    all_syms = list(base_syms)
    if args.include_personal:
        personal_syms = get_symbols_list(personal=True)
        # de-duplicate, keep order
        seen = set(all_syms)
        for s in personal_syms:
            if s not in seen:
                all_syms.append(s)
                seen.add(s)

    # 2) Headless login (only if we actually need TradingView)
    log("Headless login…")
    try:
        if not TV_USER and not TV_COOKIES_JSON_B64:
            log("No TV_USER (email) and no TV_COOKIES_JSON_B64 provided; continuing without login.")
        else:
            do_headless_login(TV_USER, TV_PWD)
    except Exception as e:
        # We won't crash the entire cron if login fails; we already saved debug.
        log(f"Continuing without authenticated session due to login error: {e}")

    # 3) Output for requested action
    if args.list == "candidates":
        # For now, candidates = symbols we have (your upstream logic can refine later)
        safe_json_print({
            "region": args.region,
            "candidates": all_syms,
            "count": len(all_syms),
        })
        return

    # If no action provided:
    log("No --list action provided. Nothing to do.")
    safe_json_print({
        "message": "No action specified. Try: --list candidates",
        "region": args.region,
        "example": "python scripts/agent_tv_guard.py --region US --list candidates --include-personal",
    })


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as ex:
        log(f"Fatal error: {ex}")
        sys.exit(1)

# Robust broadcaster with exponential retry + de-dupe cache.

from __future__ import annotations
import os, json, time, hashlib, pathlib, smtplib, ssl, socket
from typing import Optional
from email.mime.text import MIMEText
from urllib import request as urlreq

# ========= Config via ENV =========
STATE_DIR = pathlib.Path(os.getenv("WATCH_STATE_DIR", ".vega_state"))
STATE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = STATE_DIR / "mail_cache.json"

MAIL_DEDUPE_MIN   = int(os.getenv("MAIL_DEDUPE_MIN", "10"))   # minutes to suppress duplicates
MAIL_MAX_RETRIES  = int(os.getenv("MAIL_MAX_RETRIES", "3"))    # exponential retries
MAIL_RETRY_BASE_S = float(os.getenv("MAIL_RETRY_BASE_S", "1"))

# SMTP (optional if using WEBHOOK only)
EMAIL_TO    = os.getenv("EMAIL_TO")
EMAIL_FROM  = os.getenv("EMAIL_FROM")
SMTP_HOST   = os.getenv("SMTP_HOST")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
SMTP_USER   = os.getenv("SMTP_USER")
SMTP_PASS   = os.getenv("SMTP_PASS")

# Webhook (optional)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# ========= De-dupe helpers =========
def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            pass
    return {}

def _save_cache(cache: dict) -> None:
    try:
        CACHE_FILE.write_text(json.dumps(cache))
    except Exception:
        pass

def _msg_fingerprint(subject: str, body: str) -> str:
    h = hashlib.sha256()
    h.update(subject.encode("utf-8", errors="ignore"))
    h.update(b"\x00")
    h.update(body.encode("utf-8", errors="ignore"))
    return h.hexdigest()

def _is_duplicate(fingerprint: str, cache: dict, window_sec: int) -> bool:
    ts = int(time.time())
    last = cache.get(fingerprint, 0)
    if last and (ts - last) < window_sec:
        return True
    cache[fingerprint] = ts
    _save_cache(cache)
    return False

# ========= Senders =========
def _send_smtp(subject: str, body: str) -> None:
    if not (EMAIL_TO and EMAIL_FROM and SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASS):
        print("[broadcast] SMTP not configured; skipping SMTP send.")
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        s.ehlo()
        try:
            s.starttls(context=context)
        except smtplib.SMTPException:
            pass
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())

def _send_webhook(subject: str, body: str) -> None:
    if not WEBHOOK_URL:
        return
    payload = json.dumps({"subject": subject, "body": body}).encode("utf-8")
    req = urlreq.Request(WEBHOOK_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urlreq.urlopen(req, timeout=20) as resp:
        _ = resp.read()

# ========= Public API =========
def broadcast(subject: str, body: str) -> None:
    """
    Sends via SMTP (if configured) and Webhook (if configured).
    - De-dupes identical messages within MAIL_DEDUPE_MIN (default 10 minutes).
    - Retries each channel up to MAIL_MAX_RETRIES with exponential backoff.
    """
    dedupe_window_sec = MAIL_DEDUPE_MIN * 60
    fp = _msg_fingerprint(subject, body)
    cache = _load_cache()
    if _is_duplicate(fp, cache, dedupe_window_sec):
        print("[broadcast] duplicate suppressed within window")
        return

    def _with_retries(fn, label: str):
        delay = MAIL_RETRY_BASE_S
        for attempt in range(1, MAIL_MAX_RETRIES + 1):
            try:
                fn()
                if attempt > 1:
                    print(f"[broadcast] {label} succeeded on retry {attempt}")
                return
            except (smtplib.SMTPException, ConnectionError, TimeoutError, socket.timeout, OSError) as e:
                if attempt == MAIL_MAX_RETRIES:
                    print(f"[broadcast] {label} FAILED after {attempt} tries: {e}")
                    return
                print(f"[broadcast] {label} error (attempt {attempt}): {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                delay *= 2

    _with_retries(lambda: _send_smtp(subject, body), "SMTP")
    _with_retries(lambda: _send_webhook(subject, body), "WEBHOOK")

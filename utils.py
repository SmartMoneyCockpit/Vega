\
import os, datetime as dt, pytz, requests, yfinance as yf

PT = pytz.timezone(os.getenv("TZ_PREF","America/Los_Angeles"))

def now_pt():
    return dt.datetime.now(PT)

def in_us_window(ts=None):
    """US trading window 06:00–14:00 PT Mon–Fri"""
    ts = ts or now_pt()
    return ts.weekday() <= 4 and 6 <= ts.hour < 14

def in_apac_window(ts=None):
    """APAC window 18:00–22:00 PT daily"""
    ts = ts or now_pt()
    return 18 <= ts.hour < 22

def last_price(ticker):
    df = yf.download(ticker, period="1d", interval="1m", progress=False, auto_adjust=False)
    if df.empty: return None
    return float(df["Close"].dropna().iloc[-1])

def prev_close(ticker):
    df = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
    if df.empty or len(df["Close"]) < 2: return None
    return float(df["Close"].iloc[-2])

def pct_from_prev_close(ticker):
    p0 = prev_close(ticker); p = last_price(ticker)
    if p0 is None or p is None: return None
    return (p/p0 - 1.0) * 100.0

def fmt_num(x, n=2):
    return "n/a" if x is None else f"{x:.{n}f}"

def fetch_gist(gist_id, token):
    try:
        r = requests.get(f"https://api.github.com/gists/{gist_id}", headers={"Authorization": f"token {token}"} ,timeout=10)
        if r.status_code != 200: return None
        data = r.json()
        files = data.get("files",{})
        if "alerts_log.txt" in files and "content" in files["alerts_log.txt"]:
            return files["alerts_log.txt"]["content"]
    except Exception:
        return None
    return None

def append_gist(gist_id, token, line):
    try:
        existing = fetch_gist(gist_id, token) or ""
        new_content = (existing + ("\n" if existing else "") + line)
        payload = {"files": {"alerts_log.txt": {"content": new_content}}}
        r = requests.patch(f"https://api.github.com/gists/{gist_id}", headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }, json=payload, timeout=10)
        return r.status_code in (200,201)
    except Exception:
        return False

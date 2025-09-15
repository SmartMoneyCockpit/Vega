import os, time, requests

class Polygon:
    def __init__(self, api_key: str, base="https://api.polygon.io"):
        self.key = api_key
        self.base = base
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {self.key}"})

    def _get(self, path, params=None, retries=3, backoff=1.0):
        url = f"{self.base}{path}"
        for i in range(retries):
            r = self.s.get(url, params=params, timeout=20)
            if r.ok:
                return r.json()
            time.sleep(backoff * (2**i))
        r.raise_for_status()

    def aggregates_day(self, ticker, limit=60):
        # last 60 daily bars (enough for EMA/ATR/RS)
        return self._get(f"/v2/aggs/ticker/{ticker}/range/1/day/1970-01-01/2100-01-01",
                         params={"limit": limit, "adjusted": "true"})["results"]

    def avg_volume_30d(self, ticker):
        bars = self.aggregates_day(ticker, 35)
        vols = [b["v"] for b in bars[-30:]]
        return sum(vols)/len(vols) if vols else 0

    def upcoming_earnings(self, ticker):
        # polygon vX routes vary; this one is commonly available:
        j = self._get(f"/vX/reference/financials?ticker={ticker}&type=earnings")  # fallback if your plan differs
        # if your plan lacks this endpoint, we fail "safe": return None and pass via calendar you keep in repo
        return j if j else None

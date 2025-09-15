import requests, time

class SectorResolver:
    def __init__(self):
        self._cache = {}

    def sector(self, ticker: str) -> str | None:
        t = ticker.upper()
        if t in self._cache:
            return self._cache[t]
        try:
            # Unofficial JSON: fast & small; acceptable for CI usage
            r = requests.get(f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{t}?modules=assetProfile", timeout=10)
            if r.ok:
                j = r.json()
                sector = j["quoteSummary"]["result"][0]["assetProfile"].get("sector")
                self._cache[t] = sector
                # small backoff to be polite
                time.sleep(0.2)
                return sector
        except Exception:
            pass
        self._cache[t] = None
        return None

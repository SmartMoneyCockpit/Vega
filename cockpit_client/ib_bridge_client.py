
import os, requests

class IBKRBridgeClient:
    def __init__(self, base_url=None, api_key=None, timeout=10):
        self.base = (base_url or os.getenv("IBKR_BRIDGE_URL") or "http://127.0.0.1:8088").rstrip("/")
        self.key  = api_key or os.getenv("BRIDGE_API_KEY") or ""
        self.timeout = timeout

    def _h(self):
        return {"x-api-key": self.key} if self.key else {}

    def health(self):
        r = requests.get(f"{self.base}/health", timeout=5)
        r.raise_for_status()
        return r.json()

    def price(self, symbol: str):
        r = requests.get(f"{self.base}/price/{symbol}", headers=self._h(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def market_order(self, symbol: str, action: str, qty: int):
        payload = {"symbol": symbol, "action": action, "quantity": int(qty)}
        r = requests.post(f"{self.base}/order/market", json=payload, headers=self._h(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

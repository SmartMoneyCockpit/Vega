
import os, requests
from config.ib_bridge_client import get_bridge_url, default_headers

class IBKRBridgeClient:
    def __init__(self, base_url: str | None = None, timeout: float = 8.0):
        self.base = (base_url or get_bridge_url()).rstrip("/")
        self.timeout = timeout

    def health(self):
        r = requests.get(f"{self.base}/health", headers=default_headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def price(self, symbol: str):
        r = requests.get(f"{self.base}/quote?symbol={symbol}", headers=default_headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def market_order(self, symbol: str, action: str, qty: int):
        payload = {"symbol": symbol, "action": action, "quantity": int(qty)}
        r = requests.post(f"{self.base}/order/market", json=payload, headers=default_headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

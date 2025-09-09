from dataclasses import dataclass
from typing import List, Dict, Optional
import os

@dataclass
class TickerQuote:
    symbol: str
    last: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    time: Optional[str] = None  # ISO

class IBKRClient:
    def __init__(self, host: str = None, port: int = None, client_id: int = 1):
        self.host = host or os.getenv("IBKR_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("IBKR_PORT", "7497"))
        self.client_id = client_id
    def connect(self) -> bool:
        return True
    def get_quotes(self, symbols: List[str]) -> Dict[str, TickerQuote]:
        return {s: TickerQuote(symbol=s) for s in symbols}

def get_client() -> IBKRClient:
    return IBKRClient()

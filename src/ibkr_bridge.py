# src/ibkr_bridge.py
import os
import time
from typing import Dict, Iterable, Optional
from ib_insync import IB, Stock, Contract, util

def _env_or_cfg(cfg, key, default=None):
    env_map = {
        "host": "IB_HOST",
        "port": "IB_PORT",
        "client_id": "IB_CLIENT_ID",
        "market_data_type": "IB_MKT_TYPE",
        "connect_timeout_sec": "IB_CONNECT_TIMEOUT",
    }
    if key in env_map and os.getenv(env_map[key]):
        val = os.getenv(env_map[key])
        if key in ("port","client_id","market_data_type","connect_timeout_sec"):
            try:
                return int(val)
            except Exception:
                return default if default is not None else cfg["ibkr"].get(key, default)
        return val
    return cfg["ibkr"].get(key, default)

def connect_ib(cfg) -> IB:
    """Connect to IBKR using config/env settings and set market data type.
    Market data: 1=live, 2=frozen, 3=delayed (free), 4=delayed frozen.
    """
    ib = IB()
    host = _env_or_cfg(cfg, "host", "127.0.0.1")
    port = _env_or_cfg(cfg, "port", 4002)
    client_id = _env_or_cfg(cfg, "client_id", 7)
    timeout = _env_or_cfg(cfg, "connect_timeout_sec", 8)
    ib.connect(host, int(port), clientId=int(client_id), timeout=int(timeout))

    mkt_type = _env_or_cfg(cfg, "market_data_type", 3)
    ib.reqMarketDataType(int(mkt_type))
    return ib

# Basic suffix mapping; extend via config if needed
_SUFFIX_MAP = {
    ".TO": {"currency": "CAD", "primaryExchange": "TSE"},  # Toronto
    # Add more here later if desired (LSE/HKEX/ASX, etc.).
}

def to_ib_contract(ticker: str) -> Contract:
    for suffix, params in _SUFFIX_MAP.items():
        if ticker.endswith(suffix):
            sym = ticker[: -len(suffix)]
            return Stock(sym, "SMART", params["currency"], primaryExchange=params["primaryExchange"])
    # default US
    return Stock(ticker, "SMART", "USD")

def get_delayed_last(ib: IB, ticker: str, wait: float = 1.5) -> Optional[float]:
    """Request (delayed) market data and return best available price."""
    c = to_ib_contract(ticker)
    t = ib.reqMktData(c, "", False, False)
    time.sleep(wait)
    price = t.last or t.close or t.marketPrice()
    try:
        ib.cancelMktData(c)
    except Exception:
        pass
    return float(price) if price is not None else None

def fetch_prices(ib: IB, tickers: Iterable[str], wait: float = 1.5) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {}
    for tk in tickers:
        out[tk] = get_delayed_last(ib, tk, wait=wait)
    return out

# src/ibkr_bridge.py
import os
import time
from typing import Dict, Iterable, Optional
from ib_insync import IB, Stock, Contract

def _read_env(cfg, key, default=None):
    # Accept both IB_* and IBKR_* prefixes; allow a single URL to override host/port.
    map_primary = {
        "host": ["IB_HOST", "IBKR_HOST"],
        "port": ["IB_PORT", "IBKR_PORT"],
        "client_id": ["IB_CLIENT_ID", "IBKR_CLIENT_ID"],
        "market_data_type": ["IB_MKT_TYPE", "IBKR_MARKET_DATA_TYPE"],
        "connect_timeout_sec": ["IB_CONNECT_TIMEOUT", "IBKR_CONNECT_TIMEOUT"],
        "bridge_url": ["IB_BRIDGE_URL", "IBKR_BRIDGE_URL"],
    }
    # URL override (e.g., http://167.71.145.48:4002)
    url = None
    for env_name in map_primary.get("bridge_url", []):
        if os.getenv(env_name):
            url = os.getenv(env_name)
            break
    host_from_url = port_from_url = None
    if url and "://" in url:
        try:
            addr = url.split("://",1)[1]
            host_from_url, maybe_port = (addr.split(":",1)+[""])[:2]
            port_from_url = int(maybe_port) if maybe_port else None
        except Exception:
            pass

    # Host/port/clientId
    if key == "host" and host_from_url:
        return host_from_url
    if key == "port" and port_from_url:
        return port_from_url

    for env_name in map_primary.get(key, []):
        val = os.getenv(env_name)
        if val is not None and val != "":
            if key in ("port","client_id","market_data_type","connect_timeout_sec"):
                try:
                    return int(val)
                except Exception:
                    continue
            return val
    return cfg.get("ibkr", {}).get(key, default)

def connect_ib(cfg) -> IB:
    ib = IB()
    host = _read_env(cfg, "host", "127.0.0.1")
    port = _read_env(cfg, "port", 4002)  # Gateway default
    client_id = _read_env(cfg, "client_id", 7)
    timeout = _read_env(cfg, "connect_timeout_sec", 8)
    ib.connect(host, int(port), clientId=int(client_id), timeout=int(timeout))
    mkt_type = _read_env(cfg, "market_data_type", 3)  # 3 = delayed (free)
    ib.reqMarketDataType(int(mkt_type))
    return ib

_SUFFIX_MAP = {
    ".TO": {"currency": "CAD", "primaryExchange": "TSE"},  # Toronto
    # Extend as needed: ".L": {"currency": "GBP","primaryExchange":"LSE"}, etc.
}

def to_ib_contract(ticker: str) -> Contract:
    for suffix, params in _SUFFIX_MAP.items():
        if ticker.endswith(suffix):
            sym = ticker[: -len(suffix)]
            return Stock(sym, "SMART", params["currency"], primaryExchange=params["primaryExchange"])
    return Stock(ticker, "SMART", "USD")

def get_delayed_last(ib: IB, ticker: str, wait: float = 1.5) -> Optional[float]:
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

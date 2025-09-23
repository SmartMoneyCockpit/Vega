
# src/ibkr_bridge.py
import os, time
from typing import Dict, Iterable, Optional
from ib_insync import IB, Stock, Contract

def _read_env(key, default=None):
    envs = {
        "host": ["IB_HOST","IBKR_HOST"],
        "port": ["IB_PORT","IBKR_PORT"],
        "client_id": ["IB_CLIENT_ID","IBKR_CLIENT_ID"],
        "market_data_type": ["IB_MKT_TYPE","IBKR_MARKET_DATA_TYPE"],
        "connect_timeout_sec": ["IB_CONNECT_TIMEOUT","IBKR_CONNECT_TIMEOUT"],
        "bridge_url": ["IB_BRIDGE_URL","IBKR_BRIDGE_URL"],
    }
    url = next((os.getenv(e) for e in envs["bridge_url"] if os.getenv(e)), None)
    if url and "://" in url:
        try:
            addr = url.split("://",1)[1]
            host, port = (addr.split(":",1)+[""])[:2]
            if key == "host" and host: return host
            if key == "port" and port: return int(port)
        except Exception:
            pass
    for e in envs.get(key, []):
        v = os.getenv(e)
        if v not in (None, ""):
            if key in ("port","client_id","market_data_type","connect_timeout_sec"):
                try: return int(v)
                except Exception: continue
            return v
    defaults = {"host":"127.0.0.1","port":4002,"client_id":7,"market_data_type":3,"connect_timeout_sec":8}
    return defaults.get(key, default)

def connect_ib() -> IB:
    ib = IB()
    host = _read_env("host", "127.0.0.1")
    port = int(_read_env("port", 4002))
    client_id = int(_read_env("client_id", 7))
    timeout = int(_read_env("connect_timeout_sec", 8))
    ib.connect(host, port, clientId=client_id, timeout=timeout)
    ib.reqMarketDataType(int(_read_env("market_data_type", 3)))
    return ib

_SUFFIX_MAP = {
    ".TO": {"currency": "CAD", "primaryExchange": "TSE"},
    ".L":  {"currency": "GBP"},
    ".PA": {"currency": "EUR"},
    ".F":  {"currency": "EUR"},
    ".MI": {"currency": "EUR"},
    ".SW": {"currency": "CHF"},
    ".HK": {"currency": "HKD"},
    ".AX": {"currency": "AUD"},
    ".T":  {"currency": "JPY"},
    ".KS": {"currency": "KRW"},
    ".TW": {"currency": "TWD"},
    ".SI": {"currency": "SGD"},
    ".SS": {"currency": "CNY"},
    ".SZ": {"currency": "CNY"},
}

def to_ib_contract(ticker: str) -> Contract:
    for suffix, params in _SUFFIX_MAP.items():
        if ticker.endswith(suffix):
            sym = ticker[: -len(suffix)]
            if "primaryExchange" in params:
                return Stock(sym, "SMART", params["currency"], primaryExchange=params["primaryExchange"])
            return Stock(sym, "SMART", params["currency"])
    return Stock(ticker, "SMART", "USD")

def get_delayed_last(ib: IB, ticker: str, wait: float = 1.5) -> Optional[float]:
    c = to_ib_contract(ticker)
    t = ib.reqMktData(c, "", False, False)
    time.sleep(wait)
    price = t.last or t.close or t.marketPrice()
    try: ib.cancelMktData(c)
    except Exception: pass
    return float(price) if price is not None else None

def fetch_prices(ib: IB, tickers: Iterable[str], wait: float = 1.5) -> Dict[str, Optional[float]]:
    return {tk: get_delayed_last(ib, tk, wait=wait) for tk in tickers}

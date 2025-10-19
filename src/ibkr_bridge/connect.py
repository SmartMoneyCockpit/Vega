# src/ibkr_bridge/health.py
from ib_insync import IB
from ibkr_bridge.async_utils import run

def connect(host: str = "127.0.0.1", port: int = 4002, client_id: int = 16) -> IB:
    ib = IB()
    run(ib.connectAsync(host, int(port), clientId=int(client_id)))
    return ib

def disconnect(ib: IB) -> None:
    try:
        ib.disconnect()
    except Exception:
        pass

# tools/ibkr_client.py
import os, threading, asyncio
import nest_asyncio
nest_asyncio.apply()

IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", "7497"))   # TWS(7497) / Gateway(4002)
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "7"))

try:
    from ib_insync import IB, util
except Exception:
    IB = None
    util = None

_ib = None
_lock = threading.Lock()

def _ensure_loop():
    try:
        asyncio.get_running_loop()
        return
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

def get_ib():
    global _ib
    if IB is None:
        return None
    with _lock:
        if _ib and _ib.isConnected():
            return _ib
        _ensure_loop()
        try:
            if _ib is None:
                _ib = IB()
            if not _ib.isConnected():
                util.run(_ib.connectAsync(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID, timeout=5.0))
            return _ib if _ib.isConnected() else None
        except Exception:
            return None

def status():
    ib = _ib
    return {
        "enabled": bool(IB),
        "connected": bool(ib and ib.isConnected()),
        "host": IB_HOST,
        "port": IB_PORT,
        "clientId": IB_CLIENT_ID,
    }
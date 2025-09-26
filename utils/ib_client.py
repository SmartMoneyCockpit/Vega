
# utils/ib_client.py
import os, time
from ib_insync import IB

IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", "7496"))
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "1"))

def connect_with_retry(max_ids=5, backoff_sec=1.0):
    ib = IB()
    tried_ids = []
    ids = [IB_CLIENT_ID] + [i for i in range(1, max_ids+1) if i != IB_CLIENT_ID]
    last_err = None
    for cid in ids:
        try:
            ib.connect(IB_HOST, IB_PORT, clientId=cid, timeout=5)
            if ib.isConnected():
                return ib, cid
        except Exception as e:
            last_err = e
            tried_ids.append(cid)
            time.sleep(backoff_sec)
    raise RuntimeError(f"Failed to connect to IB at {IB_HOST}:{IB_PORT}. Tried client IDs {tried_ids}. Last error: {last_err}")

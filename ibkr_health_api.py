
import os
from fastapi import FastAPI
from ib_insync import IB

app = FastAPI()
IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", "7496"))
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "1"))

@app.get("/health")
def health():
    ib = IB()
    try:
        ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID, timeout=5)
        if ib.isConnected():
            return {"status": "connected", "host": IB_HOST, "port": IB_PORT, "clientId": IB_CLIENT_ID}
        return {"status": "disconnected"}
    except Exception as e:
        return {"status": "error", "message": str(e), "host": IB_HOST, "port": IB_PORT, "clientId": IB_CLIENT_ID}
    finally:
        if ib.isConnected():
            ib.disconnect()

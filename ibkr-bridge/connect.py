# ibkr_bridge/connect.py
from fastapi import FastAPI
from pydantic import BaseModel
import os, socket

app = FastAPI(title="IBKR Bridge", version="1.0")

def _ib_socket_ok(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

@app.get("/health")
def health():
    host = os.getenv("IB_HOST", "127.0.0.1")
    port = int(os.getenv("IB_PORT", "7496"))
    ok = _ib_socket_ok(host, port)
    return {"ok": ok, "host": host, "port": port}

# (Optional) simple echo endpoint to test headers/API key if you add one later
@app.get("/ping")
def ping():
    return {"pong": True}

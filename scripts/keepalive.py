
# scripts/keepalive.py
import os, socket, sys

host = os.getenv("IB_HOST", "127.0.0.1")
port = int(os.getenv("IB_PORT", "7496"))

try:
    s = socket.create_connection((host, port), timeout=5)
    s.close()
    print(f"Keepalive OK: {host}:{port}")
    sys.exit(0)
except Exception as e:
    print(f"Keepalive FAIL: {host}:{port} -> {e}")
    sys.exit(1)

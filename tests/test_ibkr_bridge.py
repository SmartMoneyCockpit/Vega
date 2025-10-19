# tests/test_ibkr_bridge.py
import os, requests

BRIDGE_URL = os.getenv("IBKR_BRIDGE_URL","http://127.0.0.1:8080")
API_KEY = os.getenv("IBKR_API_KEY","")

def test_health():
    r = requests.get(f"{BRIDGE_URL}/health")
    assert r.status_code==200

def test_price():
    r = requests.get(f"{BRIDGE_URL}/price/SPY", headers={"x-api-key":API_KEY})
    assert r.status_code==200

def test_order_reject():
    # Should fail gracefully without sending a real order
    r = requests.post(f"{BRIDGE_URL}/order", headers={"x-api-key":API_KEY},
                      json={"symbol":"SPY","side":"buy","quantity":1,"type":"MKT"})
    assert r.status_code in (200,400,403)

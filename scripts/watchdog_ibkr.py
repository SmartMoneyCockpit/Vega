# scripts/watchdog_ibkr.py
"""IBKR API watchdog.
Pings reqCurrentTime() every WATCHDOG_INTERVAL_SEC (default 600s).
After WATCHDOG_FAIL_THRESHOLD consecutive failures (default 3), restarts ibgateway.
"""
import os, time, sys, subprocess
from datetime import datetime
from ib_insync import IB

def env_int(name, default):
    try: return int(os.getenv(name, default))
    except: return default

def get_host(): return os.getenv("IBKR_HOST") or os.getenv("IB_HOST") or "127.0.0.1"
def get_port(): return env_int("IBKR_PORT", env_int("IB_PORT", 4002))
def get_cid():  return env_int("IBKR_CLIENT_ID", env_int("IB_CLIENT_ID", 7))

def restart_gateway():
    svc = os.getenv("IB_GATEWAY_SERVICE", "ibgateway@vega.service")
    print(f"[watchdog] restarting {svc} ...", flush=True)
    subprocess.run(["sudo","systemctl","restart", svc], check=False)

def main():
    interval = env_int("WATCHDOG_INTERVAL_SEC", 600)   # 10 minutes default
    threshold = env_int("WATCHDOG_FAIL_THRESHOLD", 3)
    host, port, cid = get_host(), get_port(), get_cid()
    print(f"[watchdog] host={host} port={port} cid={cid} interval={interval}s threshold={threshold}", flush=True)
    fails = 0
    while True:
        try:
            ib = IB(); ib.connect(host, port, clientId=cid, timeout=20)
            srv_time = ib.reqCurrentTime(); ib.disconnect()
            print(f"[watchdog] {datetime.now().isoformat()} OK - {srv_time}", flush=True)
            fails = 0
        except Exception as e:
            fails += 1
            print(f"[watchdog] {datetime.now().isoformat()} FAIL {fails}/{threshold}: {e}", flush=True)
            if fails >= threshold:
                restart_gateway(); fails = 0
        time.sleep(interval)

if __name__ == "__main__":
    main()


# scripts/watchdog_ibkr.py
"""Pings IBKR via ib_insync.reqCurrentTime() every N seconds.
If it fails X times in a row, restarts ibgateway via systemd.
Usage:
  IB_HOST=167.71.145.48 IB_PORT=4002 IB_CLIENT_ID=7 python scripts/watchdog_ibkr.py
Or rely on config.yaml and IBKR_* envs; both are supported if your bridge has env-compat.
"""
import os, time, sys, subprocess
from datetime import datetime
from ruamel.yaml import YAML
from pathlib import Path

try:
    from ib_insync import IB
except Exception as e:
    print(f"[watchdog] ERROR: ib_insync not available: {e}", flush=True)
    sys.exit(1)

yaml = YAML()
cfg_path = Path("config.yaml")
cfg = yaml.load(cfg_path.read_text()) if cfg_path.exists() else {"ibkr": {}}

def get(key, default=None):
    alias = {
        "host": ["IB_HOST","IBKR_HOST"],
        "port": ["IB_PORT","IBKR_PORT"],
        "client_id": ["IB_CLIENT_ID","IBKR_CLIENT_ID"],
        "timeout": ["IB_CONNECT_TIMEOUT","IBKR_CONNECT_TIMEOUT"],
        "url": ["IB_BRIDGE_URL","IBKR_BRIDGE_URL"],
    }
    url = next((os.getenv(k) for k in alias["url"] if os.getenv(k)), None)
    if url and "://" in url:
        try:
            addr = url.split("://",1)[1]
            h, p = (addr.split(":",1)+[""])[:2]
            if key == "host" and h: return h
            if key == "port" and p: return int(p)
        except Exception:
            pass
    for env in alias.get(key, []):
        if os.getenv(env):
            v = os.getenv(env)
            if key in ("port","client_id","timeout"):
                try: return int(v)
                except: continue
            return v
    if key == "host": return cfg.get("ibkr",{}).get("host", "127.0.0.1")
    if key == "port": return int(cfg.get("ibkr",{}).get("port", 4002))
    if key == "client_id": return int(cfg.get("ibkr",{}).get("client_id", 7))
    if key == "timeout": return int(cfg.get("ibkr",{}).get("connect_timeout_sec", 8))
    return default

def restart_gateway():
    svc = os.getenv("IB_GATEWAY_SERVICE", "ibgateway@vega.service")
    print(f"[watchdog] restarting {svc} ...", flush=True)
    try:
        subprocess.run(["sudo","systemctl","restart", svc], check=True)
    except Exception as e:
        print(f"[watchdog] ERROR restarting {svc}: {e}", flush=True)

def main():
    host = get("host")
    port = get("port")
    client_id = get("client_id")
    timeout = get("timeout")
    interval = int(os.getenv("WATCHDOG_INTERVAL_SEC", "60"))
    threshold = int(os.getenv("WATCHDOG_FAIL_THRESHOLD", "3"))

    print(f"[watchdog] start host={host} port={port} client_id={client_id} interval={interval}s threshold={threshold}", flush=True)

    consecutive = 0
    while True:
        try:
            ib = IB()
            ib.connect(host, port, clientId=client_id, timeout=timeout)
            srv_time = ib.reqCurrentTime()
            ib.disconnect()
            print(f"[watchdog] {datetime.now().isoformat()} OK - server time: {srv_time}", flush=True)
            consecutive = 0
        except Exception as e:
            consecutive += 1
            print(f"[watchdog] {datetime.now().isoformat()} FAIL {consecutive}/{threshold}: {e}", flush=True)
            if consecutive >= threshold:
                restart_gateway()
                consecutive = 0
        time.sleep(interval)

if __name__ == "__main__":
    main()

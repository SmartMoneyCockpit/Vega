# vega_monitor/sensors.py
import psutil, time, shutil
from dataclasses import dataclass

@dataclass
class SystemMetrics:
    cpu: float      # 0..1
    mem: float      # 0..1
    disk: float     # 0..1
    net_tx: float   # bytes/sec
    net_rx: float   # bytes/sec
    ts: float       # epoch seconds

# keep a rolling baseline for network deltas
_prev = psutil.net_io_counters()
_ts   = time.time()

def read_system_metrics() -> SystemMetrics:
    global _prev, _ts

    # short, non-blocking sample; returns last known + quick refresh
    cpu = psutil.cpu_percent(interval=0.05) / 100.0
    mem = psutil.virtual_memory().percent / 100.0

    du = shutil.disk_usage("/")
    disk = du.used / du.total if du.total else 0.0

    now = time.time()
    cur = psutil.net_io_counters()
    dt  = max(now - _ts, 1e-6)
    tx  = (cur.bytes_sent - _prev.bytes_sent) / dt
    rx  = (cur.bytes_recv - _prev.bytes_recv) / dt

    _prev, _ts = cur, now
    return SystemMetrics(cpu, mem, disk, tx, rx, now)

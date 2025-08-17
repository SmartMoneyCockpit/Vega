import psutil, time, shutil
from dataclasses import dataclass

@dataclass
class SystemMetrics:
    cpu: float; mem: float; disk: float; net_tx: float; net_rx: float

_prev = psutil.net_io_counters(); _ts = time.time()

def read_system_metrics() -> SystemMetrics:
    global _prev, _ts
    cpu = psutil.cpu_percent(interval=0.2)/100.0
    mem = psutil.virtual_memory().percent/100.0
    du = shutil.disk_usage('/')
    disk = du.used/du.total
    now = time.time(); cur = psutil.net_io_counters(); dt = max(now-_ts,1e-6)
    tx = (cur.bytes_sent - _prev.bytes_sent)/dt; rx = (cur.bytes_recv - _prev.bytes_recv)/dt
    _prev, _ts = cur, now
    return SystemMetrics(cpu, mem, disk, tx, rx)

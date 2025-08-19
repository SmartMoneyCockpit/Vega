# vega_monitor/service.py
import os, json, time, threading
from pathlib import Path
from .sensors import read_system_metrics
from .policy  import HealthPolicy
from .alerts  import send_webhook, send_email

HEALTH_DIR   = Path("data/health")
SNAP_PATH    = HEALTH_DIR / "snapshots.jsonl"
STATE_PATH   = HEALTH_DIR / "state.json"

def _ensure_dirs():
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)

class MonitorService:
    def __init__(self):
        self.policy = HealthPolicy(
            warn=float(os.getenv("VEGA_THRESH_WARN", "0.75")),
            action=float(os.getenv("VEGA_THRESH_ACTION", "0.80")),
            critical=float(os.getenv("VEGA_THRESH_CRITICAL", "0.90")),
        )
        self.defensive = False
        self._last_alert = 0.0  # throttle

    def _persist(self, snapshot: dict, state: dict):
        _ensure_dirs()
        # append snapshot
        with SNAP_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(snapshot, separators=(",", ":")) + "\n")
        # write state
        STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def step(self):
        m = read_system_metrics()
        levels = {
            "cpu":  self.policy.level(m.cpu),
            "mem":  self.policy.level(m.mem),
            "disk": self.policy.level(m.disk),
        }
        critical = any(v == "critical" for v in levels.values())
        actions  = sum(1 for v in levels.values() if v == "action")

        # snapshot
        snapshot = {
            "ts": m.ts,
            "cpu": m.cpu, "mem": m.mem, "disk": m.disk,
            "net_tx": m.net_tx, "net_rx": m.net_rx,
            "levels": levels,
        }

        # defensive logic (enter if >=2 action OR any critical)
        entered = False
        exited  = False
        if critical or actions >= 2:
            if not self.defensive:
                self.defensive = True
                entered = True
        else:
            if self.defensive:
                self.defensive = False
                exited = True

        # state
        state = {
            "ts": m.ts,
            "levels": levels,
            "defensive": self.defensive,
            "thresholds": {
                "warn": self.policy.warn,
                "action": self.policy.action,
                "critical": self.policy.critical,
            },
        }
        self._persist(snapshot, state)

        # alerts (throttled to 60s)
        now = time.time()
        if entered and now - self._last_alert > 60:
            msg = f"[VEGA] Defensive Mode ENTER — levels={levels}"
            send_webhook({"type": "defensive_mode_enter", "levels": levels})
            send_email("VEGA Defensive Mode", msg)
            self._last_alert = now
        elif exited and now - self._last_alert > 60:
            msg = f"[VEGA] Defensive Mode EXIT — levels={levels}"
            send_webhook({"type": "defensive_mode_exit", "levels": levels})
            send_email("VEGA Defensive Exit", msg)
            self._last_alert = now

        return levels, self.defensive

    def run_forever(self, interval=5):
        while True:
            try:
                self.step()
            except Exception as e:
                send_webhook({"type": "monitor_error", "error": str(e)})
                send_email("VEGA Monitor Error", str(e))
            time.sleep(interval)

# --- public helper used by app.py ---
_monitor_thread = None

def start_vega_monitor(interval=5):
    """Idempotent starter—safe to call once from app.py."""
    global _monitor_thread
    if _monitor_thread and _monitor_thread.is_alive():
        return _monitor_thread
    _ensure_dirs()
    svc = MonitorService()
    t = threading.Thread(target=svc.run_forever, kwargs={"interval": interval}, daemon=True)
    t.start()
    _monitor_thread = t
    return t

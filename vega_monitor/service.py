import os, time
from .sensors import read_system_metrics
from .policy import HealthPolicy
from .alerts import send_webhook, send_email

class MonitorService:
    def __init__(self):
        self.policy = HealthPolicy(
            warn=float(os.getenv("VEGA_THRESH_WARN","0.75")),
            action=float(os.getenv("VEGA_THRESH_ACTION","0.80")),
            critical=float(os.getenv("VEGA_THRESH_CRITICAL","0.90")),
        )
        self.defensive = False

    def step(self):
        m = read_system_metrics()
        lv = {k:self.policy.level(v) for k,v in {"cpu":m.cpu,"mem":m.mem,"disk":m.disk}.items()}
        critical = any(v=="critical" for v in lv.values())
        actions = sum(1 for v in lv.values() if v=="action")
        if critical or actions>=2:
            if not self.defensive:
                self.defensive=True
                msg=f"[VEGA] Defensive Mode ENTER — {lv}"
                send_webhook({"type":"defensive_mode","levels":lv}); send_email("VEGA Defensive Mode", msg)
        elif all(v in ("ok","warn") for v in lv.values()):
            if self.defensive:
                self.defensive=False
                msg=f"[VEGA] Defensive Mode EXIT — {lv}"
                send_webhook({"type":"defensive_mode_exit","levels":lv}); send_email("VEGA Defensive Exit", msg)
        return m, lv, self.defensive

    def run_forever(self, interval=5):
        while True:
            try:
                self.step()
            except Exception as e:
                send_webhook({"type":"monitor_error","error":str(e)})
            time.sleep(interval)

# vega_monitor/policy.py
class HealthPolicy:
    def __init__(self, warn=0.75, action=0.80, critical=0.90):
        self.warn, self.action, self.critical = warn, action, critical

    def level(self, v: float) -> str:
        if v >= self.critical: return "critical"
        if v >= self.action:   return "action"
        if v >= self.warn:     return "warn"
        return "ok"

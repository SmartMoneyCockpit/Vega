
import yaml, os

def load_polling_policy():
    p = os.path.join("configs","polling.yaml")
    if not os.path.exists(p):
        return {"active_region_only": True, "default_interval_minutes": 60, "boost_mode_interval_minutes": 5, "boost_mode_duration_minutes": 60}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

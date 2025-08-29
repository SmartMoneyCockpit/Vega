import json, os
from dataclasses import asdict
from .engine import Triggers

CFG_JSON = "config/stay_get.json"

def load_triggers() -> Triggers:
    try:
        with open(CFG_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Triggers(**data)
    except Exception:
        return Triggers()

def save_triggers(t: Triggers) -> str:
    os.makedirs("config", exist_ok=True)
    with open(CFG_JSON, "w", encoding="utf-8") as f:
        json.dump(asdict(t), f, indent=2)
    return CFG_JSON

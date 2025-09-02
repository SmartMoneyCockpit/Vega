#!/usr/bin/env python3
from __future__ import annotations
import os, json, pathlib, datetime as dt

DEFAULTS = {
    "spy_get_in": 651.39, "qqq_confirm": 576.32, "spy_risk1": 638.49, "spy_risk2": 632.04,
}

def load_triggers():
    p = pathlib.Path("config/stay_get.json")
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out = DEFAULTS.copy()
            out.update({k: float(v) for k, v in data.items() if k in DEFAULTS})
            return out
        except Exception:
            pass
    return DEFAULTS.copy()

def main():
    t = load_triggers()
    lines = [
        f"[{dt.datetime.utcnow().isoformat()}Z] Hedge Monitor OK",
        f"Triggers: spy_get_in={t['spy_get_in']} qqq_confirm={t['qqq_confirm']} spy_risk1={t['spy_risk1']} spy_risk2={t['spy_risk2']}"
    ]
    out = pathlib.Path("artifacts"); out.mkdir(parents=True, exist_ok=True)
    path = out/"hedge_monitor_status.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()

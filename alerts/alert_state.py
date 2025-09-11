from dataclasses import dataclass, asdict
from pathlib import Path
import json, time

STATE_FILE = Path(".state/alerts_state.json")

@dataclass
class RuleState:
    armed: bool = True
    last_fire_at: float | None = None
    last_state_hash: str | None = None

def _load():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def _save(d):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(d, indent=2))

def get_state(rule_id: str) -> RuleState:
    d = _load().get(rule_id, {})
    return RuleState(**({**RuleState().__dict__, **d}))

def set_state(rule_id: str, st: RuleState):
    d = _load()
    d[rule_id] = asdict(st)
    _save(d)

def fire(rule_id: str, state_hash: str):
    st = get_state(rule_id)
    st.armed = False
    st.last_fire_at = time.time()
    st.last_state_hash = state_hash
    set_state(rule_id, st)

def rearm(rule_id: str):
    st = get_state(rule_id)
    st.armed = True
    set_state(rule_id, st)

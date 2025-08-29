from dataclasses import dataclass

@dataclass
class Triggers:
    spy_get_in: float = 651.39
    qqq_confirm: float = 576.32
    spy_risk1: float = 638.49
    spy_risk2: float = 632.04

@dataclass
class Inputs:
    spy: float | None = None
    qqq: float | None = None
    vix: float | None = None

@dataclass
class Decision:
    regime: str
    details: str

def decide(inp: Inputs, t: Triggers) -> Decision:
    if inp.spy is None or inp.qqq is None:
        return Decision("WAIT", "Waiting for live SPY/QQQ inputs.")
    if inp.spy >= t.spy_get_in and inp.qqq >= t.qqq_confirm:
        return Decision("GET_BACK_IN", "Both SPY and QQQ above close triggers.")
    if inp.spy <= t.spy_risk2:
        return Decision("RISK_OFF", "SPY below -2% line → escalate hedges.")
    if inp.spy <= t.spy_risk1:
        return Decision("WAIT", "SPY below -1% line → arm starter hedges; wait for close.")
    return Decision("WAIT", "No trigger hit; maintain stance until close.")

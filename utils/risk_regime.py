
"""
Determines risk-on/off regime for showing hedges/contras.
You can wire this to your data providers (VIX, AD line, TRIN, put/call, etc.).
Here we provide a simple pluggable interface with sensible defaults.
"""
from typing import Dict

def risk_off_signal(data: Dict) -> bool:
    """
    data may include:
      - vix: float
      - spx_breadth: float in [0,1]
      - pct_above_ma: float in [0,1]
    """
    vix = data.get("vix", 14.0)
    breadth = data.get("spx_breadth", 0.6)
    pct_above = data.get("pct_above_ma", 0.55)

    rules = 0
    rules += 1 if vix >= 20 else 0
    rules += 1 if breadth <= 0.45 else 0
    rules += 1 if pct_above <= 0.5 else 0
    return rules >= 2  # risk-off if 2+ flags

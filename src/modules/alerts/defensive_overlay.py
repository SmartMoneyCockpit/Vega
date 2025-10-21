import os
from data.eodhd_adapter import latest_close

def risk_off(vix_threshold: float = 20.0) -> bool:
    try:
        vix = latest_close("^VIX")
        if vix is None: 
            return False
        return vix >= float(vix_threshold)
    except Exception:
        return False

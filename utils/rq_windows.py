# utils/rq_windows.py
# Simple stub to prevent import errors in monitor_vol_hedge.py

def get_window_status():
    """Return a dummy status for rate/quotas windows check."""
    return {"ok": True, "msg": "stub window check"}

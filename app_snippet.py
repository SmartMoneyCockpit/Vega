# app_snippet.py
# Call this from app.py ONCE at startup (before you render the UI)
from vega_monitor.service import start_vega_monitor

def start_vega_monitor_if_needed():
    # 5s sensor cadence is a good default; adjust if needed
    start_vega_monitor(interval=5)

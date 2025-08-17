import threading
from vega_monitor.service import MonitorService

def start_vega_monitor():
    t = threading.Thread(target=MonitorService().run_forever, kwargs={"interval":5}, daemon=True)
    t.start()
    return t

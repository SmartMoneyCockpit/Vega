try:
    from ib_insync import IB  # optional
except Exception:
    IB = None

class IBKRClient:
    def __init__(self, host="127.0.0.1", port=7497, client_id=111):
        self.host, self.port, self.client_id = host, port, client_id
        self._ib = None

    def connect(self):
        if IB is None:
            return False, "ib_insync not available"
        try:
            self._ib = IB()
            self._ib.connect(self.host, self.port, clientId=self.client_id, readonly=True)
            return True, "connected"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        try:
            if self._ib:
                self._ib.disconnect()
        except Exception:
            pass

    def scan_example(self, symbols=None):
        symbols = symbols or ["AAPL", "MSFT", "SPY"]
        return [{"symbol": s, "signal": "neutral", "note": "stub"} for s in symbols]

# src/ibkr_bridge/mktdata.py
from ib_insync import Stock
from ibkr_bridge.connect import connect, disconnect
from ibkr_bridge.async_utils import run

def snapshot(symbol: str, exchange: str = "SMART", currency: str = "USD", host="127.0.0.1", port=8080, client_id=16):
    ib = connect(host=host, port=port, client_id=client_id)
    try:
        contract = Stock(symbol, exchange, currency)
        data = run(ib.reqMktDataAsync(contract, '', False, False))
        return data
    finally:
        disconnect(ib)

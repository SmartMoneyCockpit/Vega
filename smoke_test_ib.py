
import os
from ib_insync import IB, Stock

IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", "7496"))
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "1"))

print(f"Connecting to IBKR at {IB_HOST}:{IB_PORT} (clientId={IB_CLIENT_ID})...")

ib = IB()
try:
    ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID, timeout=10)
    print("✅ Connected to IBKR")
    account_summary = ib.accountSummary()
    print("Account Summary (first 5 rows):")
    for row in account_summary[:5]:
        print(f"  {row.tag}: {row.value}")
    contract = Stock("AAPL", "SMART", "USD")
    ticker = ib.reqMktData(contract, snapshot=True)
    ib.sleep(2)
    print(f"AAPL snapshot → bid={ticker.bid}, ask={ticker.ask}, last={ticker.last}")
except Exception as e:
    print(f"❌ Connection/test failed: {e}")
finally:
    ib.disconnect()
    print("Disconnected.")

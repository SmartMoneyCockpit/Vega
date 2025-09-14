# ibkr_test.py
# First cockpit scan + IBKR connection test

from ib_insync import IB, Stock

# === Step 1: Connect to IBKR ===
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # adjust port if needed

if not ib.isConnected():
    print("❌ Could not connect to IBKR. Check TWS/Gateway and port.")
    exit(1)

print("✅ Connected to IBKR")

# === Step 2: Define test contract (SPY ETF) ===
contract = Stock('SPY', 'SMART', 'USD')
ib.qualifyContracts(contract)

# === Step 3: Request live market data ===
ticker = ib.reqMktData(contract, '', False, False)
ib.sleep(3)  # wait for data to stream

# === Step 4: Print results ===
print(f"📊 Ticker: {contract.symbol}")
print(f"   Last Price: {ticker.last}")
print(f"   Bid: {ticker.bid}, Ask: {ticker.ask}")
print(f"   Volume: {ticker.volume}")

# === Step 5: Disconnect cleanly ===
ib.disconnect()
print("🔌 Disconnected from IBKR")

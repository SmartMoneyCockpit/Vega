# ibkr_live_test.py
# First cockpit scan + IBKR live connection test

from ib_insync import IB, Stock

# === Step 1: Connect to IBKR (LIVE) ===
ib = IB()
ib.connect('127.0.0.1', 7496, clientId=1)  # LIVE uses port 7496

if not ib.isConnected():
    print("❌ Could not connect to IBKR Live. Check TWS and API settings.")
    exit(1)

print("✅ Connected to IBKR LIVE account")

# === Step 2: Define test contract (SPY ETF) ===
contract = Stock('SPY', 'SMART', 'USD')
ib.qualifyContracts(contract)

# === Step 3: Request live market data ===
ticker = ib.reqMktData(contract, '', False, False)
ib.sleep(3)  # wait for stream

# === Step 4: Print results ===
print(f"📊 Ticker: {contract.symbol}")
print(f"   Last Price: {ticker.last}")
print(f"   Bid: {ticker.bid}, Ask: {ticker.ask}")
print(f"   Volume: {ticker.volume}")

# === Step 5: Disconnect cleanly ===
ib.disconnect()
print("🔌 Disconnected from IBKR LIVE")

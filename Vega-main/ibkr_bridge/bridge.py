
import os
import asyncio
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from ib_insync import IB, Stock, MarketOrder

# ---- ENV ----
APP_KEY = os.getenv("BRIDGE_API_KEY", "")
IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", "7496"))  # LIVE default; set 7497 for paper
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "9"))
IB_PAPER_ONLY = os.getenv("IB_PAPER_ONLY", "false").lower() == "true"
IBKR_MARKET_DATA_TYPE = int(os.getenv("IBKR_MARKET_DATA_TYPE", "1"))  # 1 live,2 frozen,3 delayed,4 delayed-frozen

app = FastAPI(title="IBKR Bridge", version="0.2.0-live")
ib = IB()
ib_connected = False

async def ensure_connected():
    global ib_connected
    if IB_PAPER_ONLY and IB_PORT == 7496:
        raise HTTPException(status_code=400, detail="Live port blocked (IB_PAPER_ONLY=true)")
    if not ib_connected or not ib.isConnected():
        await ib.connectAsync(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID, timeout=8)
        try:
            ib.reqMarketDataType(IBKR_MARKET_DATA_TYPE)
        except Exception:
            pass
        ib_connected = True

@app.get("/health")
async def health():
    return {
        "ok": True,
        "host": IB_HOST,
        "port": IB_PORT,
        "clientId": IB_CLIENT_ID,
        "paper_only": IB_PAPER_ONLY,
        "md_type": IBKR_MARKET_DATA_TYPE,
    }

@app.get("/price/{symbol}")
async def price(symbol: str, x_api_key: str = Header(default="")):
    if APP_KEY and x_api_key != APP_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    await ensure_connected()
    contract = Stock(symbol.upper(), "SMART", "USD")
    ticker = await ib.reqTickersAsync(contract)
    if not ticker:
        raise HTTPException(status_code=404, detail="No data for symbol")
    t = ticker[0]
    last = (t.last or t.close or t.marketPrice())
    return {"symbol": symbol.upper(), "last": float(last) if last is not None else None}

class MarketOrderIn(BaseModel):
    symbol: str
    action: str  # BUY or SELL
    quantity: int

@app.post("/order/market")
async def order_market(order: MarketOrderIn, x_api_key: str = Header(default="")):
    if APP_KEY and x_api_key != APP_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    await ensure_connected()
    contract = Stock(order.symbol.upper(), "SMART", "USD")
    ib.qualifyContracts(contract)
    ord = MarketOrder(order.action.upper(), order.quantity)
    trade = ib.placeOrder(contract, ord)
    while not trade.isDone():
        await asyncio.sleep(0.1)
    return {
        "status": trade.orderStatus.status,
        "filled": trade.orderStatus.filled,
        "avgFillPrice": trade.orderStatus.avgFillPrice,
        "symbol": order.symbol.upper(),
        "action": order.action.upper(),
        "quantity": order.quantity
    }

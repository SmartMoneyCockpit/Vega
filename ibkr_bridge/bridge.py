# vega_ibkr_bridge/bridge.py
# FastAPI bridge between Vega cockpit and IBKR Gateway using ib_insync.
# Security: simple API key via "x-api-key" header. Keep this service private on your network.

import os
import asyncio
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Header, Query
from pydantic import BaseModel
from ib_insync import IB, Stock, Forex, Contract, LimitOrder, MarketOrder, util

APP_VERSION = "0.1.0"

IBKR_HOST = os.getenv("IB_HOST") or os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.getenv("IB_PORT") or os.getenv("IBKR_PORT", "7497"))
IBKR_CLIENT_ID = int(os.getenv("IB_CLIENT_ID") or os.getenv("IBKR_CLIENT_ID", "9"))
API_KEY = os.getenv("BRIDGE_API_KEY", "")
PAPER_ONLY = os.getenv("IB_PAPER_ONLY", "true").lower() == "true"

app = FastAPI(title="Vega ↔ IBKR Bridge", version=APP_VERSION)
ib = IB()

def _require_api_key(x_api_key: str):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

async def _ensure_connected():
    if not ib.isConnected():
        try:
            await ib.connectAsync(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID, timeout=10)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"IBKR connect failed: {e}")

@app.on_event("startup")
async def on_startup():
    util.startLoop()  # ensure asyncio loop for ib_insync
    try:
        await _ensure_connected()
    except Exception:
        # allow startup even if gateway is temporarily unavailable
        pass

@app.get("/health")
async def health():
    return {
        "service": "vega-ibkr-bridge",
        "version": APP_VERSION,
        "connected": ib.isConnected(),
        "host": IBKR_HOST,
        "port": IBKR_PORT,
        "paper_only": PAPER_ONLY,
    }

@app.get("/status")
async def status(x_api_key: str = Header(default="")):
    _require_api_key(x_api_key)
    await _ensure_connected()
    accs = ib.managedAccounts() or []
    return {"accounts": accs, "isConnected": ib.isConnected()}

def _mk_contract(symbol: str, exchange: str = "SMART", currency: str = "USD", asset: str = "stock") -> Contract:
    if asset.lower() == "fx":
        return Forex(symbol)
    return Stock(symbol.upper(), exchange, currency)

@app.get("/price/{symbol}")
async def price(symbol: str, exchange: str = "SMART", currency: str = "USD", asset: str = "stock", snapshot: bool = True, x_api_key: str = Header(default="")):
    _require_api_key(x_api_key)
    await _ensure_connected()
    contract = _mk_contract(symbol, exchange, currency, asset)
    ticker = ib.reqMktData(contract, "", snapshot, False)
    # Small sleep to allow data to arrive; snapshot returns once
    await asyncio.sleep(1.0)
    return {
        "symbol": symbol.upper(),
        "last": float(ticker.last) if ticker.last is not None else None,
        "bid": float(ticker.bid) if ticker.bid is not None else None,
        "ask": float(ticker.ask) if ticker.ask is not None else None,
        "close": float(ticker.close) if ticker.close is not None else None,
        "time": dt.datetime.utcnow().isoformat() + "Z",
    }

@app.get("/quotes")
async def quotes(symbols: str = Query(..., description="Comma separated symbols"),
                 x_api_key: str = Header(default="")):
    _require_api_key(x_api_key)
    await _ensure_connected()
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    contracts = [_mk_contract(s) for s in syms]
    tickers = ib.reqMktDataBatch(contracts, "", True, False)
    await asyncio.sleep(1.0)
    out = {}
    for s, t in zip(syms, tickers):
        out[s] = {
            "last": float(t.last) if t.last is not None else None,
            "bid": float(t.bid) if t.bid is not None else None,
            "ask": float(t.ask) if t.ask is not None else None,
            "close": float(t.close) if t.close is not None else None,
        }
    return out

class OrderReq(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    type: str = "MKT"  # MKT or LMT
    limit_price: Optional[float] = None
    exchange: str = "SMART"
    currency: str = "USD"
    asset: str = "stock"

@app.post("/order")
async def place_order(req: OrderReq, x_api_key: str = Header(default="")):
    _require_api_key(x_api_key)
    if PAPER_ONLY and IBKR_PORT == 7496:
        raise HTTPException(status_code=400, detail="Live trading blocked by PAPER_ONLY policy.")
    await _ensure_connected()
    contract = _mk_contract(req.symbol, req.exchange, req.currency, req.asset)
    if req.type.upper() == "LMT":
        if req.limit_price is None:
            raise HTTPException(status_code=422, detail="limit_price required for LMT orders")
        order = LimitOrder("BUY" if req.side.lower()=="buy" else "SELL", req.quantity, req.limit_price)
    else:
        order = MarketOrder("BUY" if req.side.lower()=="buy" else "SELL", req.quantity)
    trade = ib.placeOrder(contract, order)
    await trade.done()
    return {"orderId": trade.order.orderId, "status": trade.orderStatus.status}

@app.get("/positions")
async def positions(x_api_key: str = Header(default="")):
    _require_api_key(x_api_key)
    await _ensure_connected()
    poss = ib.positions()
    return [{"account": p.account, "symbol": p.contract.symbol, "qty": float(p.position), "avgCost": float(p.avgCost)} for p in poss]

# Run with: uvicorn bridge:app --host $BRIDGE_HOST --port $BRIDGE_PORT

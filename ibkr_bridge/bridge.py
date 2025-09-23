# ibkr_bridge/bridge.py
# FastAPI bridge between Vega cockpit and IBKR Gateway using ib_insync.
# Security: send "x-api-key: <BRIDGE_API_KEY>" with every request.

import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

import datetime as dt
from fastapi import FastAPI, HTTPException, Header, Query
from pydantic import BaseModel
from ib_insync import IB, Stock, Forex, Contract, LimitOrder, MarketOrder

# ---------------------------------------------------------------------------
# Logging (single, rotated)
# ---------------------------------------------------------------------------
_handler = RotatingFileHandler("ibkr_bridge.log", maxBytes=10_000_000, backupCount=3)
logging.basicConfig(
    handlers=[_handler],
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("ibkr_bridge")

# ---------------------------------------------------------------------------
# Optional: SendGrid email alerts (disconnects, hard errors)
# ---------------------------------------------------------------------------
import requests  # noqa: E402

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")


def send_alert(subject: str, body: str) -> None:
    if not SENDGRID_API_KEY or not ALERT_EMAIL:
        return
    try:
        requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": ALERT_EMAIL}]}],
                "from": {"email": "alerts@vega.cockpit"},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body}],
            },
            timeout=5,
        )
    except Exception as e:
        log.error(f"Failed to send alert: {e}")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
APP_VERSION = "0.1.1"

IBKR_HOST = os.getenv("IB_HOST") or os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.getenv("IB_PORT") or os.getenv("IBKR_PORT", "7497"))
IBKR_CLIENT_ID = int(os.getenv("IB_CLIENT_ID") or os.getenv("IBKR_CLIENT_ID", "9"))
API_KEY = os.getenv("BRIDGE_API_KEY", "")
PAPER_ONLY = os.getenv("IB_PAPER_ONLY", "false").lower() == "true"

# ---------------------------------------------------------------------------
# App & IB client
# ---------------------------------------------------------------------------
app = FastAPI(title="Vega ↔ IBKR Bridge", version=APP_VERSION)
ib = IB()  # plain asyncio; no util.startLoop/patching


def _require_api_key(x_api_key: str):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")


async def _ensure_connected():
    if not ib.isConnected():
        try:
            await ib.connectAsync(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID, timeout=10)
            log.info(f"Connected to IBKR {IBKR_HOST}:{IBKR_PORT} as clientId={IBKR_CLIENT_ID}")
        except Exception as e:
            log.warning(f"IBKR connect failed: {e}")
            raise HTTPException(status_code=503, detail=f"IBKR connect failed: {e}")


@app.on_event("startup")
async def on_startup():
    # Do NOT call ib_insync.util.startLoop() under uvicorn.
    try:
        await _ensure_connected()
    except Exception as e:
        # Allow service to start even if Gateway is not reachable yet.
        log.warning(f"Startup: IBKR not yet reachable: {e}")
        send_alert("Vega IBKR Bridge startup warning", f"Gateway not reachable: {e}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _mk_contract(symbol: str, exchange: str = "SMART", currency: str = "USD", asset: str = "stock") -> Contract:
    if asset.lower() == "fx":
        return Forex(symbol)
    return Stock(symbol.upper(), exchange, currency)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
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


@app.get("/price/{symbol}")
async def price(
    symbol: str,
    exchange: str = "SMART",
    currency: str = "USD",
    asset: str = "stock",
    snapshot: bool = True,
    x_api_key: str = Header(default=""),
):
    _require_api_key(x_api_key)
    await _ensure_connected()
    contract = _mk_contract(symbol, exchange, currency, asset)
    ticker = ib.reqMktData(contract, "", snapshot, False)
    # Wait a moment for snapshot ticks to arrive
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
async def quotes(symbols: str = Query(..., description="Comma separated symbols"), x_api_key: str = Header(default="")):
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
    type: str = "MKT"  # MKT, LMT, STP, STP LMT, BRACKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    target_price: Optional[float] = None
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
    side = "BUY" if req.side.lower() == "buy" else "SELL"

    # Basic order types
    if req.type.upper() == "LMT":
        if req.limit_price is None:
            raise HTTPException(status_code=422, detail="limit_price required for LMT orders")
        order = LimitOrder(side, req.quantity, req.limit_price)
        trade = ib.placeOrder(contract, order)
    elif req.type.upper() == "STP":
        if req.stop_price is None:
            raise HTTPException(status_code=422, detail="stop_price required for STP orders")
        from ib_insync import StopOrder
        order = StopOrder(side, req.quantity, req.stop_price)
        trade = ib.placeOrder(contract, order)
    elif req.type.upper() == "STP LMT":
        if req.stop_price is None or req.limit_price is None:
            raise HTTPException(status_code=422, detail="stop_price and limit_price required for STP LMT orders")
        from ib_insync import StopLimitOrder
        order = StopLimitOrder(side, req.quantity, req.limit_price, req.stop_price)
        trade = ib.placeOrder(contract, order)
    elif req.type.upper() == "BRACKET":
        # Entry MKT + Stop + Target
        from ib_insync import BracketOrder
        if req.stop_price is None or req.target_price is None:
            raise HTTPException(status_code=422, detail="stop_price and target_price required for BRACKET")
        parent = MarketOrder(side, req.quantity)
        bracket = BracketOrder(
            parent=parent,
            takeProfitPrice=req.target_price,
            stopLossPrice=req.stop_price,
        )
        # Place bracket legs
        trades = [ib.placeOrder(contract, o) for o in bracket]
        for t in trades:
            await t.done()
        return {"orders": [{"orderId": t.order.orderId, "status": t.orderStatus.status} for t in trades]}
    else:
        order = MarketOrder(side, req.quantity)
        trade = ib.placeOrder(contract, order)

    await trade.done()
    return {"orderId": trade.order.orderId, "status": trade.orderStatus.status}


@app.get("/positions")
async def positions(x_api_key: str = Header(default="")):
    _require_api_key(x_api_key)
    await _ensure_connected()
    poss = ib.positions()
    return [
        {"account": p.account, "symbol": p.contract.symbol, "qty": float(p.position), "avgCost": float(p.avgCost)}
        for p in poss
    ]


@app.get("/orders")
async def orders(x_api_key: str = Header(default="")):
    """
    Recent trades and open orders summary for the UI.
    """
    _require_api_key(x_api_key)
    await _ensure_connected()
    out = []

    # Recent trades (fills)
    for t in ib.trades()[-50:]:
        out.append(
            {
                "orderId": t.order.orderId,
                "status": t.orderStatus.status,
                "symbol": getattr(t.contract, "symbol", None),
                "side": getattr(t.order, "action", None),
                "qty": getattr(t.order, "totalQuantity", None),
                "type": getattr(t.order, "orderType", None),
                "limit": getattr(t.order, "lmtPrice", None),
                "stop": getattr(t.order, "auxPrice", None),
                "time": dt.datetime.utcnow().isoformat() + "Z",
            }
        )

    # Open orders
    for o in ib.openOrders():
        out.append(
            {
                "orderId": o.orderId,
                "status": "Open",
                "symbol": getattr(o, "symbol", None),
                "side": getattr(o, "action", None),
                "qty": getattr(o, "totalQuantity", None),
                "type": getattr(o, "orderType", None),
                "limit": getattr(o, "lmtPrice", None),
                "stop": getattr(o, "auxPrice", None),
                "time": dt.datetime.utcnow().isoformat() + "Z",
            }
        )

    return out

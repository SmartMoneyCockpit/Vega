# Vega ↔ IBKR Bridge

A minimal FastAPI service that lets the Vega cockpit talk to the IBKR Gateway via ib_insync.

## Env Vars to set (Render → Environment)

- `IB_HOST` (or `IBKR_HOST`) = `127.0.0.1` (if bridge and gateway run on same host)
- `IB_PORT` (or `IBKR_PORT`) = `7497` for paper, `7496` for live
- `IB_CLIENT_ID` (or `IBKR_CLIENT_ID`) = small integer, e.g. `9`
- `BRIDGE_API_KEY` = strong random string, used in `x-api-key` header
- `BRIDGE_HOST` = `0.0.0.0`
- `BRIDGE_PORT` = `8088`
- `IB_PAPER_ONLY` = `true` (blocks live trading ports by default)

## Start
```
uvicorn bridge:app --host $BRIDGE_HOST --port $BRIDGE_PORT
```

## Example call
```
curl -H "x-api-key: $BRIDGE_API_KEY" http://127.0.0.1:8088/price/AAPL
```

## Endpoints
- `GET /health` – no auth, shows connection state
- `GET /status` – auth
- `GET /price/{symbol}` – snapshot quote
- `GET /quotes?symbols=AAPL,MSFT,SPY` – batch quotes
- `GET /positions` – positions
- `POST /order` – place simple market/limit orders (paper by default)

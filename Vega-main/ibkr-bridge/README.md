# IBKR Bridge (LIVE defaults)

- Default port: **7496** (LIVE). Set `IB_PORT=7497` for paper.
- Forces market data type from `IBKR_MARKET_DATA_TYPE` (1 live, 2 frozen, 3 delayed, 4 delayed-frozen).
- Blocks LIVE if `IB_PAPER_ONLY=true`.

## Env (server)
```
IB_HOST=127.0.0.1
IB_PORT=7496
IB_CLIENT_ID=9
IB_PAPER_ONLY=false
IBKR_MARKET_DATA_TYPE=1
BRIDGE_API_KEY=VegaTrading2025X
BRIDGE_HOST=0.0.0.0
BRIDGE_PORT=8088
```

# Env Compatibility

This patch lets the cockpit read either **IB_*** or **IBKR_*** env names, and optionally `IBKR_BRIDGE_URL` (e.g., `http://167.71.145.48:4002`).

**Recommended Render secrets** (pick one prefix; both now work):
- IB_HOST or IBKR_HOST = 167.71.145.48
- IB_PORT or IBKR_PORT = 4002   # must be 4002 for IB Gateway
- IB_CLIENT_ID or IBKR_CLIENT_ID = 7
- IB_MKT_TYPE or IBKR_MARKET_DATA_TYPE = 3

If you prefer a single value:
- IB_BRIDGE_URL or IBKR_BRIDGE_URL = http://167.71.145.48:4002

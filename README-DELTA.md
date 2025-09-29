
# Delta Package – IBKR Bridge Unification & Diagnostics

This update centralizes how the cockpit discovers your IBKR Bridge URL and fixes timeouts/headers.

## What changed
- `config/ib_bridge_client.py`: single source of truth for bridge URL + API key header.
- `cockpit_client/ib_bridge_client.py`: uses headers for `/health` and longer default timeout.
- Streamlit pages (`src/pages/095_*.py`, `096_*.py`, `097_*.py`, `99_*.py`) now use the shared helper and show clearer errors.
- Added `data/approved_tickers.json` sample so batch tests don't warn when empty.

## Required environment variables (Render -> Environment)
Set ONE of the following:
- **IBKR_BRIDGE_URL**: e.g. `http://93.127.136.167:8888`  ← recommended
- or legacy **IB_BRIDGE_URL**

Optional (alternative piecewise form):
- **BRIDGE_SCHEME** = `http`
- **BRIDGE_HOST**   = `93.127.136.167`
- **BRIDGE_PORT**   = `8888`

If your bridge requires an API key, also set one of:
- **IB_BRIDGE_API_KEY** (recommended)
- or **IBKR_BRIDGE_API_KEY**/**BRIDGE_API_KEY**

## After deploy
1. Open **Bridge Health Check** page. It should display `Testing: http://<host>:<port>/health`.
2. If it still times out, the issue is network-level (VPS firewall, bridge not running, or IP not reachable from Render).
   - On the VPS, ensure the bridge service is listening on `0.0.0.0:8888` and the firewall allows inbound from the internet (or at least from Render).
   - You can test from the VPS: `curl http://127.0.0.1:8888/health` (local) and from an external box: `curl http://<public-ip>:8888/health`.

## Notes
- All cockpit pages now use the same URL + `x-api-key` header automatically.
- Timeouts default to 8s; adjust if needed via code or add a config later.

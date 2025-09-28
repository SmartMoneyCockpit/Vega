# IBKR Bridge URL quick note
Set `IBKR_BRIDGE_URL` to the **HTTP bridge** address, not the TWS socket.
Example (default bridge port): `http://<VPS_PUBLIC_IP>:8088`
Do **NOT** use `:7496` or `:7497` here — those are TWS sockets.

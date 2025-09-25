# IBKR FastAPI Bridge (Paper‑safe)

This bundle gives you a simple **FastAPI** service that the cockpit can call over HTTP.
The service connects to **IBKR Gateway** via **ib_insync** and exposes endpoints like:

- `GET /health` (no auth)
- `GET /price/{symbol}` (requires API key)
- `POST /order/market` (requires API key, simple market order)

> **Safety:** `IB_PAPER_ONLY=true` blocks connecting to the *live* port (`7496`).  
> Keep this enabled until you're intentionally ready to go live.

---

## 1) Install & run on the droplet

```bash
# copy this folder to the droplet, e.g. /root/ibkr-bridge
cd /root/ibkr-bridge

python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt

# env (PAPER trading)
export IB_HOST=127.0.0.1
export IB_PORT=7497          # PAPER=7497; LIVE=7496
export IB_CLIENT_ID=9
export IB_PAPER_ONLY=true
export BRIDGE_API_KEY=VegaTrading2025X
export BRIDGE_HOST=0.0.0.0
export BRIDGE_PORT=8088

# start (leave running)
uvicorn bridge:app --host "$BRIDGE_HOST" --port "$BRIDGE_PORT"
```

If you see `uvicorn: command not found`, you likely did not activate the venv:  
`source /root/ibkr-bridge/.venv/bin/activate` and run again.

> Make sure **IBKR Gateway (Paper)** is running locally on the droplet and listening on **7497**.

---

## 2) Firewall (optional but recommended)

```bash
# Allow ONLY your home IP to reach port 8088
sudo ufw allow from <YOUR_HOME_IP> to any port 8088 proto tcp
```

Or use an SSH tunnel / reverse proxy with HTTPS.

---

## 3) Quick tests (from your laptop)

```bash
# health (no API key)
curl http://<DROPLET_IP>:8088/health

# price (needs API key)
curl -H "x-api-key: VegaTrading2025X" http://<DROPLET_IP>:8088/price/SPY
```

---

## 4) Run as a service (auto‑start on reboot)

```bash
sudo cp ibkr-bridge.service /etc/systemd/system/ibkr-bridge.service
sudo systemctl daemon-reload
sudo systemctl enable --now ibkr-bridge
sudo systemctl status ibkr-bridge --no-pager
```

Edit the service file if you install under a different path.

---

## 5) Point the cockpit to the bridge

On the machine running the cockpit (desktop/Render), set:

```
IBKR_BRIDGE_URL=http://<DROPLET_IP>:8088
BRIDGE_API_KEY=VegaTrading2025X
```

Then drop the provided **Streamlit test page** (`streamlit_page_IBKR_Bridge_Test.py`) into your cockpit `src/pages/` folder and open it in the UI to verify `/health` and `/price` calls.

---

## 6) Endpoints

- `GET /health` → basic status
- `GET /price/{symbol}` → returns `{symbol, last}` (SMART/USD)
- `POST /order/market` JSON body:
  ```json
  { "symbol": "SPY", "action": "BUY", "quantity": 1 }
  ```
  Returns execution summary (for demos; extend as needed).

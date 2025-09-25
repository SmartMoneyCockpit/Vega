# IBKR FastAPI Bridge — LIVE bundle (7496)

This bundle is preconfigured for **LIVE** trading (port **7496**). Flip to paper by changing envs.

## 1) Install & run on the droplet

```bash
cd /root/ibkr-bridge

python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt

# LIVE settings (you can export these in your shell or leave them in the systemd unit)
export IB_HOST=127.0.0.1
export IB_PORT=7496
export IB_CLIENT_ID=9
export IB_PAPER_ONLY=false
export IBKR_MARKET_DATA_TYPE=1       # 1=live
export BRIDGE_API_KEY=VegaTrading2025X
export BRIDGE_HOST=0.0.0.0
export BRIDGE_PORT=8088

uvicorn bridge:app --host "$BRIDGE_HOST" --port "$BRIDGE_PORT"
```

> Make sure **IBKR Gateway (LIVE)** is running on the droplet and listening on **7496**.

## 2) Optional: run as a service (auto-restart)

```bash
sudo cp ibkr-bridge.service /etc/systemd/system/ibkr-bridge.service
sudo systemctl daemon-reload
sudo systemctl enable --now ibkr-bridge
sudo systemctl status ibkr-bridge --no-pager
```

## 3) Cockpit configuration (client side)

```
IBKR_BRIDGE_URL=http://<DROPLET_IP>:8088
BRIDGE_API_KEY=VegaTrading2025X
```

## 4) Quick tests

```bash
curl http://<DROPLET_IP>:8088/health
curl -H "x-api-key: VegaTrading2025X" http://<DROPLET_IP>:8088/price/SPY
```

## 5) Security
- Restrict port 8088 to your IP via UFW or use an SSH tunnel / reverse proxy with TLS.
- Keep `BRIDGE_API_KEY` private and long.

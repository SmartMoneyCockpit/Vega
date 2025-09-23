# Render ↔ Droplet (IBKR) Wiring

## Set Render Secrets (Dashboard → Environment)
- `IB_HOST=167.71.145.48`
- `IB_PORT=4002`
- `IB_CLIENT_ID=7`
(These override `config.yaml` automatically.)

## On the droplet
```
sudo ufw allow 4002/tcp
# In IB Gateway → Configure → API → Settings
#  - Enable ActiveX/Socket Clients
#  - Read-Only API: OFF
#  - Socket port: 4002
#  - Allow connections from localhost only: OFF
#  - Trusted IPs: (optional) leave empty for now; later restrict to Render egress
```

## Free delayed data
In Client Portal enable Free Delayed Data for regions you need (US + Canada confirmed).

## Test from Render build shell or droplet venv
```
python scripts/quick_test_ibkr.py
```

## Cockpit
A new page **IBKR Feed Status** (pages/900_...) lets you press **Test Feed Now** and see prices.

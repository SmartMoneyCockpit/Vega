# Vega Mega Delta (Render ↔ Droplet IBKR, 2025-09-23)

**What this includes**
- Updated `app.py` with links to ib_insync pages
- New pages:
  - `097_IBKR_Quick_Test_ib.py`
  - `098_IBKR_Order_Ticket_ib.py`
- Watchdog (10‑minute interval) and systemd unit templates
- Cleanup scripts to remove duplicate Streamlit pages and old HTTP-bridge pages

**Optional cleanup (run from repo root):**
```
python scripts/cleanup_pages.py
python scripts/cleanup_ib_http_pages.py
```

**Install systemd on the droplet (once):**
```
sudo cp docs/systemd/ibgateway@.service /etc/systemd/system/
sudo cp docs/systemd/ibkr-watchdog@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ibgateway@vega.service
sudo systemctl start  ibgateway@vega.service
sudo systemctl enable ibkr-watchdog@vega.service
sudo systemctl start  ibkr-watchdog@vega.service
```
Change `vega` in the unit names if your Linux user is different.

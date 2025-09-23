
# Install IB Gateway Autostart + Watchdog (DigitalOcean Droplet)

Assumptions:
- Linux username: `vega` (replace if yours differs).
- Vega repo cloned at `/home/vega/vega`.
- IB Gateway start script available at `/opt/ibgateway/scripts/run.sh` (adjust if different).

## Copy files
```
sudo mkdir -p /etc/systemd/system
sudo cp docs/systemd/ibgateway@.service /etc/systemd/system/
sudo cp docs/systemd/ibkr-watchdog@.service /etc/systemd/system/
sudo chown root:root /etc/systemd/system/ibgateway@.service /etc/systemd/system/ibkr-watchdog@.service
```
Place the watchdog script in your repo:
```
mkdir -p /home/vega/vega/scripts
cp scripts/watchdog_ibkr.py /home/vega/vega/scripts/
chown -R vega:vega /home/vega/vega/scripts/watchdog_ibkr.py
```

## Enable firewall
```
sudo ufw allow 4002/tcp
```

## Enable services
```
sudo systemctl daemon-reload
sudo systemctl enable ibgateway@vega.service
sudo systemctl start ibgateway@vega.service

sudo systemctl enable ibkr-watchdog@vega.service
sudo systemctl start ibkr-watchdog@vega.service
```

## Verify
```
systemctl status ibgateway@vega.service
journalctl -u ibgateway@vega.service -f

systemctl status ibkr-watchdog@vega.service
journalctl -u ibkr-watchdog@vega.service -f
```
Edit the units if your paths or username differ.

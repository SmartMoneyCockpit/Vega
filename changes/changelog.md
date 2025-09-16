# Vega Weekly Upgrade — Mini Changelog
Generated: 2025-09-16T18:47:17.412422

## Changes Added
* Integrated Stay Out / Get Back In panel injection in `app.py`.
* Added TradingView Sector Heatmap stub and Sector Flip Alerts stub.
* Added A+ digest email stub and default settings in `config/settings.yaml`.
* Ensured minimal requirements.

### New/Modified Files
- config/settings.yaml
- modules/sector_heatmap.py
- modules/alerts/sector_flip.py
- modules/emailing/aplus_digest.py
- app.py
- requirements.txt

### Notes
- Created config/settings.yaml with polling/alerts/snapshots/email/tradingview defaults.
- Added modules/sector_heatmap.py stub (renders without external deps).
- Added modules/alerts/sector_flip.py stub.
- Added modules/emailing/aplus_digest.py stub.
- Created minimal app.py with injection marker.
- Created minimal requirements.txt.
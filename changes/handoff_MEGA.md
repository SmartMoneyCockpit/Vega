
# Vega MEGA Delta — Single Upload (UI + Automations + Full Wiring)

Generated: 2025-09-16T19:35:02.223817Z

## Included
- UI injection for **Stay Out / Get Back In** (heatmap + flip panel) in `app.py`
- Config defaults in `config/settings.yaml`
- Modules: `modules/sector_heatmap.py`, `modules/alerts/sector_flip.py`, `modules/emailing/aplus_digest.py`
- Workers: `workers/alerts/sector_flip_runner.py`, `workers/snapshots/export_grid.py`, `workers/emailing/send_aplus_digest.py`
- GitHub Actions: `sector_flip_alerts.yml`, `morning_snapshot.yml` (07:45 PT), `aplus_digest.yml` (12:45 PT)
- Requirements updated (streamlit, pandas, numpy, pyyaml, matplotlib, reportlab, requests)
- `.state/` for alert debounce/state

## Secrets (GitHub → Actions → Secrets)
- `SENDGRID_API_KEY`, `ALERTS_FROM`, `ALERTS_TO`
- `TRADINGVIEW_COOKIES` (optional; enables authenticated heatmap)

## Render
- Start: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- Python 3.11 recommended

## Optional
- Put A+ setups CSV at `data/aplus_setups.csv` (columns: ticker, entry, stop, rr, reason, grade).


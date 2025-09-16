# Vega Cockpit — Backlog Wiring Handoff
Generated: 2025-09-16T19:11:19.927681Z

Adds GitHub Actions automations + worker stubs:
- Sector Flip Alerts (hourly; script enforces NA market hours)
- Morning Snapshot at 07:45 PT (14:45 UTC)
- A+ Digest at 12:45 PT (19:45 UTC), silent if no A+ setups

Secrets required (GitHub Actions → Secrets):
- SENDGRID_API_KEY
- ALERTS_FROM
- ALERTS_TO
- TRADINGVIEW_COOKIES (optional, for authenticated TV later)

Files:
- .github/workflows/sector_flip_alerts.yml
- .github/workflows/morning_snapshot.yml
- .github/workflows/aplus_digest.yml
- workers/alerts/sector_flip_runner.py
- workers/snapshots/export_grid.py
- workers/emailing/send_aplus_digest.py

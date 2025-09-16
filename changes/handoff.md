# Vega Cockpit — Handoff Sheet

**Generated:** 2025-09-16T18:47:17.412980

## Environment / Secrets (Render)
- `SENDGRID_API_KEY` (for A+ digest email; optional if disabled)
- `ALERTS_TO` (comma emails) / `ALERTS_FROM`
- `TRADINGVIEW_COOKIES` (if using authenticated TradingView mode)
- `APP_ENV` (optional)
- `TZ` (should be America/Los_Angeles or your preferred)

## Render Settings
- Entry point: `app.py`
- Build: Python 3.11
- Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

## Manual Steps
1. If you want authenticated TradingView heatmaps, add `TRADINGVIEW_COOKIES` and set `tradingview.mode = authenticated` in `config/settings.yaml`.
2. For A+ digest email, set SendGrid vars and confirm `email.aplus_digest.enabled: true`.
3. Verify the `snapshots/` folder persists (Render disk or S3) if you want morning exports long-term.
4. Commit files to GitHub; Render redeploy will pick up changes.

## What’s included in this delta
- Panel injection (Heatmap + Flip Alerts)
- Default settings and minimal requirements

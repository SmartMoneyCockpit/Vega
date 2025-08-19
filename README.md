# Vega Cockpit — GitHub Actions Batch

This repository offloads **monitoring and report generation** from ChatGPT to **GitHub Actions**.

## What’s Included
- **Volatility & Hedge Monitor** (every 15 min): UVXY, SVIX, VIX bands, USDJPY, Breadth proxy (SPY vs RSP). Optional logging to a GitHub **Gist**.
- **North American Morning Report** (7:25 AM PT): USA, Canada, Mexico, LatAm — ultra‑digest format.
- **Asia‑Pacific Afternoon Report** (6:00 PM PT): Japan, Australia, China, Hong Kong, South Korea — ultra‑digest format.
- Output via **Webhook** (Slack/Discord/Teams) and/or **Email (SMTP)**.

## Quick Start
1. Push this repo to GitHub.
2. In **Settings → Secrets and variables → Actions**, add any of the following:
   - `WEBHOOK_URL` (Slack/Discord/Teams) **optional**
   - `EMAIL_TO`, `EMAIL_FROM`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` **optional**
   - `TZ_PREF` (default `America/Los_Angeles`)
   - *(Optional alert logging)* `GIST_ID`, `GIST_TOKEN`
3. The workflows run on schedule automatically. You can also run them manually from the **Actions** tab.

## Files
- `.github/workflows/vega_cockpit_automation.yml` — All jobs & schedules
- `monitor_vol_hedge.py` — 15‑minute monitor with optional Gist logging
- `report_na.py` — North American Morning Report generator
- `report_apac.py` — Asia‑Pacific Afternoon Report generator
- `email_webhook.py` — Output helpers
- `utils.py` — Shared helpers
- `calendar.yaml` — Optional manual event additions (user editable)

## Notes
- Schedules are set in **UTC** to match PT targets. Adjust for DST if needed.
- The monitor only **acts** in market windows (US 6–14 PT; APAC 18–22 PT) to keep noise down.
- If `WEBHOOK_URL` and SMTP are both unset, scripts will just print to the job logs.


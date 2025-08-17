# Vega Monitor & Scorecard — Quick Install

## Files to copy into your repo
- vega_monitor/ (sensors, policy, alerts, service, ui_panel)
- jobs/scorecard_weekly.py
- app_snippet.py (optional helper)
- requirements.txt additions (merge with yours)

## Environment
VEGA_WEBHOOK_URL=<your webhook>
VEGA_EMAIL_HOST=<smtp.host>
VEGA_EMAIL_PORT=465
VEGA_EMAIL_USER=<bot@yourdomain>
VEGA_EMAIL_PASS=<app_password>
VEGA_EMAIL_TO=<your_email>
VEGA_THRESH_WARN=0.75
VEGA_THRESH_ACTION=0.80
VEGA_THRESH_CRITICAL=0.90

## Start the monitor (example)
from app_snippet import start_vega_monitor
start_vega_monitor()  # call on app startup

## Weekly scorecard
- Use jobs/scorecard_weekly.py as a cron job, or wire APScheduler in your app.

## Defensive Mode
- Triggers when any 90% critical, or two 80% action metrics persist.
- Sends webhook/email; gates heavy jobs until recovered.

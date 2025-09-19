# Vega Cockpit — Schedulers & Reports (3 regions)

This folder contains **reusable workflows** and **region callers** for:
- Morning Report (NA, Europe, APAC)
- File Scheduler (earnings CSV filler per region)

## Edit/Customize
- Cron times are in UTC (see comments). Adjust to your desk hours.
- Timezones: NA uses `America/Los_Angeles`, EU uses `Europe/London`, APAC uses `Asia/Tokyo` by default.
- Replace `scripts/reports/generate_morning_report.py` with your real report builder.
- Replace `scripts/scheduler/fill_earnings_csv.py` with your real CSV logic.

## Notifications
- Each job writes a short Job Summary and uploads artifacts.
- You can add Slack/Email steps where your secrets are configured.

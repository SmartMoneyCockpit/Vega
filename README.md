📘 Vega Cockpit — README
Overview

Vega Cockpit is your trading dashboard and AI co-pilot, designed to:

Track trades, logs, and journals

Run daily/weekly Scorecards

Monitor system resources (“shields before swords”)

Enforce Smart Money trading rules and defensive guardrails

⚡ Quickstart (Day-1 MVP)

Drop your service account key into the project root as:

credentials.json


Run locally

pip install -r requirements.txt
streamlit run app.py


Deploy on Render

Create a new Web Service using this repo and render.yaml

After service is created, add a Secret File named credentials.json and paste the full JSON

Open the URL: verify the Watchlist and Quick Log work with your Google Sheet

📊 Google Sheets Integration

Expects a Google Sheet tab named COCKPIT

Watchlist reads: A2:D50 → columns: Ticker | Strategy | Entry | Stop

Quick log appends: [timestamp, type, symbol, status, notes] into the COCKPIT tab

🛡 Vega Resource Monitor & Scorecard
Files

vega_monitor/ (sensors, policy, alerts, service, ui_panel)

jobs/scorecard_weekly.py (PDF + Excel generator)

app_snippet.py (helper to start background monitor)

Environment
VEGA_WEBHOOK_URL=<your webhook>
VEGA_EMAIL_HOST=<smtp.host>
VEGA_EMAIL_PORT=465
VEGA_EMAIL_USER=<bot@yourdomain>
VEGA_EMAIL_PASS=<app_password>
VEGA_EMAIL_TO=<your_email>
VEGA_THRESH_WARN=0.75
VEGA_THRESH_ACTION=0.80
VEGA_THRESH_CRITICAL=0.90

Start the Monitor

In app.py (or your entrypoint), add:

from app_snippet import start_vega_monitor
start_vega_monitor()   # call on startup

Weekly Scorecard

Run jobs/scorecard_weekly.py manually, via cron, or APScheduler

Generates snapshots/Trade_Quality_Scorecard_<DATE>.pdf and .xlsx

Defensive Mode

Triggers when any metric ≥90% or two metrics ≥80% persist

Sends webhook/email alerts

Gates heavy jobs and trading approvals until system recovers

📦 Dependencies

Pinned in requirements.txt. Includes:

Core: streamlit, pandas, numpy, requests

Google Sheets: gspread, google-auth, google-api-python-client

Market data: yfinance

Math/Indicators: matplotlib, plotly, ta, scipy, statsmodels

News/API: newsapi-python (optional)

IBKR: ib-insync, eventkit (optional)

Vega Monitor additions: psutil, watchdog, reportlab, openpyxl, APScheduler

🚀 Deployment Notes

Render: define secrets for credentials.json and Vega env vars

Failover: Monitor auto-gates Vega to prevent overload

Upgrades: Vega recommends value-optimal scaling when resource use >80%

✅ Next Steps

Merge your trading logic/modules into this cockpit

Enable Resource Monitor + Scorecard to keep Vega “self-diagnosing”

Trust ACI Mode to enforce shields before swords

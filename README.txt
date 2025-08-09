# Vega Bundle v1 — 2025-08-09T17:31:30.900670Z

## Files
- app.py
- vega_tradeability_meter.py (Google Sheets sync + test button)
- auto_hedging_engine.py
- macro_dashboard.py
- sheets_sync.py
- requirements.txt
- .gitignore
- data/macro_calendar.csv

## Deploy
1. Upload all files to your repo root (keep `data/` folder).
2. Render → Environment:
   - POLYGON_KEY = <your key>
   - GOOGLE_SA_PATH = /etc/secrets/gcp_service_account.json
   - SHEETS_SPREADSHEET_ID = <your sheet id>
   - SHEETS_WORKSHEET_NAME = tradeability_log
3. Render → Secret Files: upload your SA JSON at /etc/secrets/gcp_service_account.json
4. Deploy latest commit.

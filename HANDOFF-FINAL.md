Final Build (Phases 1–7) — One Drop

Your Steps (simple)
1) Put this ZIP into /Drops.
2) In GitHub → Actions → Run workflow: vega-offloaded-tasks (one time to seed).
3) Optional (enable live integrations in Render → Environment):
   - SHEETS_SPREADSHEET_ID, GOOGLE_SERVICE_ACCOUNT_JSON
   - IBKR_HOST, IBKR_PORT (7497 paper / 7496 live), IBKR_CLIENT_ID
4) Open the app in Render; everything is wired and runs automatically on schedule.

What’s Included
- All dashboards: Breadth, VectorVest, ETF Tactical, APAC, Guardrails Gauges, IBKR Charts
- Trade tools: Options Helper, AI Trade Quality Scorecard, Backtest, AI Pattern Profiler
- Filters: Canada (Tariff/USMCA/Smart Money/Action Plan)
- Reports/Exports: One-Click Daily Report PDF, Breadth Snapshot, Journal to Sheets (if configured)
- Automation: Auto-Hedging Engine, Capital Rotation triggers, Guardrails alerts
- Hygiene: Cleanup inventory each run; lean repo focus

Start command (Render)
streamlit run app.py --server.port $PORT --server.address 0.0.0.0

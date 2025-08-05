<<<<<<< HEAD

SMART MONEY COCKPIT - FINAL DEPLOYMENT INSTRUCTION SET (FOR LIVE AGENT)

OBJECTIVE: Fully deploy the Smart Money Cockpit with every module, repair, and automation enabled. All tasks must complete without errors. This is the final deployment - after this, the system is considered live and no further upgrades are available.

ENVIRONMENT SETUP:
- Confirm Python 3.11+ is installed
- Ensure all dependencies from requirements.txt are installed: streamlit, ib_insync, gspread, oauth2client, etc.
- Run: pip install -r requirements.txt
- Ensure the folders assets/, modules/, config/, and logs/ exist; create them if missing.

MODULE VERIFICATION (All Must Be Active and Functional):
1. INFRASTRUCTURE
- Streamlit Cloud connection live
- GitHub repo connected with main + staging branches
- Google Sheets backend named "COCKPIT" is linked and editable
- TradingView + IBKR login modules prepared (IB Gateway with autorun enabled)
- Local fallback ZIP identical to cloud version
- Folder scanner for assets, config, and module health checks

2. CORE MODULES
- Trade Logger, Strategy Builder, Candlestick Pairing Tool
- Pattern Ranker (OBV, ADX, Bollinger, Ichimoku, etc.)
- Watchlist Screener with Smart Money Grade (📈📉) and Tariff Filter (🟢🟠🔴)
- ETF Swing Dashboard (Japan, Korea, Hong Kong, Australia)
- Preferred Income Basket logic for CPD, ZPR, HPR (with trailing stop filters)
- SPY & Inverse ETF Scanner (SPXU, SQQQ, RWM)
- BoJ Rate Hike Playbook (includes FX-triggered sector alerts)
- Macro Alert Engine (Fed, CPI, BoJ, war, sanctions, etc.)

3. INTELLIGENCE MODULES
- AI Trade Scorecard (grades daily trades)
- Auto-Journal Generator (adds lessons learned automatically)
- AI Pattern Profiler (detects most frequent winning trade setups)
- PnL & Risk Breakdown Panel (per trade, per week, per strategy)
- Backtest Mode toggle (simulated trade run, doesn't affect Journal)
- AI Memory Replay (weekly review of best/worst trade decisions)
- Auto-Hedging Engine (deploys inverse ETF setup alerts if needed)

4. HEALTH & PERFORMANCE MODULES
- BP & Vagal Recovery Tracker (daily logging & charting)
- Sleep Sync Tracker (aligns sleep vs vagal readiness vs trade performance)
- Post-Workout Decompression Protocol Generator
- BP Weekly Trend PDF Exporter
- Daily Health triggers visible in cockpit if thresholds breached

5. RISK MANAGEMENT SYSTEMS
- Capital Exposure Guardrails (detects overexposure to sectors or style)
- Journal-linked macro catalysts and tariff events
- Global Risk Heatmap: Volatility (VIX), Currencies (JPY, CADUSD), Geopolitical risks
- Trade Entry Filter: No trades unless conditions match Smart Money + macro filter

6. AUTOMATION, REFRESH, EXPORTS
- Scheduled refresh daily at 7:45 AM
- Auto-export of:
  - Daily PDF snapshot: Journal, Health log, Trade log, Watchlist, Macro events
  - Google Sheets backup for each day's logs
- Macro calendars: Live Daily + Weekly planner
- Macro + Health + Trade alerts sent via webhook (Telegram excluded)

DEPLOYMENT ACTIONS:
1. Build and deliver final cockpit ZIP (fully bundled with all modules, assets, and fallback logic)
2. Push to GitHub (main + staging branches synced)
3. Deploy to Streamlit Cloud from GitHub
   - Set necessary environment variables (e.g. GOOGLE_API_KEY) if required
   - Test Streamlit launch and confirm live app
4. Initialize Live Agent Runtime
   - Folder and file check passes
   - Live Agent starts without error
   - Logs stored in logs/deployment_complete.log
5. Run webhook test (optional but recommended)

AGENT EXIT CRITERIA:
✅ No crash or runtime errors  
✅ All modules load with success  
✅ Streamlit and GitHub in sync  
✅ ZIP is stored locally and archived  
✅ Journal, Logger, Strategy, Health, Hedging, Alerting, Macro Systems are all live  
✅ deployment_complete.log confirms system integrity  

ADDITIONAL USER INFO:
- GitHub repo is already created (reuse existing)  
- Google Sheet named "COCKPIT" is ready with correct structure  
- IBKR Trader Workstation + Gateway are installed and set to autorun  
- Visual assets (coin, placeholder animals) approved and available  
- Cockpit local path is assumed to be Desktop/cockpit/ unless overridden  

AFTER COMPLETION, REPORT:
"Cockpit is fully operational. No further modules or upgrades are available. System is execution-ready."
=======
Smart Money Cockpit
===================

This project provides a **Streamlit** dashboard for personal trading and wellness management.  The dashboard includes a suite of modules for logging trades, monitoring health, drafting strategies, generating daily briefings, and tracking macroeconomic and market data.  It is designed to run either locally or on [Streamlit Cloud](https://streamlit.io/cloud) from a single ZIP archive, without requiring manual uploads after deployment.

## Features

- **Trade Logger** – record trades, including position size, entry/exit prices, and notes.  Logged trades are synchronised to a Google Sheet named **COCKPIT**.
- **Smart Money Logic** – a placeholder for your custom trading algorithms.  The module includes a framework for analysing order flow and positioning but does not implement proprietary logic by default.
- **Health Tracker** – track daily wellness metrics such as sleep, exercise, heart rate, and mood.  Integrated suggestions for vagal tone exercises are generated after workout entries.
- **Daily Morning Briefing** – automatically generates a morning briefing summarising overnight market moves and upcoming macro events.  Data sources are configurable and can be extended.
- **Journal Logger** – a unified journal where trade logs, health entries and strategy notes are automatically stored.  Entries are written to both the local data folder and the **COCKPIT** Google Sheet.
- **Strategy Builder** – define and save trading strategies.  Users can specify indicators, risk parameters, entry/exit rules and notes.
- **PDF Generator** – export selected reports (e.g. daily briefing or journal) to PDF using the `reportlab` library.
- **Training Tier** – keep track of educational materials, backtests and practice exercises.  This module is intentionally flexible to fit individual workflows.
- **Macro/Micro Dashboard** – display real‑time macroeconomic data, index levels, yield curves and sentiment indicators.
- **Bear Mode / Tail‑Risk Watchlist** – monitor risk‑off assets and configure price alerts.  Users can set thresholds for volatility spikes and tail‑risk events.
- **ETF Dashboard** – track swing‑to‑investing ETFs across Japan, Korea, Australia and Hong Kong.  Charts are sourced via `yfinance`.
- **BoJ Rate Hike Playbook** – follow Japanese FX triggers and sector watchlists around potential Bank of Japan rate changes.
- **Tariff‑Aware Canada Stock Screener** – screen Canadian stocks with tariff grades, USMCA filters and smart money scores.  The grading logic is stubbed but can be expanded.
- **Preferred Income Basket Tracker** – track preferred share ETFs (ZPR, HPR, CPD) with stop‑yield logic.
- **Live PnL Tracker** – monitor live profit and loss using data from IBKR (Interactive Brokers).  The integration uses `ib_insync`, but live data requires credentials and the IBKR gateway running.
- **SPY and Contra ETF Tracker** – follow SPY and leveraged inverse ETFs such as SPXU, SQQQ and RWM.  Includes simple performance charts and relative strength comparisons.

## Setup

1. **Install dependencies**:  Run `pip install -r requirements.txt` in a virtual environment.  The dependencies include Streamlit, Pandas, NumPy, YFinance, GSpread and others.
2. **Google Sheets credentials**:  To enable sheet synchronisation, create a Google Service account and download the JSON credentials file.  Save it as `credentials.json` in the project root or configure the path in `modules/google_sheets.py`.  Make sure the service account has access to a Google Sheet named `COCKPIT`.
3. **IBKR integration**:  To pull live data from Interactive Brokers, ensure the IB Gateway or Trader Workstation is running, and set your IBKR host/port in the `.env` file.  The module `modules/ibkr.py` uses `ib_insync` to connect.
4. **Running locally**:  From the project root, run `streamlit run app.py`.  The application should start in your default browser.
5. **Deploying to Streamlit Cloud**:  Compress the entire `smart_money_cockpit` directory into a zip archive (`smart_money_cockpit.zip`) and upload it to the Streamlit Cloud interface.  Make sure to include all dependencies and assets.

## Customisation

The project is intentionally modular.  Each module lives in its own file under the `modules/` directory.  You can modify or extend these modules to fit your specific workflows.  Placeholder functions are clearly marked and can be replaced with your own logic.  For example, if you have a proprietary smart money algorithm, you can implement it in `modules/smart_money_logic.py`.

Visual branding assets (coin graphic and animal photos) are stored in the `assets/` directory.  You can replace these images with your own files while keeping the same filenames to avoid code changes.

## Disclaimer

This dashboard is provided **for informational purposes only**.  It does not constitute financial advice.  You are responsible for verifying data accuracy and complying with local regulations.  The authors accept no liability for losses incurred through the use of this software.
>>>>>>> 1d7947d895ee627f5b66a78bde632d8d795e9410

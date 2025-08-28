📖 Vega Trading Cockpit
Overview

Vega Cockpit is a Streamlit-based trading dashboard for stocks and ETFs.
It centralizes daily decision-making, trade tracking, journaling, and performance analytics.

🚀 Quick Start

Clone this repo and install requirements:

pip install -r requirements.txt

Run locally:

streamlit run app.py

Deploy on Render:

Push commits to GitHub.

Render will auto-build and serve the cockpit.

Secrets (email alerts / Sheets logging):
Add these under Render → Settings → Environment:

SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM, SMTP_TO

GOOGLE_SERVICE_ACCOUNT_JSON (if using Google Sheets logging)

📊 Modules
✅ Stay Out vs Get Back In

Decision module with R:R guardrails & earnings blackout.

Logs decisions to data/journal_decisions.csv.

Sends email alerts on flips to GET_BACK_IN.

Exports to PDF/CSV.

🔄 PnL & Risk Breakdown Panel

Reads data/trades.csv.

KPIs: total PnL, win rate, average R, expectancy, max drawdown.

Equity curve & weekly PnL charts.

Breakdowns by ticker or strategy.

🔄 AI Trade Quality Scorecard

Grades trades A–F based on process rules & Smart Money filters.

Considers R:R planned vs realized, stop discipline, plan adherence, earnings proximity.

🔄 Auto-Journal Generator

Combines trades + decisions into daily .md reports.

Saves under data/journal/ and offers download.

Can email daily journal summaries.

(Modules marked 🔄 are in active rollout via Weekly Drops.)

📂 Data Schema
data/trades.csv

Headers:
date,ticker,side,strategy,qty,entry,stop,exit,fees,notes,rr_planned,r_multiple,followed_plan,stop_respected,setup_quality,earnings_within_30d,risk_off

Minimum required (PnL Panel):
date,ticker,side,strategy,qty,entry,stop,exit,fees

Optional (improves Scorecard & Journal):

rr_planned → planned R:R

r_multiple → realized R multiple

followed_plan → true/false

stop_respected → true/false

setup_quality → 1–5 rating

earnings_within_30d → true/false

risk_off → true/false

Example row:
2025-08-22,SPY,LONG,Breakout,100,500,490,510,2,example,2.0,1.0,true,true,4,false,false

data/journal_decisions.csv

Written by Stay Out vs Get Back In.

Fields: timestamp, ticker, action, rationale, entry, stop, target, reward_risk, days_to_earnings, triggers.

data/journal/

Daily auto-generated .md reports by Auto-Journal Generator.

📅 Weekly Drops

Vega evolves through Weekly Drops (bundles of new modules released each Monday).

Process

Each Monday, create a GitHub Issue:
Weekly Drop – YYYY-MM-DD

Paste the standard checklist (scope, verification, sign-off).

Check off items as work is completed.

Close the issue once deployed + signed off.

Example Checklist
Weekly Drop – 2025-09-01

Scope

 Add PnL & Risk Breakdown Panel

 Add AI Trade Quality Scorecard

 Add Auto-Journal Generator

 Docs updated (ROADMAP.md, CHANGELOG.md)

Verification

 Render build OK

 Critical pages load

 Alerts fire (test email)

Sign-off

 Blaine reviewed

 Tag release

🛠️ Requirements

streamlit
yfinance>=0.2.40
pandas
numpy
pyyaml
requests
fpdf2>=2.7.9

(Optional)
gspread, google-auth if using Google Sheets logging.

🧭 Roadmap

See ROADMAP.md for the full list of approved features and status.

See CHANGELOG.md for release notes per weekly drop.

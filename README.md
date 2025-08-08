# Smart Money Cockpit

This project provides a Streamlit dashboard for personal trading and wellness management. It includes modules for logging trades, monitoring health, drafting strategies, generating briefings, and tracking macroeconomic and market data. It runs locally or on Render from a single ZIP archive or GitHub repo.

## Features

- Trade Logger – record trades, size, price, and notes; syncs to a Google Sheet (COCKPIT)
- Smart Money Logic – framework for a custom order flow and positioning logic
- Health Tracker – daily logs of sleep, exercise, HR, and vagal recovery suggestions
- Morning Briefing Generator – macro summary with upcoming events
- Journal Logger – unified journal for trades, health, and strategy
- Strategy Builder – plan setups with indicators and rules
- PDF Generator – export briefings or journals via ReportLab
- Training Tier – track education, backtests, or research
- Macro/Micro Dashboard – visualize indexes, FX, yield curves, and sentiment
- Bear Mode + Tail-Risk Watchlist – monitor inverse ETFs, VIX, and alerts
- ETF Dashboard – track Japan/Korea/Australia/Hong Kong ETFs
- BoJ Rate Hike Playbook – FX triggers and sector watchlists
- Canada Stock Screener – filter by tariff exposure and smart money score
- Preferred Income Tracker – track ZPR, HPR, CPD with trailing stop filters
- PnL Tracker – monitor profit and loss (IBKR Gateway required)
- SPY + Contra ETF Scanner – includes SPXU, SQQQ, RWM tracking

## Setup

1. Install dependencies:
   pip install -r requirements.txt

2. Google Sheets setup:
   - Create a service account via Google Cloud Console
   - Download credentials.json
   - Share your COCKPIT Google Sheet with the service account email

3. IBKR integration:
   - Run IB Gateway or TWS locally
   - Use .env to define IBKR_USERNAME, IBKR_PASSWORD, etc.

4. Running locally:
   streamlit run app.py

5. Deploy to Render or Streamlit Cloud:
   - Push to GitHub
   - Configure .env and credentials.json in the cloud environment

## Customization

- Each module lives under modules/ and is hot-loadable using importlib
- Replace placeholders like assets/coin.png or assets/animal_1.jpg with your own visuals
- Modify or override any render() method per module

## Disclaimer

This dashboard is for informational and personal-use only. It does not provide financial advice. Use responsibly and comply with local regulations.

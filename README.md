# Vega Cockpit (Starter)

[![Universal Report Scheduler](https://github.com/SmartMoneyCockpit/Vega/actions/workflows/universal_report_scheduler.yml/badge.svg)](https://github.com/SmartMoneyCockpit/Vega/actions/workflows/universal_report_scheduler.yml)

Minimal Streamlit cockpit that runs locally and on Render.  
**Docs for the VectorVest-style Rulepack live in [docs/rulepack/](docs/rulepack/).**

## Features
- Streamlit app with demo charts (SPY/QQQ) and tabs
- Render-ready (`render.yaml`)
- Clean `requirements.txt` with safe pins
- `.env.example` scaffold for local runs; use Render Environment for real secrets
- **Automated Reports**: Universal Report Scheduler builds Morning Report, Color Guard, and Economic Calendar artifacts daily (downloadable under Actions → run page)

## Local Run
**Python 3.11+ recommended.**

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

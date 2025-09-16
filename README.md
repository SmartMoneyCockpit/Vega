# Vega Cockpit (Starter)

Minimal Streamlit cockpit that runs locally and on Render.  
**Docs for the VectorVest-style Rulepack live in [`docs/rulepack/`](docs/rulepack/).**

## Features
- Streamlit app with demo charts (SPY/QQQ) and tabs
- Render-ready (`render.yaml`)
- Clean `requirements.txt` with safe pins
- `.env.example` scaffold for local runs; use Render Environment for real secrets

## Local Run
**Python 3.11** recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

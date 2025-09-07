# Vega Rulepack (VectorVest-style) — 2025-09-07

This bundle contains:
- **13 strategy rules** (consolidated from your VectorVest UniSearch set)
- **VV-like scoring proxies** (`_vega_scores.yaml`) for RT/RS/RV/CI/VST
- **Region settings** (`config/regions.yaml`) with price/volume/dollar-turnover + cap floors
- **Analyst rating policy** and **TradingView profiles**
- **GitHub Actions** daily runner (skeleton) and a small Python runner

## How to use
1. Drop these files into your repo at the same paths.
2. (Optional) Edit `config/regions.yaml` if you want different floors per country.
3. Run locally:
   ```bash
   python scripts/vega_unisearch_runner.py --region US --profile SmartMoney_NA_Level2
   ```
4. Enable the GitHub Action (`.github/workflows/vega_unisearch.yml`).

> NOTE: This runner is a **skeleton** (no live market data). In your Vega app, wire the rule YAMLs
> to your data client (Polygon/IBKR/TradingView) and the Smart Money A-to-Z filters you already use.

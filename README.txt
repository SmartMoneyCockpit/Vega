# Vega ↦ TradingView One-and-Done

**Flow:** IBKR → Vega (compute) → TradingView (display).
This package gives you export buttons and deep links to TradingView.

## Files
- `services/tradingview_exports.py` — helpers to create TXT/CSV exports and deeplinks.
- `pages/TradingView_Exports.py` — Streamlit page with buttons and links.
- `components/tv_embed.py` — optional inline TradingView chart preview.
- `utils/picks_bridge.py` — seeds demo picks from `templates/sample_picks.json` if none present.
- `exports/` — output folder for generated TXT/CSV files.

## Wiring to your pipeline
Populate `st.session_state['NA_picks']`, `['EU_picks']`, `['APAC_picks']` with a list of dicts:
```python
picks = [{
  "symbol": "AMZN", "exchange": "NASDAQ", "side": "BUY",
  "entry": 181.5, "stop": 174.0, "target1": 195.0, "target2": 205.0,
  "rr": "1:3.1", "reason_tags": "Momentum;RS>SPY", "notes": ""
}]
st.session_state['NA_picks'] = picks
```
Then open the **TradingView Export & Launch** page.

## Outputs
- `exports/tv_watchlist_<REGION>.txt` — import into TradingView as a watchlist.
- `exports/tv_trades_<REGION>.csv` — trade cards for notes/records (with `tv_url` column).
- `exports/tv_links_<REGION>.csv` — quick open links for charts.

## Optional: Authenticated heatmaps
No secrets required for this basic flow. Authenticated heatmaps can be added later.

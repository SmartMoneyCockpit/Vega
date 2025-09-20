
## Mega Bundle Delta (Unified)
- Snapshot export button: `components/snapshot_export.py` and hook in Morning Report.
- A+ daily digest script via SendGrid: `scripts/sendgrid_digest.py` + `configs/sendgrid.yaml`.
- TradingView authenticated sector heatmap with public fallback: `components/tradingview_heatmap.py`.
- Sector Flip Alerts skeleton: `modules/alerts/sector_flip.py` (hook-ready).
- Polling policy config + helper: `configs/polling.yaml`, `modules/polling.py`.
- Embedded 37 standing rules: `docs/rulepack/standing_rules_37.md`.
- (Includes prior VectorVest upgrades: metrics table, VST calc, trendlines, EPS/Growth/Sales Growth charts, sparklines.)


- Added GitHub Actions:
  - `.github/workflows/daily_sendgrid_digest.yml` @ 12:45 PT (19:45 UTC).
  - `.github/workflows/morning_snapshot.yml` @ 07:45 PT (14:45 UTC).
- Added `scripts/morning_snapshot.py` to generate a vault snapshot without Streamlit.

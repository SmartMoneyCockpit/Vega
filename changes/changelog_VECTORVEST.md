## VectorVest Metrics Upgrade (Weekly Delta)
- Added `modules/vectorvest_utils.py` with compute/merge helpers and VST calculation (weights from `_vega_scores.yaml`, default 0.4/0.3/0.3).
- Upgraded `modules/vectorvest_panel.py` to display full VV columns, including RT, RV, RS, VST, CI, EPS, Growth, and Sales Growth when present.
- Added `render_vectorvest_metrics()` section in `modules/morning_report.py` to show a watchlist snapshot with VV metrics.
- Added `components/vst_trend.py` and a VST Trend **preview** selector inside Morning Report VectorVest section (26w lookback with 4w/12w MAs, bands, flip annotations).

- Added `components/metric_trends.py` for EPS, Earnings Growth, Sales Growth trends (26w, MAs).
- Added `components/sparklines.py` and DataFrame image-based sparklines for VST/EPS/Growth/Sales Growth.
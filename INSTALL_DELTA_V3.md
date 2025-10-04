# Vega Cockpit — Delta v3 (Accordion + Auto-Discovery + Fixed Menu + Wrappers)

This delta is **non-destructive**. It adds new files; nothing is overwritten.

## Added
- `app_menu_refactor_advanced.py` — advanced entrypoint
- `core/registry.py`, `core/autoreg.py`, `core/search.py`, `core/menu_config.py`,
  `core/nav_adv.py`, `core/breadcrumbs.py`
- `pages/real_time_scanner_wrapper.py`
- `pages/markets/north_america_wrapper.py`, `pages/markets/apac_wrapper.py`, `pages/markets/europe_wrapper.py`
  (wrappers try multiple candidate module names and will render once legacy files are present)
- `menu_config.yaml` — pins Markets & Tools routes to the top
- `.streamlit/config.toml` — binds to 0.0.0.0 (port comes from Start Command)

## Start Command (Render)
```bash
PYTHONPATH=/opt/render/project/src:$PYTHONPATH streamlit run app_menu_refactor_advanced.py --server.port $PORT --server.address 0.0.0.0
```

## Notes from scan
We scanned your repo to pre-wire routes. Found TradingView-related candidate modules:
```
[
  "Vega-main/View_Exports.py",
  "Vega-main/auto_hedging_engine.py",
  "Vega-main/data_bridge.py",
  "Vega-main/db_adapter.py",
  "Vega-main/monitor_vol_hedge.py",
  "Vega-main/report_apac.py",
  "Vega-main/report_eod.py",
  "Vega-main/report_midday.py",
  "Vega-main/report_na.py",
  "Vega-main/sheets_client.py",
  "Vega-main/tradingview_embed.py",
  "Vega-main/utils.py",
  "Vega-main/warm_cache.py",
  "Vega-main/components/tradingview_heatmap.py",
  "Vega-main/components/tv_bridge.py",
  "Vega-main/components/tv_embed.py",
  "Vega-main/components/ui_overrides.py",
  "Vega-main/filters/tradable.py",
  "Vega-main/modules/apac_dashboard.py",
  "Vega-main/modules/daily_briefing.py",
  "Vega-main/modules/data_providers.py",
  "Vega-main/modules/etf_dashboard.py",
  "Vega-main/modules/morning_report.py",
  "Vega-main/modules/sector_heatmap.py",
  "Vega-main/modules/spy_contra_tracker.py",
  "Vega-main/modules/tariff_aware_screener.py",
  "Vega-main/modules/ui/focus_chart.py",
  "Vega-main/modules/utils/tv_links.py",
  "Vega-main/pages/01_RealTime_Scanner.py",
  "Vega-main/scripts/agent_tv_guard.py",
  "Vega-main/scripts/auto_hedging_engine.py",
  "Vega-main/scripts/color_guard.py",
  "Vega-main/scripts/color_guard_apac.py",
  "Vega-main/scripts/color_guard_europe.py",
  "Vega-main/scripts/econ_calendar.py",
  "Vega-main/scripts/econ_calendar_apac.py",
  "Vega-main/scripts/econ_calendar_europe.py",
  "Vega-main/scripts/export_digest.py",
  "Vega-main/scripts/generate_etf_tactical_cache.py",
  "Vega-main/scripts/morning_report_apac.py",
  "Vega-main/scripts/morning_report_europe.py",
  "Vega-main/scripts/sector_flip_scan.py",
  "Vega-main/scripts/seed_db.py",
  "Vega-main/scripts/tv_push.py",
  "Vega-main/scripts/uptime_ping_apac.py",
  "Vega-main/scripts/uptime_ping_europe.py",
  "Vega-main/scripts/vega_unisearch_runner.py",
  "Vega-main/services/tradingview_exports.py",
  "Vega-main/src/app.py",
  "Vega-main/src/config_schema.py",
  "Vega-main/src/providers.py",
  "Vega-main/src/components/tv_bridge.py",
  "Vega-main/src/components/vega_sections.py",
  "Vega-main/src/integrations/tv_connect.py",
  "Vega-main/src/modules/ui/focus_chart.py",
  "Vega-main/src/modules/utils/tv_links.py",
  "Vega-main/src/pages/00_Home.py",
  "Vega-main/src/pages/01_North_America_Text_Dashboard.py",
  "Vega-main/src/pages/01_Scanner_OnDemand.py",
  "Vega-main/src/pages/02_APAC_Text_Dashboard.py",
  "Vega-main/src/pages/02_Europe_Text_Dashboard.py",
  "Vega-main/src/pages/05_TradingView_Charts.py",
  "Vega-main/src/pages/06_Vega_Native_Chart.py",
  "Vega-main/src/pages/10_IBKR_Scanner.py",
  "Vega-main/src/pages/10_TradingView_Bridge.py",
  "Vega-main/src/pages/99_Diagnostics.py",
  "Vega-main/src/panels/apac_tradingview_panel.py",
  "Vega-main/utils/picks_bridge.py",
  "Vega-main/utils/risk_regime.py",
  "Vega-main/utils/tradingview.py",
  "Vega-main/vega/tradingview.py",
  "Vega-main/vega/tv_heatmap.py",
  "Vega-main/workers/alerts/sector_flip_from_snapshots.py",
  "Vega-main/workers/providers/csv_sources.py",
  "Vega-main/workers/reports/build_region_reports.py",
  "Vega-main/workers/snapshots/daily_scorecard_export.py",
  "Vega-main/workers/snapshots/market_snapshot.py"
]
```
(If your NA/APAC/Europe pages are not present yet, wrappers will activate automatically when you add them.)

## Local test
```bash
streamlit run app_menu_refactor_advanced.py
```

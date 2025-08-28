# Vega Cockpit — Trading Roadmap (Source of Truth)

**Owner:** Blaine Dares  
**Last updated:** 2025-08-27  
**Status Key:** ✅ Done · 🔄 In progress · ⏳ Planned

## A. Core Platform
- ✅ Streamlit import order fixed
- ✅ Safe import guard for `render_stay_or_reenter`
- ✅ Readable dark theme
- ✅ PDF export guard
- 🔄 Weekly module drops (Mondays)
- ⏳ Auto-vaulting & secrets rotation
- ⏳ Render health watchdog

## B. Trading Modules
- ✅ Stay Out vs Get Back In (this module)
- 🔄 PnL & Risk Panel
- 🔄 AI Trade Quality Scorecard
- 🔄 Auto-Journal Generator
- ⏳ Backtest Mode
- ⏳ Capital Exposure Guardrails
- ⏳ Auto-Hedging Engine
- ⏳ Pattern Profiler
- ⏳ Global Risk Heatmap

## C. Market Dashboards
- ⏳ VectorVest-style USA/Canada/Mexico
- ⏳ Morning (NA) & Evening (APAC) reports
- ⏳ APAC TV chart embeds

## D. Rules & Policies
- ✅ “No buys within 30 days of earnings” honored by logic
- ✅ Contras/hedges visible only in risk-off (policy)
- ⏳ VIX > 20 defensive overlay trigger
- ⏳ FX impact scan for Canadian tickers

## E. Alerts
- ✅ Email alert formatter + SMTP helper
- ✅ Email alerts on flips
- ❌ Webhooks/Discord/Slack (not desired now)

## Source of Truth
- Code + roadmap in GitHub. Render deploys from GitHub.

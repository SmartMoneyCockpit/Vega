# Vega Cockpit — Trading Roadmap (Source of Truth)

**Owner:** Blaine Dares  
**Last updated:** 2025-08-27  
**Status Key:** ✅ Done · 🔄 In progress · ⏳ Planned · 🧪 Experimental · 🧯 Hotfix

## Vision
A self-contained trading cockpit (Render/GitHub) with daily automation, weekly module drops, and a persistent record of approvals and changes.

## A. Core Platform
- ✅ Streamlit import order fixed (`st.set_page_config` after import)
- ✅ `utils.prefs_bootstrap` shim to load prefs cleanly
- ✅ Safe import guard for `render_stay_or_reenter` + tab mounting
- ✅ Lighter dark theme via `.streamlit/config.toml`
- ✅ PDF export guard (`fpdf2` optional, friendly warning)
- 🔄 Weekly module-drop cadence (Mondays)
- ⏳ Auto-vaulting & secrets rotation
- ⏳ Render health watchdog + recovery actions

## B. Trading Modules
- ✅ **Stay Out vs Get Back In** decision module (logging, CSV/Sheets, alerts, PDF)
- 🔄 **PnL & Risk Breakdown Panel** (per trade/week/strategy)
- 🔄 **AI Trade Quality Scorecard**
- 🔄 **Auto-Journal Generator** (daily trade summaries)
- ⏳ **Backtest Mode**
- ⏳ **Capital Exposure Guardrails**
- ⏳ **Auto-Hedging Engine** (SPXU/SQQQ/RWM when risk-off)
- ⏳ **Pattern Profiler**
- ⏳ **Global Risk Heatmap**

## C. Market Dashboards
- ⏳ VectorVest-style dashboards (USA / Canada / Mexico)
- ⏳ NA Morning & APAC Evening reports (macro calendars)
- ⏳ APAC index TV charts (RSI/SMA/EMA) saved + embedded

## D. Rules & Standing Policies
- ✅ “No buys within 30 days of earnings”
- ✅ Contras/hedges shown only in clear risk-off regimes
- ✅ Canadian stock reviews: Tariff Exposure Grade (🟢🟠🔴), USMCA status, Smart Money Grade, Action Plan
- ⏳ VIX > 20 defensive overlay trigger
- ⏳ FX impact scan for Canadian tickers (USDMXN/USDCAD divergence)

## E. Alerts & Integrations
- ✅ Email formatter for Defensive Mode (clear subject/body + thresholds + actions)
- ✅ Robust SMTP helper with retries & validation
- ❌ Discord/webhook alerts (not requested)
- ✅ Module crash alerts (Email only)

## Today’s Approvals (2025-08-27)
- ✅ Finalize **Stay Out vs Get Back In** imports/guards/theme.
- ✅ Add **email alert formatter** & **safe_send_email** helper.
- ✅ Create **ROADMAP.md** as the master record.
- 🔄 Prepare **Batch Trading-#1**: PnL Panel, Scorecard, Auto-Journal (stocks only).

## Cadence
- **Weekly Module Drop:** Mondays  
- **Docs to update each drop:** ROADMAP.md, CHANGELOG.md

## Source of Truth
- Code + roadmap in GitHub. Render deploys from GitHub.

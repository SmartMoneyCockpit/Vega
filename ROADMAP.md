# Vega Cockpit — Trading Roadmap (Source of Truth)

**Owner:** Blaine Dares  
**Last updated:** 2025-08-27  
**Status Key:** ✅ Done · 🔄 In progress · ⏳ Planned · 🧪 Experimental · 🧯 Hotfix

---

## Vision
A self-contained **trading cockpit** (Render/GitHub) with daily automation, weekly module drops, and a persistent record of approvals and changes. This file is the **official manifest** of what exists, what’s queued, and what’s next.

---

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
- ⏳ **PnL & Risk Breakdown Panel** (per trade/week/strategy)
- ⏳ **AI Trade Quality Scorecard**
- ⏳ **Backtest Mode** (simulated runs without journal impact)
- ⏳ **Capital Exposure Guardrails** (sector/strategy limits)
- ⏳ **Auto-Hedging Engine** (SPXU/SQQQ/RWM when risk-off)
- ⏳ **Auto-Journal Generator** (daily trade summaries)
- ⏳ **Pattern Profiler** (frequent winner setup detector)
- ⏳ **Global Risk Heatmap** (vol, FX, geo overlays)

## C. Market Dashboards
- ⏳ VectorVest-style dashboards (USA / Canada / Mexico)
- ⏳ NA Morning & APAC Evening reports (template + macro calendar)
- ⏳ APAC index TV charts (RSI/SMA/EMA) save + embed

## D. Rules & Standing Policies
- ✅ “No buys within 30 days of earnings”
- ✅ Contras/hedges shown only in clear risk-off regimes
- ✅ Canadian stock reviews: Tariff Exposure Grade (🟢🟠🔴), USMCA status, Smart Money Grade, Action Plan
- ⏳ VIX > 20 defensive overlay trigger
- ⏳ FX impact scan for Canadian tickers (USDMXN/USDCAD divergence)

## E. Alerts & Integrations
- ✅ Email formatter for Defensive Mode (clear subject/body + thresholds + actions)
- ✅ Robust SMTP helper with retries & validation
- ⏳ Webhook (Discord) mirror for key flips

---

## Today’s Approvals (2025-08-27)
- ✅ Finalize **Stay Out vs Get Back In** imports/guards/theme.
- ✅ Add **email alert formatter** & **safe_send_email** helper.
- ✅ Create **ROADMAP.md** as the master record.
- ⏳ Prepare **Batch Trading-#1**: PnL Panel, Scorecard, Auto-Journal.

---

## Cadence
- **Weekly Module Drop:** Mondays
- **Docs to update each drop:** ROADMAP.md (status), CHANGELOG.md (diff), any new config.

---

## Ownership & Source of Truth
- Code + roadmap live in **GitHub**.  
- Render deploys from GitHub.  
- If it’s not in this roadmap, it is not approved or it’s not scheduled.

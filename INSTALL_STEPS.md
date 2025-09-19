# Vega → TradingView One-and-Done Installation

**Flow:** IBKR → Vega (compute) → TradingView (display). No inbound data from TradingView.

## Step 1 — Copy files into your Vega repo
- Unzip this package.
- Option A (Windows): right-click `scripts/copy_to_repo.ps1` → Run with PowerShell  
  Example: `./scripts/copy_to_repo.ps1 -Dest "C:\\Users\\you\\code\\Vega"`
- Option B (Mac/Linux): `bash scripts/copy_to_repo.sh /path/to/your/Vega`
- Option C: Manually copy folders into the repo root: `services/`, `components/`, `utils/`, `pages/`, `templates/`, `exports/`.

**Reply “Step 1 done” once copied.**

---

## Step 2 — Wire your A-to-Z outputs to the page
In your pipeline where picks are finalized, add (per region):

```python
from services.pipeline_wire import publish_picks

publish_picks("NA", na_picks)    # list[dict]
publish_picks("EU", eu_picks)    # list[dict]
publish_picks("APAC", apac_picks)
```

Each dict should include:
`symbol, exchange, side, entry, stop, target1, target2, rr, reason_tags, notes`

- Missing `exchange` → assumed **US** (bare ticker).
- Exchange codes auto-normalized (e.g., `TSE → TSX`, `NASD → NASDAQ`).

**Reply “Step 2 done” once wired.**

---

## Step 3 — Run and verify locally
Launch Streamlit and open the page:
```bash
streamlit run app.py
```
In the sidebar: **TradingView Export & Launch**

Expect:
- Table of picks per region.
- Buttons: **Export Watchlist**, **Export Trades**, **Export Links**.
- **Open All in TradingView** button (opens tabs; allow popups once).
- **Inline TradingView Preview** (expander).

**Reply “Step 3 done” when you see the page.**

---

## Step 4 — Import into TradingView
- In TradingView, open Watchlists → **Import** → select `exports/tv_watchlist_<REGION>.txt`.
- (Optional) Keep `tv_trades_<REGION>.csv` for your notes/archive.
- You can also use **Open in TradingView** links or the **Open All** button for quick visual checks.

**Reply “Step 4 done” after import.**

---

## Step 5 — CI/CD note (optional)
Per your choice, exports are **manual only**. If later you want them attached as CI artifacts, I’ll add a small job that copies `exports/*.csv|*.txt` to GitHub Actions artifacts.

---

## Troubleshooting
- Page empty? Use the included sample data first (Step 3) — it auto-seeds if no picks in `session_state`.
- Wrong exchange prefix? We normalize common codes; you can pass the exact code you want (e.g., `BMV`, `TSX`, `NYSE`).

**Done.** From here, your daily flow is unchanged — IBKR feeds Vega → Vega computes → you export and/or deep-link to TradingView.

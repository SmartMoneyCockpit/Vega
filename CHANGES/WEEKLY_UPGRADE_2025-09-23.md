# Weekly Upgrade – 2025-09-23 (Render ↔ Droplet IB Bridge)

**What's new (delta only):**
- **config.yaml**: `ibkr` block updated for droplet IP `167.71.145.48`, port `4002`, client `7`, delayed data.
- **src/ibkr_bridge.py**: ENV override support (`IB_HOST`, `IB_PORT`, `IB_CLIENT_ID`, `IB_MKT_TYPE`); TSX mapping; delayed quotes.
- **pages/900_IB_Feed_Status.py**: Streamlit diagnostics page with a one-click feed test & watchlist pull.
- **scripts/quick_test_ibkr.py**: CLI sanity test for US + TSX tickers.
- **docs/README-Render-IB.md**: render secrets + droplet firewall/API checklist.

**How to deploy:**
1) Upload these files to your repo at the same paths and push to GitHub (Render will redeploy).
2) Set secrets in Render as listed in the README (they override YAML automatically).
3) Ensure droplet `ufw` allows 4002/tcp and IB Gateway API settings match README.
4) Open the **IBKR Feed Status** page and click **Test Feed Now**.

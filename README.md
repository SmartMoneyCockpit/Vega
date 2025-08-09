
# Vega Cockpit — Day‑1 MVP

## Quickest Path (3 steps)
1) **Drop your service account key** in the project root as `credentials.json`.
2) **Run locally**:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
3) **Deploy on Render (blueprint)**:
   - Create a new Web Service using this repo and `render.yaml`.
   - After service is created, add a **Secret File** named `credentials.json` and paste the full JSON.
   - Open the URL; verify the Watchlist and Quick Log work with your Google Sheet.

## Notes
- Expects a Google Sheet with a tab named `COCKPIT`.
- Watchlist reads `A2:D50` → columns: Ticker | Strategy | Entry | Stop
- Quick Log appends `[timestamp, type, symbol, status, notes]` to the `COCKPIT` tab.

# Vega Handoff Package (Hands-Off Deploy)

This package is ready for **drag-and-drop** to GitHub. On push:
- CI runs a smoke check.
- If you set the `RENDER_DEPLOY_HOOK` GitHub secret, it triggers a Render deploy automatically.
- Or, let Render auto-deploy when it detects a new commit on the watched branch.

## How to deploy
1. **Extract this ZIP** locally.
2. Open GitHub → your `Vega` repository → switch to the branch Render watches (`staging` or `main`).
3. Drag **all extracted files/folders** into the GitHub upload box and **Commit** with a message like:
   `Vega handoff upgrade – {today}`

### One-time setup (secrets)
- In **GitHub → Settings → Secrets and variables → Actions → New repository secret**:
  - `RENDER_DEPLOY_HOOK` = your Render Deploy Hook URL (optional but recommended).
- In **Render → Service → Settings → Environment** add your credentials (IBKR, TradingView, Polygon, SendGrid, etc).

### Files included
- `.github/workflows/ci-smoke.yml` – Python 3.11, installs deps, imports `app.py`/`main.py` to catch obvious errors.
- `.github/workflows/deploy-render.yml` – Calls Render Deploy Hook on every push to `main`/`staging`.
- `Procfile` – Ensures Streamlit runs with `$PORT` on Render.
- `render.yaml` – Optional Render blueprint (if you want to use "Blueprint Deploys").
- `.env.example` – Example env vars (do **not** commit real secrets).

### Notes
- This handoff **does not change your app code** beyond automation scaffolding. It cannot include unknown changes from your “1000-Q” session unless those were already integrated here. If you have a newer code ZIP, upload that instead; the workflows here will still work.

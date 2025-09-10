Vega Drop-in Delta — 2025-09-10 06:57 

What this includes
------------------
1) Robust Gmail mailer (tools/emailer.py) used by the app AND GitHub Actions.
2) IBKR safe client (tools/ibkr_client.py) + ibkr_charts wired without asyncio crashes.
3) Breadth panel backed by cache/fallback (tools/breadth.py) so it always renders.
4) One-Click Daily Report UI with recipient override, test send, and resend buttons.
5) Morning Report GitHub workflow that builds a PDF and emails it (secrets-based).
6) An inline-credentials workflow example if you insist (replace placeholders).

How to install
--------------
A. Unzip this archive at your REPO ROOT, preserving folders:
   tools/, modules/, .github/workflows/
B. Commit and push.
C. Render env (already set for you): VEGA_EMAIL_* (host/port/user/pass/to).
   Optional polish: MAIL_FROM="Vega Cockpit <your@gmail.com>".
D. GitHub → Settings → Secrets and variables → Actions:
     - MAIL_USER = your_gmail@gmail.com
     - MAIL_APP_PASSWORD = 16-char Gmail App Password
     - MAIL_TO = your_inbox@gmail.com
E. Actions → Morning Report (NA) → Run workflow → check your inbox.

Optional
--------
- If you prefer inline credentials temporarily, edit
  .github/workflows/morning_report_INLINE.yaml.example, replace __MAIL_*__ placeholders,
  rename to morning_report.yaml (and remove/disable the secrets-based one).
- IBKR: if you run TWS/Gateway elsewhere, set IB_HOST/IB_PORT/IB_CLIENT_ID in Render env.
- Breadth cache: monitors can write vault/cache/breadth.json; the UI will pick it up.
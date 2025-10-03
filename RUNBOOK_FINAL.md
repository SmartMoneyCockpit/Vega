# FINAL ONE-AND-DONE RUNBOOK

## Upload
1) Unzip this package into your repo root, commit, and push.

## Render (once)
2) Disks → Add 1 GB disk, mount to `/opt/render/project/src/data`.
3) Environment → Add `VEGA_DB_PATH=/opt/render/project/src/data/vega.db` → Save.

## Seed & Verify (one-time)
4) Jobs → New Job → Command: `python scripts/seed_db.py` → Run once.
5) Jobs → New Job → Command: `python scripts/verify_health.py` → Run once.

## Scheduled Jobs
6) Jobs → New Cron Job → `python scripts/export_digest.py` → `45 14 * * 1-5` (UTC).
7) Jobs → New Cron Job → `python scripts/rotate_snapshots.py` → `0 15 * * *` (UTC).
   - Add env on this job: `SNAPSHOT_KEEP_DAYS=90`, `SNAPSHOT_MAX_DISK_MB=900`
8) (Optional) Jobs → New Cron Job → `python scripts/sector_flip_scan.py` → `0 * * * 1-5` (UTC).

## Test
9) Open the app → Sidebar should show: Admin, Daily Digest, Breadth, RS Dashboard, Sector Alerts, System Status.
10) System Status page → confirm disk usage and timestamps appear after first export run.

## After TradingView Approval (Security Flip)
11) Environment → add `BASIC_AUTH_USER` / `BASIC_AUTH_PASS`.
12) Cloudflare → Enable Always Use HTTPS + HSTS; (optional) IP allow-list.

Done. No further steps required.

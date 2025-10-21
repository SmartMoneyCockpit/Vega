\
# Cleanup IBKR/TWS and Cloudflare artifacts (safe to re-run)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Join-Path $Root ".."

$targets = @(
  "src/ibkr_bridge",
  "cockpit_client/ib_bridge_client.py",
  "src/pages/095_IB_Feed_Status.py",
  "src/pages/096_IBKR_Ticker_ib.py",
  "src/pages/097_IBKR_Quick_Test_ib.py",
  "src/pages/10_IBKR_Scanner.py",
  "tools/ibkr_client.py",
  "utils/ib_client.py",
  "utils/ibkr.py",
  "utils/ibkr_client.py",
  "smoke_test_ib.py",
  "ibkr_test.py",
  "ibkr_health_api.py",
  "README_IBKR_CONN.md",
  "cloudflared.yml",
  "scripts/cloudflare*",
  "scripts/cloudflared*"
)

foreach ($t in $targets) {
  $p = Join-Path $Repo $t
  if (Test-Path $p) {
    Write-Host "Removing $p"
    Remove-Item $p -Recurse -Force -ErrorAction SilentlyContinue
  } else {
    Write-Host "Skip (missing): $p"
  }
}

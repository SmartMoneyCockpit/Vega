$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Join-Path $Root '..'
$p = Join-Path $Repo 'src/pages/IBKR_Ticker_ib.py'
if (Test-Path $p) { Remove-Item $p -Force -ErrorAction SilentlyContinue; Write-Host ('Removed ' + $p) } else { Write-Host ('Skip ' + $p) }
$p = Join-Path $Repo 'src/pages/IBKR_Quick_Test_ib.py'
if (Test-Path $p) { Remove-Item $p -Force -ErrorAction SilentlyContinue; Write-Host ('Removed ' + $p) } else { Write-Host ('Skip ' + $p) }
$p = Join-Path $Repo 'src/pages/IB_Feed_Status.py'
if (Test-Path $p) { Remove-Item $p -Force -ErrorAction SilentlyContinue; Write-Host ('Removed ' + $p) } else { Write-Host ('Skip ' + $p) }
$p = Join-Path $Repo 'src/pages/Bridge_Health_Test.py'
if (Test-Path $p) { Remove-Item $p -Force -ErrorAction SilentlyContinue; Write-Host ('Removed ' + $p) } else { Write-Host ('Skip ' + $p) }
$p = Join-Path $Repo 'src/pages/Not_Found.py'
if (Test-Path $p) { Remove-Item $p -Force -ErrorAction SilentlyContinue; Write-Host ('Removed ' + $p) } else { Write-Host ('Skip ' + $p) }
$p = Join-Path $Repo 'src/pages/all_pages.py'
if (Test-Path $p) { Remove-Item $p -Force -ErrorAction SilentlyContinue; Write-Host ('Removed ' + $p) } else { Write-Host ('Skip ' + $p) }
$p = Join-Path $Repo 'src/pages/real_time_scanner_wrapper.py'
if (Test-Path $p) { Remove-Item $p -Force -ErrorAction SilentlyContinue; Write-Host ('Removed ' + $p) } else { Write-Host ('Skip ' + $p) }
$p = Join-Path $Repo 'src/pages/RS_Dashboard.py'
if (Test-Path $p) { Remove-Item $p -Force -ErrorAction SilentlyContinue; Write-Host ('Removed ' + $p) } else { Write-Host ('Skip ' + $p) }
$p = Join-Path $Repo 'src/pages/IBKR_Scanner.py'
if (Test-Path $p) { Remove-Item $p -Force -ErrorAction SilentlyContinue; Write-Host ('Removed ' + $p) } else { Write-Host ('Skip ' + $p) }
param(
  [string]$Dest = "."
)
$ErrorActionPreference = "Stop"
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Join-Path $src ".."
$root = (Resolve-Path $root).Path
Write-Host "Copying to: $Dest"
New-Item -ItemType Directory -Force -Path "$Dest/services","$Dest/components","$Dest/utils","$Dest/pages","$Dest/templates","$Dest/exports" | Out-Null
Copy-Item "$root/services/*.py" "$Dest/services" -Force
Copy-Item "$root/components/*.py" "$Dest/components" -Force
Copy-Item "$root/utils/*.py" "$Dest/utils" -Force
Copy-Item "$root/pages/*.py" "$Dest/pages" -Force
Copy-Item "$root/templates/*.json" "$Dest/templates" -Force
Copy-Item "$root/exports/.gitkeep" "$Dest/exports/.gitkeep" -Force -ErrorAction SilentlyContinue
Write-Host "Done. Launch Streamlit and open 'TradingView Export & Launch' page."

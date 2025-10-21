\
param(
  [string]$ZipPath = ".\Vega_delta_Weekly_Upgrade_2025-10-21.zip"
)
Write-Host "Applying weekly upgrade from $ZipPath"
Expand-Archive -Path $ZipPath -DestinationPath . -Force
Write-Host "Done. Consider: git add .; git commit; git push"

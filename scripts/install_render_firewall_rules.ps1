
# scripts/install_render_firewall_rules.ps1
Param([int]$Port = 7496)
$rules = @(
  @{ Name="IBKR Render 44.229.227.142"; Address="44.229.227.142" },
  @{ Name="IBKR Render 54.188.71.94" ; Address="54.188.71.94" },
  @{ Name="IBKR Render 52.13.128.188"; Address="52.13.128.188" },
  @{ Name="IBKR Render 74.220.48.0-24"; Address="74.220.48.0/24" },
  @{ Name="IBKR Render 74.220.56.0-24"; Address="74.220.56.0/24" }
)
foreach ($r in $rules) {
  if (-not (Get-NetFirewallRule -DisplayName $r.Name -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $r.Name -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -RemoteAddress $r.Address | Out-Null
    Write-Output "Added rule: $($r.Name) -> $($r.Address):$Port"
  } else {
    Write-Output "Rule exists: $($r.Name)"
  }
}

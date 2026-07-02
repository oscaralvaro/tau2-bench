$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$policy = Join-Path $root 'data\tau2\domains\restaurante_joaquin_cachay\policy.md'
$baseline = Join-Path $root 'data\tau2\domains\restaurante_joaquin_cachay\prompts\policy_e3_baseline.md'

Copy-Item $baseline $policy -Force
Write-Host 'policy_e3_baseline.md restaurado en policy.md'


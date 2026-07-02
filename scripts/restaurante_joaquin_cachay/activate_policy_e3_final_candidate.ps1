$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$policy = Join-Path $root 'data\tau2\domains\restaurante_joaquin_cachay\policy.md'
$exp = Join-Path $root 'data\tau2\domains\restaurante_joaquin_cachay\prompts\policy_e3_final_candidate.md'

Copy-Item $exp $policy -Force
Write-Host 'policy_e3_final_candidate.md activado en policy.md'

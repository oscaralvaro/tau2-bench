$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$domainSimDir = Join-Path $root 'data\tau2\domains\restaurante_joaquin_cachay\simulations'
$source = Join-Path $root 'data\simulations\sim_e3_baseline.json'
$targetA = Join-Path $root 'data\simulations\sim_e4_A_baseline.json'
$targetDomain = Join-Path $domainSimDir 'sim_e4_A_baseline.json'

if (-not (Test-Path $source)) {
    throw "No se encontro el baseline de E3 en: $source"
}

New-Item -ItemType Directory -Force -Path $domainSimDir | Out-Null
Copy-Item $source $targetA -Force
Copy-Item $source $targetDomain -Force

Write-Host 'sim_e4_A_baseline.json creado desde sim_e3_baseline.json'

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("B", "C", "D")]
    [string]$Condicion,

    [ValidateSet("headers", "fixed_200")]
    [string]$EstrategiaD = "headers"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$envPath = Join-Path $repoRoot ".env"
if (-not (Test-Path $envPath)) {
    throw "No se encontro .env en la raiz del repositorio."
}

Get-Content $envPath | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"').Trim("'")
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

if (-not $env:GEMINI_API_KEY -and $env:GOOGLE_API_KEY) {
    $env:GEMINI_API_KEY = $env:GOOGLE_API_KEY
}
if (-not $env:GOOGLE_API_KEY -and $env:GEMINI_API_KEY) {
    $env:GOOGLE_API_KEY = $env:GEMINI_API_KEY
}
if (-not $env:GEMINI_API_KEY) {
    throw "No se encontro GEMINI_API_KEY ni GOOGLE_API_KEY en .env."
}

$strategy = switch ($Condicion) {
    "B" { "headers" }
    "C" { "fixed_200" }
    "D" { $EstrategiaD }
}
$useThink = $Condicion -eq "D"
$saveName = switch ($Condicion) {
    "B" { "sim_e4_B_headers_k3" }
    "C" { "sim_e4_C_fixed200_k3" }
    "D" { "sim_e4_D_${strategy}_k3_think" }
}

$llmArgs = '{\"temperature\":0.0,\"rate_limit_requests_per_minute\":14,\"rate_limit_requests_per_day\":14000,\"rate_limit_tokens_per_minute\":150000,\"rate_limit_bucket\":\"gemma4-free-tier-e4\",\"rate_limit_token_reserve\":750}'
$envArgs = @{
    chunking_strategy = $strategy
    retrieval_k = 3
    use_think = $useThink
} | ConvertTo-Json -Compress
$envArgs = $envArgs.Replace('"', '\"')

Write-Host "Condicion: $Condicion"
Write-Host "Estrategia: $strategy"
Write-Host "Think: $useThink"
Write-Host "Archivo: data/simulations/$saveName.json"

# Las respuestas permiten reanudar aunque el checkpoint tenga un commit anterior.
"y`ny`ny" | python -m tau2.cli run `
    --domain divemotor_santiago `
    --agent-llm gemini/gemma-4-26b-a4b-it `
    --user-llm gemini/gemma-4-26b-a4b-it `
    --task-ids 1 3 7 10 11 12 14 15 18 19 `
    --num-trials 5 `
    --max-steps 30 `
    --max-concurrency 1 `
    --save-to $saveName `
    --agent-llm-args $llmArgs `
    --user-llm-args $llmArgs `
    --env-args $envArgs `
    --log-level WARNING

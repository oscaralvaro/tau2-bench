$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$domainSimDir = Join-Path $root 'data\tau2\domains\restaurante_joaquin_cachay\simulations'
$logDir = Join-Path $root 'data\logs\restaurante_joaquin_cachay'
Set-Location $root
New-Item -ItemType Directory -Force -Path $domainSimDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$stdoutLog = Join-Path $logDir "run_e4_C_fixed_k3_${timestamp}.stdout.log"
$stderrLog = Join-Path $logDir "run_e4_C_fixed_k3_${timestamp}.stderr.log"
$stdinFile = Join-Path $logDir "run_e4_C_fixed_k3_${timestamp}.stdin.txt"
Set-Content -Path $stdinFile -Value "y`r`ny`r`n" -Encoding ASCII

$agentArgs = @{
    temperature = 0.0
    timeout = 600
    num_retries = 0
    rate_limit_requests_per_minute = 6
    rate_limit_requests_per_day = 14000
    rate_limit_bucket = 'google-free-tier-26b'
    rate_limit_token_reserve = 750
    rate_limit_429_max_retries = 0
} | ConvertTo-Json -Compress
$agentArgsEscaped = $agentArgs.Replace('"', '\"')

$userArgs = @{
    temperature = 0.0
    timeout = 600
    num_retries = 0
    rate_limit_requests_per_minute = 6
    rate_limit_requests_per_day = 14000
    rate_limit_bucket = 'google-free-tier-26b'
    rate_limit_token_reserve = 750
    rate_limit_429_max_retries = 0
} | ConvertTo-Json -Compress
$userArgsEscaped = $userArgs.Replace('"', '\"')

$envArgs = @{
    use_rag = $true
    chunking_strategy = 'fixed_200'
    retrieval_k = 3
    use_think = $false
} | ConvertTo-Json -Compress
$envArgsEscaped = $envArgs.Replace('"', '\"')

$arguments = @(
    '-X', 'utf8',
    '-m', 'tau2.cli',
    'run',
    '--domain', 'restaurante_joaquin_cachay',
    '--agent-llm', 'gemini/gemma-4-26b-a4b-it',
    '--user-llm', 'gemini/gemma-4-26b-a4b-it',
    '--task-split-name', 'base_top10hard',
    '--num-trials', '5',
    '--max-steps', '30',
    '--max-errors', '10',
    '--max-concurrency', '1',
    '--seed', '300',
    '--save-to', 'sim_e4_C_fixed_k3',
    '--agent-llm-args', $agentArgsEscaped,
    '--user-llm-args', $userArgsEscaped,
    '--env-args', $envArgsEscaped
)

$process = Start-Process `
    -FilePath 'py' `
    -ArgumentList $arguments `
    -NoNewWindow `
    -Wait `
    -PassThru `
    -RedirectStandardInput $stdinFile `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog
if ($process.ExitCode -ne 0) {
    Write-Host "STDOUT log: $stdoutLog"
    Write-Host "STDERR log: $stderrLog"
    throw "La corrida E4 C fallo con exit code $($process.ExitCode)."
}

$sourceJson = Join-Path $root 'data\simulations\sim_e4_C_fixed_k3.json'
if (-not (Test-Path $sourceJson)) {
    Write-Host "STDOUT log: $stdoutLog"
    Write-Host "STDERR log: $stderrLog"
    throw "No se genero el archivo esperado: $sourceJson"
}

Copy-Item $sourceJson (Join-Path $domainSimDir 'sim_e4_C_fixed_k3.json') -Force
Write-Host "STDOUT log: $stdoutLog"
Write-Host "STDERR log: $stderrLog"

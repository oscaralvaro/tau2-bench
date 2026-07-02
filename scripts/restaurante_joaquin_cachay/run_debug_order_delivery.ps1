$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$logDir = Join-Path $root 'data\logs\restaurante_joaquin_cachay'
Set-Location $root
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$stdoutLog = Join-Path $logDir "run_debug_order_delivery_${timestamp}.stdout.log"
$stderrLog = Join-Path $logDir "run_debug_order_delivery_${timestamp}.stderr.log"
$saveTo = "sim_debug_order_delivery_after_fix_${timestamp}"

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

$arguments = @(
    '-X', 'utf8',
    '-m', 'tau2.cli',
    'run',
    '--domain', 'restaurante_joaquin_cachay',
    '--agent-llm', 'gemini/gemma-4-26b-a4b-it',
    '--user-llm', 'gemini/gemma-4-26b-a4b-it',
    '--task-ids', 'restaurant_order_delivery_1',
    '--num-trials', '1',
    '--max-steps', '200',
    '--max-errors', '10',
    '--max-concurrency', '1',
    '--seed', '300',
    '--save-to', $saveTo,
    '--agent-llm-args', $agentArgsEscaped,
    '--user-llm-args', $userArgsEscaped
)

$process = Start-Process `
    -FilePath 'py' `
    -ArgumentList $arguments `
    -NoNewWindow `
    -Wait `
    -PassThru `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog
if ($process.ExitCode -ne 0) {
    Write-Host "STDOUT log: $stdoutLog"
    Write-Host "STDERR log: $stderrLog"
    throw "La corrida debug de order delivery fallo con exit code $($process.ExitCode)."
}

Write-Host "STDOUT log: $stdoutLog"
Write-Host "STDERR log: $stderrLog"
Write-Host "Save to: $saveTo"

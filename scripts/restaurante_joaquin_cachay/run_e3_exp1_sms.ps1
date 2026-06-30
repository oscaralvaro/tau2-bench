$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$logDir = Join-Path $root 'data\logs\restaurante_joaquin_cachay'
Set-Location $root
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$policy = Join-Path $root 'data\tau2\domains\restaurante_joaquin_cachay\policy.md'
$baseline = Join-Path $root 'data\tau2\domains\restaurante_joaquin_cachay\prompts\policy_e3_baseline.md'
$exp = Join-Path $root 'data\tau2\domains\restaurante_joaquin_cachay\prompts\policy_e3_exp1.md'
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$stdoutLog = Join-Path $logDir "run_e3_exp1_sms_${timestamp}.stdout.log"
$stderrLog = Join-Path $logDir "run_e3_exp1_sms_${timestamp}.stderr.log"

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
    '--task-ids', 'restaurant_sms_reservation_cancel_1', 'restaurant_sms_reservation_cancel_wrong_code_1', 'restaurant_sms_role_validation_mismatch_1',
    '--num-trials', '5',
    '--max-steps', '200',
    '--max-errors', '10',
    '--max-concurrency', '1',
    '--seed', '300',
    '--save-to', 'sim_e3_exp1_sms_identity',
    '--agent-llm-args', $agentArgsEscaped,
    '--user-llm-args', $userArgsEscaped
)

try {
    Copy-Item $exp $policy -Force
    Write-Host 'policy_e3_exp1.md activado en policy.md'

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
        throw "La corrida E3 exp1 fallo con exit code $($process.ExitCode)."
    }
    Write-Host "STDOUT log: $stdoutLog"
    Write-Host "STDERR log: $stderrLog"
}
finally {
    Copy-Item $baseline $policy -Force
    Write-Host 'policy_e3_baseline.md restaurado en policy.md'
}

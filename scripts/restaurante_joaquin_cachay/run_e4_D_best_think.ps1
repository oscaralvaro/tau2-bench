$BestChunkingStrategy = if ($args.Count -gt 0 -and $args[0]) { $args[0] } else { 'headers' }

$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$domainSimDir = Join-Path $root 'data\tau2\domains\restaurante_joaquin_cachay\simulations'
$logDir = Join-Path $root 'data\logs\restaurante_joaquin_cachay'
Set-Location $root
New-Item -ItemType Directory -Force -Path $domainSimDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$stdoutLog = Join-Path $logDir "run_e4_D_best_think_${timestamp}.stdout.log"
$stderrLog = Join-Path $logDir "run_e4_D_best_think_${timestamp}.stderr.log"
$stdinFile = Join-Path $logDir "run_e4_D_best_think_${timestamp}.stdin.txt"
Set-Content -Path $stdinFile -Value "y`r`ny`r`n" -Encoding ASCII

$agentArgsJson = @{
    temperature = 0.0
    timeout = 600
    num_retries = 3
    rate_limit_requests_per_minute = 6
    rate_limit_requests_per_day = 14000
    rate_limit_bucket = 'google-free-tier-26b'
    rate_limit_token_reserve = 750
    rate_limit_429_max_retries = 0
} | ConvertTo-Json -Compress

$userArgsJson = @{
    temperature = 0.0
    timeout = 600
    num_retries = 3
    rate_limit_requests_per_minute = 6
    rate_limit_requests_per_day = 14000
    rate_limit_bucket = 'google-free-tier-26b'
    rate_limit_token_reserve = 750
    rate_limit_429_max_retries = 0
} | ConvertTo-Json -Compress

$envArgsJson = @{
    use_rag = $true
    chunking_strategy = $BestChunkingStrategy
    retrieval_k = 3
    use_think = $true
} | ConvertTo-Json -Compress

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
    '--save-to', 'sim_e4_D_best_think',
    '--agent-llm-args', $agentArgsJson,
    '--user-llm-args', $userArgsJson,
    '--env-args', $envArgsJson
)

function Quote-ProcessArgument([string]$argument) {
    if ($null -eq $argument) {
        return '""'
    }
    if ($argument.Length -eq 0) {
        return '""'
    }
    if ($argument -notmatch '[\s"]') {
        return $argument
    }
    $escaped = $argument -replace '(\\*)"', '$1$1\"'
    $escaped = $escaped -replace '(\\+)$', '$1$1'
    return '"' + $escaped + '"'
}

$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = 'py'
$startInfo.Arguments = (($arguments | ForEach-Object { Quote-ProcessArgument $_ }) -join ' ')
$startInfo.UseShellExecute = $false
$startInfo.RedirectStandardInput = $true
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.CreateNoWindow = $true

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $startInfo
[void]$process.Start()

$process.StandardInput.WriteLine('y')
$process.StandardInput.WriteLine('y')
$process.StandardInput.Close()

$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$process.WaitForExit()

Set-Content -Path $stdoutLog -Value $stdout -Encoding UTF8
Set-Content -Path $stderrLog -Value $stderr -Encoding UTF8

$exitCode = $process.ExitCode
if ($exitCode -ne 0) {
    Write-Host "STDOUT log: $stdoutLog"
    Write-Host "STDERR log: $stderrLog"
    throw "La corrida E4 D fallo con exit code $exitCode."
}

$sourceJson = Join-Path $root 'data\simulations\sim_e4_D_best_think.json'
if (-not (Test-Path $sourceJson)) {
    Write-Host "STDOUT log: $stdoutLog"
    Write-Host "STDERR log: $stderrLog"
    throw "No se genero el archivo esperado: $sourceJson"
}

Copy-Item $sourceJson (Join-Path $domainSimDir 'sim_e4_D_best_think.json') -Force
Write-Host "STDOUT log: $stdoutLog"
Write-Host "STDERR log: $stderrLog"

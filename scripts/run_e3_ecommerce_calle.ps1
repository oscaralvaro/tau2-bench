param(
    [string]$AgentLlm = "gemini/gemma-4-31b-it",
    [string]$UserLlm = "gemini/gemma-4-31b-it",
    [int]$NumTrials = 5,
    [int]$MaxConcurrency = 1,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $root "scripts\run_e3_ecommerce_calle.py"
$pythonExe = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "No se encontro python en $pythonExe"
}

if (-not (Test-Path $runner)) {
    throw "No se encontro el runner en $runner"
}

$args = @(
    $runner,
    "--agent-llm", $AgentLlm,
    "--user-llm", $UserLlm,
    "--num-trials", "$NumTrials",
    "--max-concurrency", "$MaxConcurrency"
)

if ($DryRun) {
    $args += "--dry-run"
}

& $pythonExe @args
exit $LASTEXITCODE

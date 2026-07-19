param(
    [string]$TotalTarget = "500",
    [Parameter(Mandatory = $true)]
    [string]$RunLabel,
    [Parameter(Mandatory = $true)]
    [int]$CaseOffset,
    [Parameter(Mandatory = $true)]
    [int]$CaseLimit,
    [string]$GenBatch = "5",
    [string]$JudgeBatch = "10",
    [string]$GenEffort = "low",
    [string]$JudgeEffort = "minimal"
)

$env:ASTERIA_SIMILARITY_TARGET = $TotalTarget
$env:ASTERIA_SIMILARITY_CASE_LIMIT = "$CaseLimit"
$env:ASTERIA_SIMILARITY_CASE_OFFSET = "$CaseOffset"
$env:ASTERIA_SIMILARITY_RUN_LABEL = $RunLabel
$env:ASTERIA_SIMILARITY_GEN_BATCH = $GenBatch
$env:ASTERIA_SIMILARITY_JUDGE_BATCH = $JudgeBatch
$env:ASTERIA_SIMILARITY_GEN_EFFORT = $GenEffort
$env:ASTERIA_SIMILARITY_JUDGE_EFFORT = $JudgeEffort
$env:ASTERIA_SIMILARITY_RESUME = "0"
$env:ASTERIA_SIMILARITY_INCLUDE_UPLOADED = "0"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonPath = Join-Path $ProjectRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonPath)) {
    $PythonPath = "python"
}

Set-Location $ProjectRoot
& $PythonPath -u "scripts\run_historical_similarity_eval.py"

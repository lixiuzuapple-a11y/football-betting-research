# EV-Lab TASK0048: research-only scheduled official post-match scoring.
# Requires Windows logged-in Administrator, original off-Git forecast roots.
# Existing cloud collector and TASK0046 pre-kickoff scheduler are not touched.
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$forward = 'E:\WebCodex-Workspace\EVLab-Data-Backups\task0046-forward-20261031'
$score = 'E:\WebCodex-Workspace\EVLab-Data-Backups\task0048-official-score'
$python = 'E:\WebCodex-Workspace\_evlab_task0036_sandbox\venv\Scripts\python.exe'
$exitCode = 2
$description = 'not invoked'
try {
    if (!(Test-Path -LiteralPath $python) -or !(Test-Path -LiteralPath (Join-Path $repo '.git')) -or
        !(Test-Path -LiteralPath (Join-Path $forward 'journal'))) {
        throw 'Missing original source repo/Python or immutable forward journal'
    }
    Set-Location -LiteralPath $repo
    & $python -m tools.task0048_scheduled_score --repo $repo --forward-base $forward --score-base $score
    $exitCode = $LASTEXITCODE
    $description = "python exit $exitCode"
}
catch {
    $exitCode = 2
    $description = $_.Exception.Message
}
finally {
    New-Item -ItemType Directory -Path (Join-Path $score 'scheduler') -Force | Out-Null
    $line = @{ invoked_at_utc = (Get-Date).ToUniversalTime().ToString('o')
               exit_code = $exitCode
               description = $description
               scheduled_task = 'EVLab-TASK0048-DailyOfficialScore' } | ConvertTo-Json -Compress
    Add-Content -LiteralPath (Join-Path $score 'scheduler\INVOCATIONS.jsonl') -Value $line -Encoding UTF8
}
exit $exitCode

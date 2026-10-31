# TASK0046: daily guarded prospective research run; no betting or market use.
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$base = 'E:\WebCodex-Workspace\EVLab-Data-Backups\task0046-forward-20261031'
$python = 'E:\WebCodex-Workspace\_evlab_task0036_sandbox\venv\Scripts\python.exe'
$identity = 'E:\WebCodex-Workspace\EVLab-Data-Backups\task0037-competitions-20261022\TASK0037-STRICT-CUP-IDENTITY.json'
$history = 'E:\WebCodex-Workspace\EVLab-Data-Backups\task0036-data-source-gate-20261022'
$exitCode = 2
$description = 'failed before Python invocation'
try {
    if (!(Test-Path -LiteralPath $python) -or !(Test-Path -LiteralPath $identity) -or
        !(Test-Path -LiteralPath (Join-Path $history 'hf_manifest.json'))) {
        throw 'Missing frozen EV-Lab Python, identity or historical source'
    }
    Set-Location -LiteralPath $repo
    $commit = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[a-fA-F0-9]{40}$') {
        throw 'Cannot pin code source Git commit'
    }
    & $python -m tools.task0046_forward_publication --repo $repo --evidence-base $base --identity $identity --history $history --source-commit $commit --mode publish
    $exitCode = $LASTEXITCODE
    $description = "python exit $exitCode"
}
catch {
    $description = $_.Exception.Message
    $exitCode = 2
}
finally {
    $logDir = Join-Path $base 'scheduler'
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    $record = @{ invoked_at_utc = (Get-Date).ToUniversalTime().ToString('o')
                 exit_code = $exitCode
                 description = $description
                 windows_scheduler = 'EVLab-TASK0046-DailyForward' } | ConvertTo-Json -Compress
    Add-Content -LiteralPath (Join-Path $logDir 'INVOCATIONS.jsonl') -Value $record -Encoding UTF8
}
exit $exitCode

# TASK0050: battery-safe, bounded-retry local research schedules.
# Does not recreate tasks, change credentials, triggers, Git preflight,
# publication deadlines, script actions, or run a bet.
$ErrorActionPreference = 'Stop'
$names = @('EVLab-TASK0046-DailyForward', 'EVLab-TASK0048-DailyOfficialScore')
foreach ($name in $names) {
    $before = Get-ScheduledTask -TaskName $name -ErrorAction Stop
    $actionBefore = @($before.Actions | ForEach-Object { $_.Execute + ' ' + $_.Arguments })
    $principalBefore = $before.Principal.UserId + '|' + $before.Principal.LogonType
    $triggersBefore = @($before.Triggers | ForEach-Object { $_.StartBoundary + '|' + $_.Enabled })
    $settings = $before.Settings
    $settings.DisallowStartIfOnBatteries = $false
    $settings.StopIfGoingOnBatteries = $false
    # A failed or interrupted instance may be retried twice at five-minute
    # intervals. Existing create-only journals and pre-kickoff Git checks
    # remain authoritative, so retries cannot silently double-publish.
    $settings.RestartCount = 2
    $settings.RestartInterval = 'PT5M'
    Set-ScheduledTask -TaskName $name -Settings $settings -ErrorAction Stop | Out-Null
    $after = Get-ScheduledTask -TaskName $name -ErrorAction Stop
    if ($after.Settings.DisallowStartIfOnBatteries -or
        $after.Settings.StopIfGoingOnBatteries -or
        $after.Settings.RestartCount -ne 2 -or
        $after.Settings.RestartInterval -ne 'PT5M' -or
        ($after.Principal.UserId + '|' + $after.Principal.LogonType) -ne $principalBefore -or
        ((@($after.Actions | ForEach-Object { $_.Execute + ' ' + $_.Arguments })) -join ';') -ne ($actionBefore -join ';') -or
        ((@($after.Triggers | ForEach-Object { $_.StartBoundary + '|' + $_.Enabled })) -join ';') -ne ($triggersBefore -join ';')) {
        throw "Scheduled task power-only policy verification failed: $name"
    }
    Write-Output ("VERIFIED " + $name + " battery_safe=true retries=2 interval=PT5M")
}

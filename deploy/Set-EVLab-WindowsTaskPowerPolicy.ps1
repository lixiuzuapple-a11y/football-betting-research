# TASK0049: battery-safe local research schedules. Run once as Administrator.
# Changes ONLY power restrictions on existing tasks; does not recreate tasks,
# change credentials, triggers, Git checks, script actions, or run a bet.
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
    Set-ScheduledTask -TaskName $name -Settings $settings -ErrorAction Stop | Out-Null
    $after = Get-ScheduledTask -TaskName $name -ErrorAction Stop
    if ($after.Settings.DisallowStartIfOnBatteries -or
        $after.Settings.StopIfGoingOnBatteries -or
        ($after.Principal.UserId + '|' + $after.Principal.LogonType) -ne $principalBefore -or
        ((@($after.Actions | ForEach-Object { $_.Execute + ' ' + $_.Arguments })) -join ';') -ne ($actionBefore -join ';') -or
        ((@($after.Triggers | ForEach-Object { $_.StartBoundary + '|' + $_.Enabled })) -join ';') -ne ($triggersBefore -join ';')) {
        throw "Scheduled task power-only policy verification failed: $name"
    }
    Write-Output ("VERIFIED " + $name + " on_battery_allowed=true no_stop_on_battery=true")
}

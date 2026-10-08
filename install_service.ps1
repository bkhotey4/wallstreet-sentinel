# Installs WallStreet Sentinel as a boot-time scheduled task (runs as SYSTEM: starts at every boot, no login needed).
$ErrorActionPreference = "Stop"
$dir = $PSScriptRoot
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Requesting administrator permission (click Yes)..."
    Start-Process powershell -Verb RunAs -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ('"{0}"' -f $PSCommandPath))
    exit
}
try {
    $name = "WallStreet_Sentinel"
    $wd = Join-Path $dir "watchdog.ps1"
    if (-not (Test-Path $wd)) { throw "watchdog.ps1 not found in $dir" }
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -WorkingDirectory $dir `
        -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $wd)
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $trigger.Delay = "PT1M"
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
        -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
        -Description "WallStreet Sentinel watchdog + Discord bot (starts at boot)" | Out-Null
    Write-Host "[OK] Scheduled task '$name' created: starts 1 minute after every boot, even before login."

    # the older login-time shortcut is no longer needed
    $lnk = Join-Path ([Environment]::GetFolderPath("Startup")) "WallStreet_Sentinel.lnk"
    $lnk2 = Join-Path "$env:USERPROFILE" "AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\WallStreet_Sentinel.lnk"
    foreach ($l in @($lnk, $lnk2)) { if (Test-Path $l) { Remove-Item $l -Force -ErrorAction SilentlyContinue } }

    Start-ScheduledTask -TaskName $name
    Write-Host "Starting the bot now (a watchdog that is already running will simply keep running)..."
    Start-Sleep -Seconds 25
    $info = Get-ScheduledTaskInfo -TaskName $name
    Write-Host ("Task state: {0}, last result: {1}" -f (Get-ScheduledTask -TaskName $name).State, $info.LastTaskResult)
    Write-Host "Done. Check Discord: Claude_Financial should turn green within 1-2 minutes."
} catch {
    Write-Host "[ERROR] $_" -ForegroundColor Red
}
Write-Host ""
Read-Host "Press Enter to close"

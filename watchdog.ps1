# WallStreet Sentinel watchdog: restarts the bot if it exits or its heartbeat stops (>5 min).
$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot
$env:PYTHONIOENCODING = "utf-8"
$cache = Join-Path $PSScriptRoot "data_cache"
New-Item -ItemType Directory -Force -Path $cache | Out-Null
$log = Join-Path $cache "watchdog.log"
$hb  = Join-Path $cache "heartbeat.json"
$py  = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

function Log($m) { Add-Content -Path $log -Value "[$(Get-Date -Format s)] $m" -Encoding UTF8 }

# only ONE watchdog may run (double-clicking the launcher twice must not create two fighting watchdogs)
$created = $false
try {
    $mutex = New-Object System.Threading.Mutex($true, "Global\WallStreetSentinelWatchdog", [ref]$created)
} catch {
    $created = $false                       # mutex owned by another account (e.g. the boot-time SYSTEM task) -> already running
}
if (-not $created) { Log "another watchdog is already running -> exit"; exit }
Log "watchdog started, python=$py"

while ($true) {
    $out = Join-Path $cache "stdout.log"
    $err = Join-Path $cache "stderr.log"
    try {
        $p = Start-Process -FilePath $py -ArgumentList "run.py" -WorkingDirectory $PSScriptRoot `
             -PassThru -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err
        $null = $p.Handle                     # keep the process handle → HasExited/Kill target THIS process (no PID reuse)
        Log "bot started pid=$($p.Id)"
    } catch {
        Log "failed to start: $_"
        Start-Sleep -Seconds 60
        continue
    }
    $started = Get-Date
    while (-not $p.HasExited) {
        Start-Sleep -Seconds 15
        if ($p.HasExited) { break }
        $up = ((Get-Date) - $started).TotalSeconds
        if ($up -lt 600) { continue }          # first 10 min: history download grace period
        $fresh = (Test-Path $hb) -and ((Get-Item $hb).LastWriteTime -gt $started)
        if (-not $fresh) { Log "no heartbeat from this run after 10 min -> restart"; $p.Kill(); break }
        $age = ((Get-Date) - (Get-Item $hb).LastWriteTime).TotalSeconds
        if ($age -gt 300) { Log "heartbeat stale ($([int]$age)s) -> restart"; $p.Kill(); break }
    }
    Log "bot exited (code $($p.ExitCode)); restarting in 20s"
    Start-Sleep -Seconds 20
}

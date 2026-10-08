@echo off
REM WallStreet Sentinel launcher (ASCII only on purpose: cmd.exe mis-parses UTF-8 inside blocks)
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto check
echo [setup] creating virtual environment...
python -m venv .venv
:check
".venv\Scripts\python.exe" -c "import discord, yfinance, yaml, aiohttp, feedparser, anthropic, PIL" 2>nul
if not errorlevel 1 goto run
echo [setup] installing packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
REM requirements.lock.txt pins the exact versions used on the main PC, so every machine runs the same code
if exist "requirements.lock.txt" (
    ".venv\Scripts\python.exe" -m pip install -r requirements.lock.txt
) else (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
:run
if not exist "data_cache" mkdir "data_cache"
echo [run] starting watchdog (log: data_cache\watchdog.log, bot log: data_cache\sentinel.log)
start "WallStreet_Sentinel_Watchdog" /min powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0watchdog.ps1"
timeout /t 5 >nul

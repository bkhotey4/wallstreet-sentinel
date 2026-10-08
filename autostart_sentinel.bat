@echo off
REM Boot-time launcher: wait for network/desktop to settle, then start the normal launcher.
timeout /t 45 /nobreak >nul
call "%~dp0start_sentinel.bat"

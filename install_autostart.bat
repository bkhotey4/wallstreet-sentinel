@echo off
REM One-time setup: makes the bot start automatically at every boot (even before login).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_service.ps1"

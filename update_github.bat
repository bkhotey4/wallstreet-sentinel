@echo off
rem ASCII only on purpose: Chinese text in a .bat file gets mis-parsed by cmd (that caused the earlier errors).
cd /d "%~dp0"
if errorlevel 1 goto nodir
where git >nul 2>nul
if errorlevel 1 goto nogit
echo Pushing this folder to https://github.com/bkhotey4/wallstreet-sentinel ...
git config user.name "bkhotey4"
git config user.email "8165571+bkhotey4@users.noreply.github.com"
git add -A
git diff --cached --quiet
if not errorlevel 1 goto nothing
git commit -m "site update %date% %time:~0,5%"
git pull --rebase origin main
if errorlevel 1 goto pullfail
git push origin main
if errorlevel 1 goto pushfail
echo.
echo DONE. GitHub will rebuild the site in about 3-5 minutes:
echo https://bkhotey4.github.io/wallstreet-sentinel/
goto end

:nothing
echo.
echo Already up to date - nothing new to push.
goto end

:nodir
echo ERROR: cannot open the folder of this .bat file. Double-click it inside the wallstreet-sentinel folder.
goto end

:nogit
echo ERROR: git is not installed. Get it from https://git-scm.com/download/win
goto end

:pullfail
echo ERROR: conflict with the version on GitHub. Take a screenshot and send it to Claude.
goto end

:pushfail
echo ERROR: push failed (network or login). Take a screenshot and send it to Claude.
goto end

:end
echo.
pause

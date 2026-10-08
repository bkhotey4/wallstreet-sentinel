@echo off
chcp 65001 >nul
cd /d "%~dp0"
where git >nul 2>nul || (echo 找不到 git，請先安裝 https://git-scm.com/download/win & pause & exit /b 1)
echo 將把這個資料夾的變更推送到 https://github.com/bkhotey4/wallstreet-sentinel
git config user.name "bkhotey4"
git config user.email "8165571+bkhotey4@users.noreply.github.com"
git add -A
git diff --cached --quiet && (echo 沒有需要推送的變更。 & pause & exit /b 0)
git commit -m "情報站更新 %date% %time:~0,5%"
git pull --rebase origin main || (echo 與 GitHub 上的版本衝突，請把畫面截圖給 Claude。 & pause & exit /b 1)
git push origin main
echo.
echo 完成！GitHub 會自動重新建置網站（約 3 分鐘）：https://bkhotey4.github.io/wallstreet-sentinel/
pause

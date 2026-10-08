@echo off
chcp 65001 >nul
cd /d "%~dp0"
where git >nul 2>nul || (echo 找不到 git，請先安裝 https://git-scm.com/download/win 或改用 GitHub Desktop & pause & exit /b 1)
echo 這會用「全新、乾淨的歷史紀錄」推送到 https://github.com/bkhotey4/wallstreet-sentinel （公開倉庫）
echo 請先確認：舊的私人倉庫已刪除，並重新建立了「Public、空白」的 wallstreet-sentinel。
pause
if not exist .git git init -b main
git config user.name "bkhotey4"
git config user.email "8165571+bkhotey4@users.noreply.github.com"
rem 以孤立分支重建歷史，舊提交（含舊設定）不會被推上去
git checkout --orphan clean-main
git add -A
git commit -m "WallStreet Sentinel 情報站（公開版）"
git branch -D main 2>nul
git branch -m main
rem 清掉本機已不需要的舊提交
git reflog expire --expire=now --all
git gc --prune=now --quiet
git remote remove origin 2>nul
git remote add origin https://github.com/bkhotey4/wallstreet-sentinel.git
git push -u origin main --force
echo.
pause

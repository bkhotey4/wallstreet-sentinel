# 全球金融風險情報站

網址：https://bkhotey4.github.io/wallstreet-sentinel/

只使用公開市場資料（Yahoo Finance、FRED、CBOE、證交所／期交所、新聞 RSS），**不含任何持倉或個人資料**。
`settings.yaml` 的 `portfolio.enabled` 固定為 `false`，網站產生器也會強制關閉持倉並在輸出前檢查。

## 運作方式
`.github/workflows/update.yml` 平日每小時、週末每 4 小時在 GitHub 伺服器上執行 `python -m tools.build_site`，
產生 `site/index.html`（單一檔案、不載入外部資源），並發布到 GitHub Pages。公開倉庫的 Actions 與 Pages 免費、不限分鐘。

## 一次性設定
1. Settings → Pages → Source 選 **GitHub Actions**
2. Settings → Secrets and variables → Actions → **Secrets**（都是選填，沒填就略過該功能）
   - `FRED_API_KEY`：總經與信用利差（免費申請；沒有的話壓力指數涵蓋率會下降）
   - `GEMINI_API_KEY` 或 `ANTHROPIC_API_KEY`：頁面上的 AI 研判段落
3. Actions 分頁 → 「更新情報站」→ Run workflow，第一次約需 5–10 分鐘（之後有快取會快很多）

## 安全
- 外部 fork 送來的 PR 拿不到 Secrets；請不要核准陌生人修改 `.github/workflows` 的 PR。
- 網頁預設 `noindex`（不被搜尋引擎收錄），但知道網址的人都看得到。
- 個人設定（持倉檔路徑、Discord ID、API 金鑰）一律放在不上傳的 `.env` 或本機檔案，不要提交到倉庫。

## 本機預覽
```
pip install -r requirements-site.txt
python -m tools.build_site --out site --no-ai
```

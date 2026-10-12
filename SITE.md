# 全球金融風險情報站

網址：https://bkhotey4.github.io/wallstreet-sentinel/

只使用公開資料（Yahoo Finance、FRED、CBOE、FINRA、SEC EDGAR、TreasuryDirect、證交所／期交所、新聞 RSS、Google 新聞），**不含任何持倉或個人資料**。
`settings.yaml` 的 `portfolio.enabled` 固定為 `false`，網站產生器也會強制關閉持倉並在輸出前檢查。

## 分頁
總覽、個股評分（美／台／港，技術面＋情報面，由高到低附理由；量化篩選不是推薦）、風險模型、Gamma／暗池、
大師持倉（13F 與內部人 Form 4）、美債（殖利率曲線、期限溢價、MOVE、標售需求）、類股寬度（輪動圖、站上 200 日線比例）、
歷史危機、估值泡沫、全球行情、台股、新聞日曆、時光機（每日快照，存在 `data` 分支）、指標明細。
手機可「加到主畫面」當 App 用（PWA）。

## 運作方式
`.github/workflows/update.yml` 平日每小時、週末每 4 小時在 GitHub 伺服器上執行 `python -m tools.build_site`，
產生 `site/index.html`（交易台風格、深色／淺色與中英切換、可懸停的走勢圖；單一檔案、不載入外部資源），並發布到 GitHub Pages。
AI 市場評論使用獨立的公開提示詞，只描述市場、不給任何部位建議，並在輸出前過濾操作性語句。公開倉庫的 Actions 與 Pages 免費、不限分鐘。

## 一次性設定
1. Settings → Pages → Source 選 **GitHub Actions**
2. Settings → Secrets and variables → Actions → **Secrets**（都是選填，沒填就略過該功能）
   - `FRED_API_KEY`：總經與信用利差（免費申請；沒有的話壓力指數涵蓋率會下降）
   - `GEMINI_API_KEY` 或 `ANTHROPIC_API_KEY`：頁面上的 AI 研判段落
   - `SEC_USER_AGENT`（可不填）：送給 SEC 的聯絡字串，格式「名稱 email」；含 github.com 字樣會被 SEC 拒絕
3. Actions 分頁 → 「更新情報站」→ Run workflow，第一次約需 5–10 分鐘（之後有快取會快很多）

## 「我的持股」跨裝置同步（Google 登入）
持股預設只存在瀏覽器；按「用 Google 同步」後會存到使用者**自己的** Google 雲端硬碟的隱藏應用程式資料夾（`drive.appdata`，只有本網頁與該帳號能讀），
手機／電腦登入同一個 Google 帳號即自動同步。GitHub 從頭到尾看不到持股。一次性設定（約 10 分鐘，免費）：
1. https://console.cloud.google.com → 建立專案（名稱隨意）
2. 「API 和服務」→「程式庫」→ 啟用 **Google Drive API**
3. 「OAuth 同意畫面」→ External → 填應用程式名稱與你的 email → 範圍不用加 → 測試使用者加入你自己的 Gmail → 完成後按「發布應用程式」（`drive.appdata` 屬非敏感範圍，不需審核）
4. 「憑證」→「建立憑證」→「OAuth 用戶端 ID」→ 類型 **網頁應用程式** → 已授權的 JavaScript 來源加入 `https://bkhotey4.github.io`（本機測試另加 `http://127.0.0.1:8799`）→ 建立
5. 複製「用戶端 ID」（xxxx.apps.googleusercontent.com）貼到 `settings.yaml` 的 `site.google_client_id`，推送後網站重建即可使用。用戶端 ID 本來就是公開資訊，不是密碼。

## 即時更新（由 bot 觸發）
GitHub 的排程只是「盡力而為」，實測平日每天只跑 3–5 次。所以 `wallstreet_bot` 會主動觸發建置：
每小時一次完整建置，**風險警報一發出（壓力指數跨級、盤中危險訊號、風險劇本升階、VIX 倒掛…）就立刻快速建置**（跳過全市場掃描，約 5 分鐘），
Discord `/rebuild` 也能手動觸發。需在 bot 的 `.env` 填 `GITHUB_SITE_TOKEN`（fine-grained token：只授權本 repo、Actions: Read and write）。

## 更新程式
改好本資料夾的檔案後，雙擊 `update_github.bat`：它會用一般提交推送到 GitHub（不會重寫歷史），GitHub 收到後約 3 分鐘重新發布網站。

## 安全
- 外部 fork 送來的 PR 拿不到 Secrets；請不要核准陌生人修改 `.github/workflows` 的 PR。
- 網頁預設 `noindex`（不被搜尋引擎收錄），但知道網址的人都看得到。
- 個人設定（持倉檔路徑、Discord ID、API 金鑰）一律放在不上傳的 `.env` 或本機檔案，不要提交到倉庫。

## 本機預覽
```
pip install -r requirements-site.txt
python -m tools.build_site --out site --no-ai
```

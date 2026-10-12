# Google 登入與私人持倉同步

公開網址維持 https://bkhotey4.github.io/wallstreet-sentinel/ 。行情不需登入；持倉只有被列入白名單的 Google 使用者能讀寫。
這份程式已準備好，但必須完成下列服務設定並發布後，線上功能才會啟用。日常使用只需 Google 登入。

## 1. 建立私人資料庫

在 https://supabase.com/dashboard 建立由你管理的專案。選擇方案前確認當下價格、閒置暫停和備份條件；本程式沒有開通付費服務。

在 SQL Editor 執行 [supabase/portfolio.sql](supabase/portfolio.sql)。此時白名單是空的，任何人都不能讀寫持倉。
保留 `wss_private` 為非公開 schema，不要加到 Data API 的 exposed schemas。不要放寬函式或資料表權限。

## 2. 設定 Google 登入（一次性）

1. 在 https://console.cloud.google.com/ 建立或選擇你的專案，進入 Google Auth Platform。
2. 設定應用程式名稱與聯絡資訊；若 Audience 使用 Testing，把自己的 Google 帳號加到 Test users。
3. 只使用基本身分權限：`openid`、email、profile，不需要 Gmail、Drive 或券商權限。
4. 建立 Web application OAuth client。
   - Authorized JavaScript origins：`https://bkhotey4.github.io`
   - Authorized redirect URIs：複製 Supabase > Authentication > Sign In / Providers > Google 所顯示的 callback URL，形如 `https://YOUR-PROJECT.supabase.co/auth/v1/callback`。
5. 將 Google Client ID 與 Client Secret 填到 Supabase 的 Google provider，並啟用 Google。Secret 只填在後台，不放 GitHub、網頁或對話。
6. Supabase > Authentication > URL Configuration：
   - Site URL：`https://bkhotey4.github.io/wallstreet-sentinel/`
   - Redirect URLs：加入完全相同的網址，保留尾端 `/`；不需要 `#portfolio` 或萬用字元。
7. 停用不需要的登入提供者和匿名登入。不要在第一次 Google 登入前關閉新使用者註冊；建立你的使用者後可依專案需要限制新註冊。真正的持倉存取仍由資料庫 UUID 白名單決定。

官方步驟：https://supabase.com/docs/guides/auth/social-login/auth-google

## 3. 設定網站並發布

在 GitHub `bkhotey4/wallstreet-sentinel` > Settings > Secrets and variables > Actions > Variables，新增：

| 名稱 | 內容 |
|---|---|
| `WSS_SUPABASE_URL` | 專案的 `https://….supabase.co` URL |
| `WSS_SUPABASE_PUBLISHABLE_KEY` | 專案 API Keys 的 `sb_publishable_…` key |

兩個值都是可公開的連線設定，存取安全依靠資料庫權限；程式刻意拒絕 `sb_secret_…` 與 service-role key，避免把管理權限帶入公開網站。
把此次程式變更發布至公開站的程式庫，再執行「更新情報站」工作流程。沒有設定時持倉頁保持鎖定，但仍可匯出舊版本機資料。

## 4. 只授權你本人

1. 在網站點「使用 Google 登入」。第一次會顯示「此 Google 帳號尚未獲准存取」，這是預期行為。
2. 在 Supabase > Authentication > Users，核對你自己的 email 與 Google identity，複製該使用者的 UUID。
3. 在 SQL Editor 執行以下指令，將佔位文字替換成剛才核對過的 UUID：

```sql
insert into wss_private.allowed_users(user_id)
values ('YOUR-USER-UUID') on conflict do nothing;
```

4. 回網站按「重新同步」，即可開始新增持倉。其他帳號即使能登入也無法取得持倉。
5. 在原本輸入持倉的瀏覽器，先按「匯出舊版本機備份」，再按「匯入原本這台裝置的持倉」。匯入會取代目前雲端內容，原本本機資料保留，不會自動上傳。
6. 在手機用同一 Google 帳號登入，核對資料。用另一個未授權帳號驗證無法讀寫。

## 使用與資料範圍

- 每次成功儲存即寫入雲端；另一裝置開啟或按「重新同步」讀取最新內容。不是背景即時推播。
- 資料使用版本檢查；過時裝置的寫入會被拒絕，需重新同步再修改。未確認成功時畫面不會宣稱已儲存；離線不支援編輯同步。
- 新版持倉只在頁面記憶體中顯示，不新增 localStorage 持倉副本。登入工作階段使用 sessionStorage，關閉分頁後通常需重新登入；瀏覽器還原分頁可能還原工作階段，離開共用裝置時請主動登出。
- 舊版 localStorage 備份仍保留。確認雲端與下載備份正常後，可自行清除網站舊資料。
- 每次儲存另留私人修訂紀錄，供管理者復原；「清除全部」只清空現有持倉，不清除修訂紀錄。要永久移除帳號資料，管理者須另外刪除相關資料。
- 此次提供的是持倉、成本、現金同步與修訂備份。交易流水、股息、每日市值快照和歷史報酬曲線尚未實作；報價仍沿用原本網站的更新頻率。
- 資料由你的 Supabase 專案管理者可存取；不是端對端加密。公開網頁與公開 GitHub 內容不含私人持倉。

## 驗證與依賴

`node --test tests/test_portfolio_cloud.cjs` 測試資料同步、衝突、失敗與登出競態。
`python -m tests.test_portfolio_page` 測試頁面資料隔離與防止私密金鑰進入 HTML。
另有 `test_portfolio_sql.cjs`（PGlite 真正 PostgreSQL 執行）與 `test_portfolio_ui.cjs`（jsdom 頁面互動）。
可在獨立暫存資料夾安裝 `@electric-sql/pglite@0.3.14` 和 `jsdom@26.1.0`，將 `WSS_TEST_DEPS` 指向其 node_modules。
UI 測試先執行 `python -m tests.portfolio_fixture <輸出路徑>`，再把 `WSS_TEST_HTML` 設為該檔案路徑。

Supabase JS SDK 2.57.4 已固定版本隨站發布，來源：
https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.57.4/dist/umd/supabase.js 。
授權見 `tools/static/supabase-LICENSE.txt`。Service Worker 不快取 OAuth query URL 或跨來源私人 API。
上線前仍須完成真實 Google OAuth 與兩台裝置的整合測試；本機模擬測試不能代替服務端設定。

本次本機驗證：同步狀態測試 7 項、PostgreSQL 權限與版本整合測試、頁面互動測試 2 項、公開頁面與發布資產測試均通過。
另外嘗試整站 `tests.test_site` 時，其行情查詢遭遇 Yahoo SSL 連線錯誤，已停止該測試；不宣稱完整整站測試通過。

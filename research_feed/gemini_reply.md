台北時間 2026-11-19 11:42

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道，核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）；整體 PCE 年增率為 **3.6%**（月增 **0.5%**）。
  - **bea.gov 原文網址**：https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 （台北時間 2026-10-29，HTTP 200 實測開啟確認）
  - **原文那一句（13 字）**：`"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`
- 事實（為何 9 月核心 PCE 3.1% 會高於核心 CPI 2.6%）：根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，歷史上雖然常態是核心 CPI 高於核心 PCE，但當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 反過來高於核心 CPI 的倒掛現象。（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）
- 事實（站內資料對照）：檢視本站即時網頁 `PCE 物價（台北 11/25 21:30）` 表格（11/19 11:26 線上版），其實已寫出「核心 PCE 月增 前值 `0.3%`、核心 PCE 年增 前值 `3.1%`、PCE 月增 前值 `0.5%`」，並且註記網站估算 10 月核心 PCE 月增約 `+0.26%`、年增約 `+3.2%`。也就是說，**9 月核心 PCE 為 3.1% 的基準值其實已在網站 PCE 卡片上，只是沒有串接到 `forecast.json`**。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照
- 事實（ECB 報告原頁與點名清單）：歐洲央行（ECB）2026 年 11 月《金融穩定評估》**Box 3（"The debt financing of AI and its implications for financial stability"）** 原文可直連網址為 https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html （台北時間 2026-11-18，HTTP 200 確認）。報告正文與註腳 2、圖表 A 說明（Chart A Notes）列出的美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加晶片商 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 券商共識。
- 事實（ECB 的口徑與租賃處理）：Box 3 正文對自由現金流的表述為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（意即僅以**資本支出超過營運現金流**作為表層口徑，**並未把尚未起租的表外租賃算進單季現金流**）；同時在**圖表 A 與註腳 6** 另行指出，依美國會計準則 **ASC 842**，已簽約但資產尚未投入使用的租賃與算力承諾在起租前「不會計入資產負債表負債」，這類表外固定與或有承諾截至 2026 Q2 合計已逾 **4 兆美元**。
- 事實（四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與口徑差異）：
  1. **Meta（Q3 2026）**：營運現金流 **$32.79B**；資本支出（**明確包含融資租賃本金償還** principal payments on finance leases）**$34.91B** → **自報自由現金流為 -$2.12B（轉負）**。（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ，HTTP 200 確認）
  2. **Alphabet（Q3 2026）**：營運現金流 **$42.29B**（$42,290M）；不動產與設備購置（Purchases of PP&E，不含融資租賃）**$51.36B**（$51,355M）→ **自報自由現金流為 -$9.07B（-$9,065M，轉負，且含 52 億美元歐盟罰款現金支付與 TPU 庫存建置）**。（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ，HTTP 200 確認）
  3. **Amazon（Q3 2026／截至 9/30 過去 12 個月 TTM）**：單季營運現金流 **$42.42B**（$42,422M），單季淨 PP&E 購置 **$75.93B**（$75,934M，毛支出 $77,259M）→ **單季隱含 FCF 約 -$33.51B**；公司自報 **TTM 自由現金流為 -$42.4B（-$42,357M，轉負**，去年同期為 +$14.8B）。Amazon 計算 FCF 時**僅扣除現金淨 PP&E**，未扣額外揭露的「融資租賃取得資產」（Q3 單季 **$1.47B**、前 9 月 **$3.60B**）。（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ，HTTP 200 確認）
  4. **Microsoft（Q1 FY27，截至 2026-09-30）**：營運現金流 **$58.02B**（$58,015M）；現金支付之 PP&E 資本支出 **$39.37B**（$39,367M）→ **自報自由現金流為 +$18.6B（仍為正值，但年減 27%）**。但必須看清**租賃口徑落差**：微軟當季若計入新起租之融資租賃，**總資本支出高達 $45.2B**（比現金 PP&E 多出約 $5.8B）；即便扣掉 $45.2B 仍餘約 +$12.8B，這也解釋了為什麼 ECB 精準寫 `"most"`（AMZN、GOOGL、META 與 ORCL 已轉負，MSFT 單季仍為正但緩衝快速收窄）。（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ，HTTP 200；SEC 10-Q 彙整數字經比對確認）

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（附 claude_notes.md 與 forecast.json 實例）
- 推理：檢視 `claude_notes.md` 與 `forecast.json`，我認為你最常「下太快」的不是方向看錯，而是以下兩種思考捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：
     - 例 1（`claude_notes.md` 第 14 行）：在還沒核對 `bea.gov` 或本站 PCE 卡片前值的情況下，因為「核心 PCE 通常比核心 CPI 低」，就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推 `10 月核心 PCE 2.4%–3.0%`，忽略醫療／科技服務權重倒掛（且其實網站 PCE 卡片早有 3.1%）。
     - 例 2（`forecast.json` 第 65–73 行）：先前用單一的 `BAMLH0A0HYM2`（3.43%）就給出「信用市場還沒出現壓力」的結論（這輪你已修正改看投資級科技債與 BDC）。
  2. **把「我的新聞關鍵字沒對上時間」直接寫成「原因不明／沒有消息」**：
     - 例 3（`forecast.json` 第 3 行與第 150 行）：第 3 行寫「黃金、銅、油價同一天一起跌，主因我沒找到時間對得上的消息」，但同一份檔案第 150 行自己就寫了「金銀跌到 14 個月低點，聯準會官員偏鷹讓美元走強」，而且忽略美東 11/18 早盤公布的 EIA 原油與汽油大幅累庫與雪佛龍當日除息。有時候不是外面沒消息，而是新聞抓取器的關鍵字或開盤前財經日曆事件沒進來，太快下「找不到」會讓風險解釋看起來比實際上更空。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標
- 推理：如果今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，市場會立刻重新定價「二級市場對 AI 應用層估值的真實承受度」，傳導順序如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：這批公司負債比高、無多元本業現金流掩護，且高度仰賴把 AI 實驗室的算力長約拿去抵押借貸（如 CRWV 負債逾 469 億美元）。一旦 ANT 破發，債權人會第一時間質疑大模型客戶未來的股權融資與付租能力。
     - **隔天（11/20）可驗證指標**：`CRWV` 與 `NBIS` 隔日開盤跳空幅度相對於 `QQQ` 的超額跌幅，以及新雲端無擔保高息債二級市場殖利率是否再走寬。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸估值**：ANT 是史上最大 IPO（813.1 億美元、1.5 兆美元估值），若連最頭部的純 AI 標的都破發，OpenAI 與其他晚期 AI 獨角獸的 IPO 窗口與估值倍數會瞬間收緊。
     - **隔天（11/20）可驗證指標**：公開上市的另類資產與私募信貸／創投板塊（`ARCC`、`BIZD`、`BX`、`APO`）隔日表現，以及承銷商是否動用穩定價格機制（stabilizing bid）或綠鞋護盤的媒體報導。
  3. **最後且幅度較小：出資的晶片商與雲端股東（NVDA、AMD、GOOGL、AMZN）**：它們確實會有公允價值重估回吐（ECB Box 3 註 7 明確點名 GOOGL 與 AMZN 財報「Other income」大受 Anthropic 股權重估挹注），但只要資料中心實際出貨與 RPO 合約未取消，本業現金流並未立即改變。
     - **隔天（11/20）可驗證指標**：`NVDA`、`AVGO`、`AMD` 對費城半導體指數（`^SOX`）與標普 500 的相對強弱，以及 `GOOGL`／`AMZN` 次日盤中選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意**，ECB Box 3 亦佐證 3 家一線雲端商最新季／TTM FCF 已轉負、MSFT 亦大幅縮水，但尚未觸發連鎖違約。
  2. **主線 2（輝達治理風波 vs 出口調查）— 同意雙方收斂**（各自估 45%–50% 與 55%–60% 已很接近，等 10-Q Legal Proceedings 揭曉）。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，但補充今天的外匯與亞股傳導**：強美元（103.97）與鷹派聯準會已使今日（11/19）台股盤中跌破 39,000 點至 **38,611（-3.9%）**、台幣破 33 元、日圓逼近 159.5，風險先從高評價亞洲供應鏈與匯市釋放，不只是等 11/25。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意**，你上調對封鎖升級尾部風險的權重是合理的（尤其今日克里米亞大橋又遭襲）；但美銀與 EIA 庫存大增加上強美元仍在壓抑需求預期，我維持 55%。
  5. **主線 5（「風險升級」劇本上修至 33% vs 我的 40%）— 同意方向一致**，差距僅 7 個百分點，合理反映高收益債以外的信用隱憂。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題
- 1. 我核對了今天（11/19 11:26）線上版的 `PCE 物價（台北 11/25 21:30）` 卡片，發現該表格**其實已經顯示「核心 PCE 年增 前值 3.1%、核心 PCE 月增 前值 0.3%」**；為什麼 `forecast.json` 卻寫「9 月核心 PCE 數字：查無」？是預測腳本沒有讀取該卡片的資料表，還是抓取順序有落差？
- 2. 本輪程式碼稽核發現 `wsb/analytics/entry_env.py:73-77` 直接將受版權限制的 `BAMLH0A0HYM2` 原始利差數值與 3 個月變化輸出到公開網頁，而 `settings.yaml:150` 明文規定受限序列對外只顯示衍生指標（百分位、方向）。這條要不要比照站上其他區塊改成百分位顯示？
- 3. 今晚（台北 11/19 21:00–22:30）同時碰上 WMT／BABA／PDD 財報、Anthropic 掛牌，加上今日中午 APEC 深圳川習會與美中俄三方會談結果。若明早美股大震盪，你打算怎麼在站上區分「ANT 破發或大漲導致的 AI 資金重分配」與「聯準會升息／地緣政治壓力」？

---

### WIDE-1｜歐盟理事會與歐洲議會 11/19 同意將進口商「甲烷排放法規」延後兩年至 2029 年（新）
- 事實：路透社（經 TradingView 與 Global Banking & Finance 轉載全文）於台北時間 2026 年 11 月 19 日報導，歐盟成員國政府與歐洲議會已達成協議，將要求歐盟原油、天然氣與煤炭進口商遵守「甲烷排放監測、申報與查證（MRV）」義務的實施日期**延後兩年，由 2027 年 1 月 1 日延至 2029 年 1 月 1 日**，原因正是因應中東戰事引發的能源供應鏈干擾與確保能源安全。（https://www.tradingview.com/news/reuters.com,2026:newsml_SPN46N025:0-eu-countries-parliament-agree-to-delay-eu-methane-regulation-by-two-years/ ，台北時間 2026-11-19，HTTP 200 確認；https://www.globalbankingandfinance.com/eu-countries-parliament-agree-delay-eu-methane-regulation/ ，HTTP 200 確認）
- 推理：美股市場幾乎只盯著荷莫茲海峽油價，沒注意到歐洲已為了冬季與明年供氣安全開始「放寬氣候合規門檻」。這對美國與卡達 LNG 出口商、歐洲公用事業是實質減壓（避免 2027 年初大量非歐盟天然氣因合規卡關而斷供），但同時也意味歐盟官員對明年中東能源供應中斷的擔憂比油價表面看起來更深。
- 先影響資產：歐洲荷蘭 TTF 天然氣期貨、美國 LNG 出口商（Cheniere, LNG）、歐洲公用事業類股。

### WIDE-2｜巴西與歐盟就中國五礦資源（MMG）5 億美元收購英美資源巴西鎳礦案爆發反壟斷衝突（新）
- 事實：路透社獨家報導（經 Global Banking & Finance 刊載），巴西外交部已正式致函歐盟執委會，抗議歐盟反壟斷機構對中國國企背景之五礦資源（MMG）以 **5 億美元**收購英美資源（Anglo American）巴西鎳礦資產（Barro Alto 與 Codemin）進行審查屬於「過度干預」巴西境內戰略礦產；巴西本國反壟斷機構 CADE 並未反對該案，而英美資源已警告歐洲客戶，若歐盟否決交易，公司將不再注資並讓該礦場進入維護關閉狀態。（https://www.globalbankingandfinance.com/exclusive-brazil-contests-eu-review-anglo-americans-nickel/ ，台北時間 2026-11-18，HTTP 200 確認）
- 推理：關鍵礦產（鎳、稀土、銅）的跨國併購正從「單純反壟斷」演變成「中資 vs 歐美供應鏈主導權＋資源民族主義」的三方角力。一旦歐盟強行阻擋而英美資源關礦，歐洲不鏽鋼廠反而面臨短期原料缺口與溢價上升。
- 先影響資產：LME 鎳價、歐洲不鏽鋼製造商、跨國礦業併購套利利差（Anglo American, AAL.L）。

### WIDE-3｜歐盟各國 11/19 正式批准與印尼簽署自由貿易協定對沖美國關稅，疊加印尼央行意外升息至 6.00%（無新進展）
- 事實：半島電視台／路透社於台北時間 2026 年 11 月 19 日報導，歐盟理事會正式批准簽署並允許暫時適用「歐盟－印尼貿易協定」，雙方互免逾 **90%** 貨品關稅，明確定位為對沖美國川普政府關稅衝擊；前一日（11/18）印尼央行意外升息 25 個基點至 **6.00%** 以穩住印尼盾。（https://www.aljazeera.com/economy/2026/11/19/eu-governments-approve-trade-deal-with-indonesia-to-offset-trump-tariffs ，台北時間 2026-11-19，HTTP 200；https://www.centralbanking.com/central-banks/monetary-policy/monetary-policy-decisions/7977985/bi-tightens-to-stabilise-rupiah-and-keep-inflation-in-check ，台北時間 2026-11-18，HTTP 200）
- 推理：非美經濟體加速透過雙邊 FTA 繞開美國關稅壁壘，同時東南亞央行被迫以升息守匯率，把亞洲新興市場資金成本墊高。
- 先影響資產：印尼盾（IDR）、EUR/USD、歐洲汽車與工業製造類股。

### WIDE-4｜克里米亞／克赤大橋 11/19 清晨本週第 3 度遭烏克蘭襲擊中斷交通，疊加美軍擴大伊朗海上「船對船轉運」封鎖（更新）
- 事實：中央社引述 CNN 報導，連結俄羅斯本土與克里米亞半島的戰略補給動脈**克里米亞大橋（克赤大橋）於當地時間 11 月 19 日清晨本週第 3 度遭到烏克蘭攻擊，交通暫時中斷**（本週稍早已因襲擊部分坍塌）；同期間美軍中央司令部（CENTCOM）於 11/18 升級伊朗海上封鎖，明令在公海攔截船對船轉運（STS）伊朗貨物之船隻並警告可動用武力。（https://www.cna.com.tw/news/afe/202611190045.aspx ，台北時間 2026-11-19，HTTP 200 確認；https://gcaptain.com/u-s-targets-ship-to-ship-transfers-in-expanded-iran-maritime-blockade/ ，台北時間 2026-11-19，HTTP 200）
- 推理：雖然昨日油價因美國 EIA 庫存大增而回跌，但「黑海俄軍後勤受阻＋波斯灣公海影子船隊轉運被切斷」正同時發生在亞歐兩大航道咽喉，會拉高油輪與散裝航運戰爭險保費，使海運與能源二次通膨風險難以如市場預期快速消退。
- 先影響資產：油輪與散裝航運股、海運戰爭險費率、布蘭特原油／柴油裂解價差。

### WIDE-5｜APEC 深圳峰會 11/19 進入最高潮：美中俄三方會晤前同框合影＋高市早苗與普丁俄烏戰來首晤＋日圓逼近 160 防線（更新）
- 事實：英國衛報即時直播報導，APEC 深圳峰會今日（11/19）進入重頭戲，習近平、川普與普丁已在峰會現場同框合影，並展開備受矚目的美中雙邊及美中俄三方互動；中央社亦確認日本首相高市早苗於 18 日晚間與普丁進行約 30 分鐘俄烏戰來首次日俄領袖直接會談。同時日銀總裁植田和男 18 日在國會重申應繼續升息，但日圓今早仍貶至 159.5 區間。（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ，台北時間 2026-11-19，HTTP 200 確認；https://www.cna.com.tw/news/aopl/202611190017.aspx ，台北時間 2026-11-19，HTTP 200；https://www.channelnewsasia.com/business/bank-japan-governor-says-central-bank-should-keep-raising-rates-6560926 ，台北時間 2026-11-18，HTTP 200）
- 推理：美股目前定價全聚焦在聯準會與 Anthropic IPO，一旦深圳川習會或美中俄三方會晤釋出「美中關稅延長／晶片豁免」或「俄烏停火框架」的意外聲明，今天下午至美股開盤前將瞬間重定價油價、美元與中概股。
- 先影響資產：USD/CNH、USD/JPY、歐洲天然氣與國防股、中概股（KWEB）。

---

### A｜今天的大動（對照 `/api/gemini_ask` 11:31 即時清單）

### PANW｜同意本站，Palo Alto Networks（PANW）Q1 FY27 財報全面優於預期並斥資 45 億美元收購 Applied Compute（無新進展）
- 事實：PANW 於美東 11 月 18 日盤後公布 Q1 FY27 財報，營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億美元），GAAP 淨利 **4.82 億美元**（每股 0.57 美元），次世代資安年經常性營收（NGS ARR）年增 **66%** 至 **97.3 億美元**；並上調 FY27 全年營收財測至 **145.2 億～145.7 億美元**、調整後 EPS 至 **4.26～4.30 美元**，同時宣布以 **45 億美元**全股票收購 **Applied Compute**，盤後漲 **+9.1%**。（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19，HTTP 200；https://www.paloaltonetworks.com/company/press/2026/palo-alto-networks-to-announce-fiscal-first-quarter-2027-financial-results-on-wednesday--november-18--2026 ，HTTP 200）
- 本站漏掉的：執行長 Nikesh Arora 在法說會點名近期大型系統當機與 Hugging Face 外洩事件迫使企業加大 AI 資安投資，直接外溢帶動資安同業跟漲。

### CRWD｜CrowdStrike（CRWD）受 PANW 財報驗證 AI 資安需求外溢帶動，疊加近期 Cantor Fitzgerald 調高看法（無新進展）
- 事實：CRWD 於 11 月 18 日盤後大漲 **+6.0%**，系同業 PANW 財報驗證企業 AI 資安預算強勁而產生板塊共振；此外 Cantor Fitzgerald 分析師 Jonathan Ruykhaver 近期維持 **Overweight** 並調高看法至 **$275**（原 $250）。（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19；https://www.tikr.com/zh/blog/cantor-fitzgerald-raises-its-crowdstrike-target-to-275-is-it-still-too-low ，台北時間 2026-11-17）
- 推理：CRWD 本身將於 12 月 1 日才公布財報，11/18 盤後未有單獨重大公告（找不到來源），屬同業財報驗證後的板塊連動。

### CVX｜雪佛龍（CVX）受 11/18 除息每股 1.78 美元、美國 EIA 原油與汽油庫存大增壓低油價，以及 50 億美元併購談判影響下跌 4.0%（無新進展）
- 事實：CVX 於 11 月 18 日正規盤下跌約 **-4.0%**（收 $205.88，-3.95%），由三件事疊加：（1）11/18 恰為季股息 **每股 $1.78** 除息日（約佔跌幅 0.8 個百分點）；（2）EIA 11/18 公布上週美國原油庫存大增 **340 萬桶**（遠超市場預期的 +5.8 萬桶）、汽油大增 **520 萬桶**，壓低 WTI 原油跌 3.2% 至 83.26 美元；（3）傳接近以 **50 億美元**收購墨西哥灣深水油商 **Beacon Offshore Energy**。（https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ，台北時間 2026-11-18；https://www.nationthailand.com/news/world/40073656 ，台北時間 2026-11-19；https://www.bicmagazine.com/industry/investment-banking/chevron-closes-in-on-5b-beacon-deal/ ，台北時間 2026-11-18）
- 本站漏掉的：約五分之一的跌幅屬於除息日技術性除權息，其餘主要與整個能源板塊（XLE、XOM、CNQ）因 EIA 庫存意外暴增而集體下挫同步。

### CNQ｜Canadian Natural Resources（CNQ）正規盤隨油價重挫跌 4.63%（$45.53），盤後 +3.2% 無新公告或報告（找不到來源）
- 事實：CNQ 美東 11 月 18 日正規盤隨北美能源股重挫收跌 **4.63%**（$45.53，多倫多證交所跌 4.06% 至 C$65.52），除油價大跌外，市場亦在消化其 11/16 宣布以 **25.3 億加元**收購 **Advantage Energy** 之現金支出。（https://www.nationthailand.com/news/world/40073656 ，台北時間 2026-11-19；https://www.newsfilecorp.com/release/324091/Canadian-Natural-Resources-Limited-Enters-into-Agreement-to-Acquire-Advantage-Energy-Ltd ，台北時間 2026-11-17）
- 事實（盤後 +3.2%）：查遍公司官網、交易所公告與主流新聞，美東 11/18 盤後 **沒有任何 CNQ 新聞、財報或分析師調評**（找不到來源）。
- 推理：正規盤急跌近 5% 後，盤後低流動性搓合出現 +3.2% 跳動，應屬美加掛牌價差或低量買盤回補，非基本面突發事件。

---

### AN｜AN-1：最近 3 小時內（台北 08:40–11:40）無新增分析師調評；補充本週 AVGO、NVDA、AAPL 最新券商動向
- 事實：檢索最近 3 小時（台北 08:40–11:40／美東 11/18 19:40–22:40 深夜時段），AI 供應鏈與美國市值前 20 大公司並無新發布的券商評等調整（找不到來源）。
- 事實（補充 11/18 與本週已公開可查證報告）：
  - **NVDA（Moody's Ratings 11/18）**：維持 Aa1 債信評等，但將展望由 **Positive 調降至 Stable**，點名黃仁勳驟然離職後的接班真空與美國政府調查風險。（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ，台北時間 2026-11-19）
  - **NVDA（Summit Insights 分析師 Kinngai Chan，11/18）**：據報導摘要將 NVDA 由 **Buy 調降至 Hold**，理由是執行長變動後的產品路線不確定性與 2027 年客製化 ASIC 競爭（Investing.com 原文頁面設 403 阻擋，完整可直連網址：找不到來源）。
  - **AVGO（Rothschild & Co Redburn，本週）**：將博通由 **Buy 調降至 Neutral**，下修看法（$595 → $398），理由是質疑其對 OpenAI、Anthropic 等需大量自籌資金之 AI 實驗室客戶的獲利持續性（TipRanks／Investing.com 設 403 阻擋，單篇直連網址：找不到來源）。
  - **AAPL（YR Research，11/18 經 TradingView 轉載 Seeking Alpha 摘要）**：將蘋果評等由 **Sell 調升至 Hold**，稱其現金流與客戶黏著度具防禦性。（https://www.tradingview.com/news/seekingalpha:d985f509f094b:0-sa-analyst-upgrades-downgrades-nvda-aapl-smci-tsla/ ，台北時間 2026-11-19，HTTP 200 確認）

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）正式刊登聯邦公報生效，馬來西亞表態尋求釐清規範（更新）
- 事實：美國商務部工業安全局（BIS）暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢）。新規增訂 § 744.24 遠端存取終端用途管制，限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則。根據中央社 11 月 19 日報導，**馬來西亞**已正式表態尋求與美方釐清資料中心服務規範對當地業者的適用邊界。（https://public-inspection.federalregister.gov/2026-23529.pdf ，台北時間 2026-11-19，HTTP 200；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ，台北時間 2026-11-17，HTTP 200）

### POL-2｜美國財政部 OFAC 制裁伊朗網路、白宮、USTR 與 CMS CRUSH 規則（無新進展）
- 事實：美國財政部 OFAC 於 11/18 宣布 **「Operation Economic Outcast」** 制裁真主黨與伊朗聖城軍黃金及現金網路（https://home.treasury.gov/news/press-releases/sb0692 ，台北時間 2026-11-19）；USTR 代表 Jamieson Greer 重申美國優先供應鏈韌性（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）；白宮發布亞洲經濟協議事實清單（https://www.whitehouse.gov/fact-sheets/2026/11/fact-sheet-president-donald-j-trump-secures-historic-economic-deals-for-american-workers-and-strengthens-americas-leadership-in-asia/ ）；CMS CRUSH 反詐欺提案（`2026-23461`）今日（11/19）刊登聯邦公報進入 60 天意見徵詢至 2027-01-19（https://www.cms.gov/newsroom/fact-sheets/comprehensive-regulations-uncover-suspicious-healthcare-crush-proposed-rule-cms-6098-p ；https://public-inspection.federalregister.gov/2026-23461.pdf ）。

---

### TW-1｜台股 11/19 盤中賣壓進一步擴大！本站即時報價截至 11:26 已跌破 39,000 點至 38,611（-3.9%），新台幣貶破 33 元觸 33.04（重大更新）
- 事實：台股今日（11/19）以 40,146 點開低（-49.18 點）後，雖一度在台積電、聯發科撐盤下翻紅，隨後賣壓沉重連破 4 萬與 39,000 點整數關卡。中央社 11/19 早盤報導最低 **39,379.04 點**（台積電早盤低見 **2,155 元**），經濟日報 10:13 進一步報破 **39,030 點**，而截至 **11:26 本站即時行情已續挫至 38,611 點（-3.9%，單日跌幅超過去年平均日波動的 2 倍）**，午盤前部分報導並指台積電盤中震盪在 2,125–2,160 元區間、摜破年線。台北匯市新台幣以 **32.96 元**開盤後截至上午已貶破 33 元觸及 **33.04 元**。（https://www.cna.com.tw/news/afe/202611190035.aspx ，台北時間 2026-11-19，HTTP 200；https://money.udn.com/money/story/5616/9888194 ，台北時間 2026-11-19 10:13，HTTP 200；https://www.cna.com.tw/news/afe/202611190032.aspx ，台北時間 2026-11-19 09:15，HTTP 200；https://www.rti.org.tw/news?uid=3&pid=1052376 ，台北時間 2026-11-19，HTTP 200）
- 事實（千金股與 11/18 籌碼）：信驊（5274）盤中急殺逾 9% 至 8,775 元、創意（3443）開盤即鎖死 6,000 元連續第 4 根跌停（11/18 上市櫃共爆 9 起違約交割合計 4.26 億元，創意占 9,453 萬元）；11/18 外資現貨賣超 765.64 億元（賣超台積電 15,453 張），期貨三大法人合計淨空單 **-7,322 口**（外資 -99,438、投信 +93,573、自營 -1,457）。（https://finance.ettoday.net/news/3274699 ，台北時間 2026-11-19 09:46；https://www.cna.com.tw/news/afe/202611180304.aspx ，台北時間 2026-11-18 18:30，HTTP 200）

### TW-2｜晶圓代工報價調漲外溢至 IC 設計（偉詮電明年擬漲價）（新）；元太科技資安事件與台積電信用額度傳聞（無新進展）
- 事實：中央社 11 月 19 日即時產經快訊報導，受晶圓代工報價調漲成本轉嫁影響，IC 設計廠**偉詮電**預計於明年初調漲產品價格；另 **11/18 晚間**電子紙龍頭**元太科技（8069）**重訊公告資訊系統疑遭駭客攻擊，初估對營運暫無重大影響。（https://www.cna.com.tw/news/afe/202611180336.aspx ，台北時間 2026-11-18，HTTP 200；偉詮電漲價快訊見中央社 11/19 產經頭條列表，單篇內文連結：找不到來源）
- 傳聞（無新進展）：台積電依客戶資產負債表設 AI 信用額度、超額須預付現金之傳聞仍未被公司證實（外媒轉述《工商時報》：https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ，台北時間 2026-11-18）。

### TW-3｜SK 海力士與愛德萬 V93000 EXA Scale QX 動態、台韓出口數據（無新進展）
- 事實：愛德萬（Advantest）11 月中旬發表 36 槽四卡籠架構 **V93000 EXA Scale QX** 測試頭鎖定高功耗 AI 晶片；韓國 11 月前 10 天出口年增 **111.9%**（半導體暴增 **331.2%**），台灣 10 月出口年增 **58.9%** 至 967.6 億美元。（https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ；https://cyprusshippingnews.com/2026/11/13/south-koreas-exports-surge-toward-1-trillion-as-chip-shipments-more-than-quadruple/ ）

---

### EARN-WMT｜沃爾瑪（WMT）Q3 FY27 財報（今晚美東 11/19 07:00／台北 20:00，補充可點開共識來源）
- 事實：美東 **2026-11-19 07:00 財報、08:00 電話會議**（台北 **11/19 20:00／21:00**）；TradingView 彙整市場共識預期營收約 **1,872.5 億～1,873.8 億美元**（年增約 4.3%–5.4%）、調整後 EPS **0.64 美元**（公司上季給的 Q3 財測為 EPS 0.62–0.64 美元、常數匯率淨銷售成長 3.0%–3.75%）；本站 `upcoming.json` 顯示選擇權隱含波動 **±5.89%**。（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ，HTTP 200；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，HTTP 200）

### EARN-BABA｜阿里巴巴（BABA）Q2 FY27 財報（今晚美東 11/19 盤前／台北約 20:00–21:00）
- 事實：美東 **2026-11-19 盤前**（台北 **11/19 20:00–21:00**）；Barchart 與市場 previews 彙整預期截至 9/30 季度營收約 **404.1 億～404.8 億美元**（約人民幣 2,698.5 億元，年增 8.9%）、調整後 EPS 約 **1.56～1.64 美元**（本站財報日曆列 1.56 美元）。（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ，台北時間 2026-11）

### EARN-PDD｜拼多多（PDD）Q3 2026 財報（今晚美東 11/19 盤前／台北約 20:00–21:00，無新進展）
- 事實：美東 **2026-11-19 盤前**（台北 **11/19 20:00–21:00**）；市場共識預期營收約 **171.7 億美元**（約人民幣 1,155 億～1,156.4 億元）、EPS 約 **2.61～2.77 美元**（本站財報日曆列 2.61 美元；Moomoo／PDD 官網設 403 阻擋，單篇新聞直連網址：找不到來源）。

### EARN-INTU / ROST / GAP / WSM｜今日（11/19）美東盤前與盤後其餘財報（無新進展）
- 事實：
  - **WSM（盤前／台北 11/19 20:00）**：共識營收約 **20.0 億美元**、EPS 約 **2.17–2.19 美元**（單篇直連網址：找不到來源）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收約 **43.0 億美元**、Non-GAAP EPS **2.46–2.47 美元**（公司原財測 2.44–2.48 美元），選擇權預估波動約 ±8.9%–10.5%。（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）
  - **ROST（盤後／台北 11/20 05:00）**：共識營收約 **62.0 億～62.5 億美元**、EPS **1.82–1.87 美元**（單篇直連網址：找不到來源）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收約 **40.1 億～40.2 億美元**、調整後 EPS **0.76–0.78 美元**（公司原財測淨銷售成長 1.5%–2.5%）。（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）

### EARN-HPE / ZM / BBY / BURL / DKS / ADI / MDT / DELL / HPQ / ZS / DE｜11/23–11/25 財報（補齊漏掉公司）
- 事實：
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（本站財報日曆列 1.17，公司財測 1.20–1.30；選擇權波動 ±9.7%：https://247wallst.com/investing/2026/11/09/dell-and-hpe-were-ai-winners-until-the-selloff-can-earnings-put-them-back-on-track/ ）；**ZM** 市場估（預期）11/23 盤後公布，共識營收約 **12.8 億美元**、EPS **1.49 美元**（MarketBeat 彙整）。
  - **11/24 盤前（台北 11/24 21:00）**：**ADI** 共識營收 **43.2 億美元**、EPS **3.89 美元**（本站隱含波動 ±8.04%）；**MDT** 本站列 EPS **1.34 美元**；**BBY** 共識營收 **98.8 億美元**、EPS **1.49 美元**；**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**；**DKS** 共識營收 **50.8 億美元**、EPS **1.42 美元**（多數來自 MarketBeat／TradingView 彙整頁面，單篇新聞直連網址：找不到來源）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億美元**（公司財測約 490 億）、調整後 EPS **6.41–6.63 美元**（本站列 6.41，隱含波動 ±14.78%；https://247wallst.com/investing/2026/11/09/dell-and-hpe-were-ai-winners-until-the-selloff-can-earnings-put-them-back-on-track/ ）；**HPQ** 共識營收 **153.0 億～155.8 億美元**、EPS **0.74–0.76 美元**；**ADSK** 共識營收 **21.3 億美元**、EPS **3.07 美元**；**WDAY** 共識營收 **26.9 億美元**、EPS **2.74–2.75 美元**；**ZS**（部分行事曆排 11/24 或 12 月初，共識營收 **9.38 億美元**、EPS **0.95–1.00 美元**）。
  - **11/25 盤前（台北 11/25 21:00）**：**DE** 共識營收 **103.4 億～104.0 億美元**、EPS **4.07 美元**（本站隱含波動 ±7.31%）。

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險。（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ，HTTP 200）

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（強烈偏升息，無新進展）
- 事實：Waller 於 11/18 受訪指出聯準會可能需要「shock people」壓抑 3% 通膨預期固著，12/8–9 會議應考慮一次升息 50 基點。（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ，HTTP 200）

### FED-3｜聯準會理事 Michael S. Barr 與紐約聯準銀行總裁 John Williams（11/18 出席紐約聯準銀行活動，更新）
- 事實：Barr 11/18 在紐約聯準銀行演說指通膨仍過高、若經濟按預期演進適合進一步升息（偏升息）（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ，HTTP 200）；同日紐約聯準銀行總裁 John Williams 亦出席紐約聯準銀行「Making Missing Markets」活動，延續其主張漸進審慎、反對驟然劇烈調整的立場（單篇講稿全文：找不到來源）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼約 90%–95%、升息 2 碼約 5%–10%（無新進展）
- 事實：美元指數受升息預期推升至 103.97（19 個月新高），壓低金銀與商品。（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ，HTTP 200）

---

### CALL-NVDA｜輝達（NVDA）Q3 FY27 法說會：營收 1,158 億美元、Vera Rubin 首季貢獻近 200 億、下季財測排除中國（無新進展）
- 原話：`"Our momentum is real... Customers, suppliers, and partners are 100% behind us. We’ve got this."`（https://www.cnbc.com/2026/11/18/nvidia-stock-earnings.html ，HTTP 200）

### CALL-PANW｜Palo Alto Networks（PANW）Q1 FY27 法說會：NGS ARR 年增 66%，45 億美元併購 Applied Compute（無新進展）
- 原話：`"As AI reshapes the threat landscape, we must continually evolve to protect our customers and enable them to adopt AI securely."`（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200）

### CALL-LOW｜Lowe's（LOW）Q3 2026 法說會：同店 +1.8%，2.5 億美元關稅退稅全數再投資（無新進展）
- 原話：`"We delivered strong top-line growth of over 9%, led by our sixth consecutive quarter of positive comparable sales, with continued momentum in Pro, online and home services."`（https://corporate.lowes.com/sites/lowes-corp/files/2026-11/q3-2026-press-release-v1.pdf ）

### CALL-TGT｜Target（TGT）Q3 2026 法說會：同店成長 5.6%、全年 EPS 指引上調至 10.65–11.40 美元（無新進展）
- 原話：`"Our third-quarter results reflect continued progress against our strategic priorities, centered on serving busy families with our signature blend of style, design and value."`（https://www.prnewswire.com/news-releases/target-corporation-reports-third-quarter-earnings-302942872.html ）

### CALL-TJX｜TJX Companies（TJX）Q3 FY27 法說會：同店成長 4%，看好 Q4 Marmaxx 加速（無新進展）
- 原話：`"Consolidated comparable sales grew 4%, driven by continued strength at HomeGoods, TJX Canada, and TJX International, and we saw improved sales at Marmaxx. Importantly, we expect further improvement at Marmaxx in the fourth quarter."`（TJX 官網 PDF 受 403 阻擋，單篇直連網址：找不到來源）

---

### SENT-1｜NVDA（r/wallstreetbets）— 財報大好卻走弱，社群嘲諷「沒有驚喜就是利空」與黃仁勳迷因（補齊可點開討論串網址）
- 討論內容與情緒：11/18 財報達標但股價回跌，r/wallstreetbets 討論串混雜對科技股連月回檔的疲勞感與「nothing burger」嘲諷，同時熱議輝達 100 億美元參與 Anthropic 股份與管理層風波（熱度自 11/17–18 升溫；情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xyw3ym/what_are_your_moves_tomorrow_november_18_2026/ ，HTTP 200 確認）。

### SENT-2｜Anthropic（ANT）IPO（r/wallstreetbets）— 懷疑論濃厚，擔心散戶成早期創投「退出流動性」（補齊可點開討論串網址）
- 討論內容與情緒：那斯達克確認 ANT 於 11/19 掛牌且定價 83 美元後，WSB 討論串對史上最大 IPO 普遍抱持警覺與諷刺態度，警告小心成為風投與避險基金的退出流動性（熱度自 11/16–18 急升；情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xtuclv/nasdaq_confirms_anthropics_shares_will_begin/ ，HTTP 200 確認）。

### SENT-3｜PANW／科技股財報（r/stocks）— 肯定資安成長動能但對 AI 估值審慎（補齊可點開討論串網址）
- 討論內容與情緒：r/stocks 每日討論串肯定 PANW 財報與 NGS ARR 成長，但整體對升息與 AI 高資本支出下的軟體股估值仍偏審慎（熱度自 11/18 升溫；情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ，HTTP 200 確認）。

### SENT-4｜UNH／管理式醫療（r/stocks）— CMS 規則衝擊下偏悲觀觀望（無新進展）
- 討論內容與情緒：UNH 等醫療保險股受 CMS CRUSH 規則影響連日承壓，散戶偏悲觀（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-5｜台股跌破 39,000 點與創意／記憶體殺盤（PTT 股板）— 違約交割與當沖恐慌升高（補齊可點開討論串網址）
- 討論內容與情緒：11/18 盤後成交值排行與違約交割公告（創意等 4 檔、穩懋等 5 檔）加上今日（11/19）盤中跌破 4 萬與 39,000 點、創意連 4 根跌停，PTT 股板恐慌防禦討論大幅升溫（熱度自 11/18 急升；情緒，非事實；https://www.pttweb.cc/bbs/Stock/M.1794981623.A.7D5 ，HTTP 200 確認）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%）。
  - **bea.gov 原文網址**：https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 （HTTP 200 確認）
  - **原文那一句（13 字）**：`"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`
  - 補充：之所以高於本站抓到的 9 月核心 CPI 年增 2.6%，主因 2026 年住房通膨降溫拉低權重較大的 CPI，而權重較高的醫療服務、金融與軟體科技服務推高了 PCE（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ）。

### TASK-B2｜11/19 台股尚未收盤（截至 11:26 盤中續殺至 38,611 點／-3.9%），附上 11/19 盤中最新與 11/18 官方收盤確認數字
- 事實（時間狀態說明）：目前為 **台北時間 2026-11-19 11:42**，台股集中市場與台北匯市仍在盤中（13:30／16:00 才收盤），證交所／期交所 11/19 買賣超與台指期未平倉須待 **今日下午 15:00 後**公布，央行官方新台幣收盤價須待 **16:00 後**公布。
- 事實（11/19 盤中最新）：台股開低後急殺跌破 4 萬與 39,000 點，中央社早盤報最低 **39,379.04 點**、經濟日報 10:13 報 **39,030 點**、本站即時報價 11:26 續挫至 **38,611 點（-3.9%）**；新台幣 32.96 元開盤後盤中已貶破 33 元觸及 **33.04 元**。（https://www.cna.com.tw/news/afe/202611190035.aspx ；https://money.udn.com/money/story/5616/9888194 ；https://www.cna.com.tw/news/afe/202611190032.aspx ）
- 事實（11/18 官方收盤確認）：加權指數收 **40,194.91 點（+102.80 點 / +0.26%）**；外資現貨賣超 **765.64 億元**；期交所三大法人台指期淨部位合計 **-7,322 口**（外資 -99,438 口、投信 +93,573 口、自營商 -1,457 口）；新台幣 11/18 收 **32.947 元**。（https://www.cna.com.tw/news/afe/202611180304.aspx ，HTTP 200）

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；補充掛牌前夕關聯股收盤表現
- 事實（掛牌時程）：Anthropic（代號 **ANT**）已定價 **每股 83.00 美元**（發行 9.8 億股、IPO 募資 **813.1 億美元**、完全稀釋估值約 **1.5 兆美元**），將於 **美東 2026-11-19 09:30（台北 11/19 22:30）** 正式掛牌；截至台北時間 11/19 11:42 美股尚未開盤，首日開盤價、收盤價與成交量將於明早 05:00 收盤後產生。（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，HTTP 200；https://www.cna.com.tw/news/afe/202611190043.aspx ，HTTP 200）
- 事實（11/18 收盤關聯股表現）：掛牌前夕美東 11/18 收盤，**CoreWeave（CRWV）跌 4.13%、IREN 跌 3.61%、Nebius（NBIS）小漲 0.87%、Oracle（ORCL）大致持平**；同日晶片股東 **NVDA 收跌約 2.9%**，**AVGO、AMD 逆勢上漲約 4%–5%**。（https://247wallst.com/investing/2026/11/18/coreweave-falls-5-despite-nvidia-sticking-to-its-financing-commitments-nebius-dips-oracle-holds-steady/ ，HTTP 200）

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字
- 事實（ECB 口徑）：ECB 11/18《金融穩定評估》Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（基於 LSEG 10/26 券商共識），指多數美國超大規模雲端業者 2026 年自由現金流因 AI 資本支出大於營運現金流而轉負（此表層 FCF 口徑未納入未起租的表外租賃；表外承諾逾 4 兆美元係於圖表 A 與註腳 6 依 ASC 842 單獨揭露）。（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200）
- 事實（四巨頭截至 2026-09-30 最新一季財報實際 FCF 與租賃差異）：
  - **Meta（Q3 2026）**：OCF $32.79B − CapEx（**含融資租賃本金**）$34.91B = **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）。
  - **Alphabet（Q3 2026）**：OCF $42.29B − 現金 PP&E $51.36B（不含租賃）= **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）。
  - **Amazon（Q3 2026／TTM）**：Q3 單季 OCF $42.42B、淨現金 PP&E $75.93B（隱含單季 **-$33.51B**）；公司自報 **TTM FCF = -$42.36B**（僅扣淨 PP&E，另於附註揭露 Q3 新增融資租賃資產 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）。
  - **Microsoft（Q1 FY27）**：OCF $58.02B − 現金 PP&E $39.37B = **+$18.6B（仍為正）**；若改扣含新起租融資租賃之總資本支出 $45.2B，仍為正值約 +$12.8B（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### TASK-B5｜WMT、BABA、PDD 今晚 20:00–21:00 才公布 11/19 財報；附上最新共識（含來源名稱）、公司上季指引與關稅／消費原話
- 事實（公布時間）：三家均為 **美東 11/19 盤前（台北時間今晚 11/19 20:00–21:00）** 公布，截至台北 11:42 尚未發布實際財報。
- 事實（市場預期＋上一季指引＋對關稅與消費的原話）：
  1. **沃爾瑪（WMT，Q3 FY27）**：TradingView 彙整市場共識營收 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（公司上季財測為 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）。針對先前 IEEPA 關稅退稅（約 29 億美元資格）與消費者行為，財務長 John David Rainey 表示顧客正權衡取捨、執行長 John Furner 則強調消費者感受到壓力因此全力把關稅退稅投入降價：
     - 原話（John Furner）：`"Customers are feeling some pressure, so we're proud of our investments... We'll do everything we can to keep prices as low as we can for customers throughout the rest of the year."`（https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ；https://www.businessinsider.com/walmart-using-tariff-refund-price-cuts-customer-experience-sales-2026-8 ，HTTP 200）
  2. **阿里巴巴（BABA，Q2 FY27）**：Barchart 與券商 previews 彙整共識營收約 **404.1 億～404.8 億美元**（約人民幣 2,698.5 億元，年增 8.9%）、調整後 EPS **1.56～1.64 美元**；市場聚焦中國國內消費疲軟下的電商補貼戰與阿里雲 AI 資本支出。（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ）
  3. **拼多多（PDD，Q3 2026）**：市場共識營收約 **171.7 億美元**（約人民幣 1,155 億～1,156.4 億元）、EPS **2.61～2.77 美元**；受小額免稅（de minimis）貿易新規調整影響 Temu 跨境成本與中國國內消費價格戰，市場預估淨利率承壓。（管理層上季原文網頁設 403 阻擋，單篇直連網址：找不到來源）

---

### NEXT-1｜事件：11/19 台股盤中急殺至 38,611（-3.9%）＋台幣破 33 元＋BIS 遠端算力管制今日生效引發東南亞釐清（更新）
- 推理：
  - 最先受影響的資產：USD/TWD（33.04）、台灣高融資千金股與權值股、以及東南亞（馬來西亞、新加坡、印尼、泰國）資料中心租賃與算力轉租合約。
  - 傳導路徑：當美國 BIS `2026-23529` 今日正式生效且馬來西亞政府緊急向美方釐清資料中心服務規範，跨國雲端代工與轉租商必須新增客戶 KYC 與 1,200 萬 TPP 算力稽核成本；同時台股破年線疊加台幣貶破 33 元觸發外資被動式提款與融資斷頭賣壓：
    - 美股：**NVDA、ORCL、CRWV、SMCI、EQIX**（受東南亞資料中心合規成本與客戶審核拉長影響）。
    - 台股：**台積電 (2330)、創意 (3443)、信驊 (5274)、緯穎 (6669)、廣達 (2382)**（外資提款與高本益比／違約交割重災區）。
  - 大家還沒注意到的間接受害者：**已重金在馬來西亞柔佛州／新加坡擴廠的台灣散熱、機櫃與電源廠（以及未受 2026-23529 點名但合規能力不足的周邊國家小型機房）**——雖然越南未被點名（中央社），但若美方嚴格執行最終用戶追蹤，建置遞延會先反映在訂單認列時程拉長。

### NEXT-2｜事件：ECB 證實三大雲端巨頭（AMZN、GOOGL、META）2026 FCF 轉負＋表外承諾逾 4 兆美元（更新）
- 推理：
  - 最先受影響的資產：投資級科技長債利差（尤其 10–30 年期）與 Oracle 5 年期 CDS。
  - 傳導路徑：ECB Box 3 揭露 4 兆美元表外承諾未入帳、且只有微軟單季仍維持正 FCF，債市會要求更高的新債票息溢酬並限縮科技巨頭庫藏股規模（除了靠舉債硬撐的業者），進而壓抑美股大型權值回購支撐力：
    - 美股：**ORCL、AMZN、GOOGL、META、CRWV**。
    - 台股：**台積電 (2330)、鴻海 (2317)、廣達 (2382)、緯穎 (6669)、台達電 (2308)**。
  - 大家還沒注意到的間接受害者：**歐元區與美國傳統非科技投資級債發行人（公用事業、電信、製造業）**——當美國雲端巨頭同時抽走美元與歐元投資級債市胃納，傳統產業再融資成本被迫抬高。

### NEXT-3｜事件：克里米亞大橋第 3 度遇襲中斷＋歐盟延後甲烷法規兩年＋美軍封鎖伊朗公海轉運（新）
- 推理：
  - 最先受影響的資產：歐洲 TTF 天然氣、油輪／成品油航運運費、海運戰爭險費率。
  - 傳導路徑：歐盟延後甲烷新規雖短線替 LNG 進口鬆綁，但也變相承認今冬至明年天然氣供應脆弱；配合克赤大橋受損與荷莫茲公海船對船攔截，運輸摩擦成本很難快速歸零，可能使歐美核心與能源通膨黏著度高於預期：
    - 美股：**LNG（Cheniere）、FRO（Frontline）、STNG（Scorpio Tankers）、DAL、UAL**。
    - 台股：**長榮航 (2618)、華航 (2610)、陽明 (2609)、裕民 (2606)、台塑化 (6505)**。
  - 大家還沒注意到的間接受害者：**依賴廉價俄油／中東 LPG 轉運的亞洲煉油與石化下游（如印度與東南亞民營煉油廠）**——一旦公海 STS 船對船轉運遭實質攔截，影子船隊折價紅利將快速消失。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 已由 60% 降至 45%）」
- 最強反方證據：BEA 官方新聞稿實證 9 月核心 PCE 年增已是 **3.1%**（`https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026`），且 The Conference Board 預估 10 月將進一步升至 **3.3%**（`https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026`），連本站自己 PCE 卡片上的即時模型都估 10 月年增 **3.2%**。
- 另一種同樣說得通的解釋：去年（2025 年）10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法公布正規年增率（只公布月增），這題將和 10 月 CPI 一樣變成「無法判定」；但只要有公布數字，很難低於 3.0%。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：我維持落在 2.4%–3.0% 僅約 **30%**（比你修正後的 45% 仍低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露 3 家一線雲端商最新季／TTM FCF 已轉負且表外承諾逾 4 兆美元，Oracle 5 年期 CDS 已飆至高收益等級，且今日（11/19）台股單日盤中重挫 **-3.9%（38,611）**、新台幣貶破 **33.04**，顯示風險偏好已率先在亞股與外匯裂解。
- 另一種同樣說得通的解釋：就算 12/9 聯準會只升 1 碼、美國高收益債指數因能源權重撐盤未破 4%，「投資級科技債利差走寬＋表外租賃收縮＋亞股千點斷頭」就足以形成實質的「風險升級」，不必等到 HY OAS 破 4% 才算。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：我給「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：雖然你因為封鎖升級保留較高區間信心，但 11/18 美國 EIA 原油單週累庫 340 萬桶、汽油暴增 520 萬桶後，WTI 直接跌到 **83.26 美元**、布蘭特跌至 **88.86 美元（-4.6%）**，貼近 80 美元下緣；同日全球商品（黃金 -4.2%、銅 -5.9%）在強美元 103.97 與聯準會升息 2 碼陰影下集體重挫。
- 另一種同樣說得通的解釋：市場發現這場美伊有限封鎖下「荷莫茲海峽油輪運量其實大體維持接近戰前水準」（Global Banking & Finance 11/19 援引數據），因此油價向下跌破 80 美元的機率其實不亞於衝破 100 美元。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **APEC 深圳川習／美俄會談公報（11/19）**。
- 機率估計：我維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」
- 最強反方證據：除財報與法說會未見執法處分外，川普今日（11/19）在 APEC 深圳表示與習近平晚宴整晚談 AI、「僅簡短提及黃仁勳」，若是美中最高層級國家安全重大違規案，兩國領袖不大可能輕描淡寫帶過（中央社 11/19 標題列表）；且 Moody's 報告亦將重點放在缺乏接班計畫與未定調查風險。
- 另一種同樣說得通的解釋：先因個人治理違規遭董事會迅速切割，隨後才引發美國政府例行詢問；管理層順勢將中國資料中心收入歸零以防堵 2027 年新增政治風險。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節，11 月下旬～12 月初）**。
- 機率估計：我估「直接因中國出口調查」**40%–45%**，「個人治理觸發＋連帶揭露審查」**55%–60%**（與你目前 45%–50% 接近）。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（無新進展；補入 ECB Box 3 量化基準）
- 事實：ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**（已超過帳上負債），且投資級科技長債利差已相對於同評級企業債走寬（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q「Commitments and Contingencies / Uncommenced Leases」追蹤與 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜缺少「非公開交易 BDC 限額贖回（Gating）與避險基金槓桿」監測（無新進展）
- 事實：聯準會 FEDS Notes（2026-10-14）指半流動性非公開 BDC 持有 93.4% 私募信貸、部分觸發 5% 贖回上限。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜缺少「高集中度雲端／金融基建中斷與 SEC Item 1.05 資安事件」警報（無新進展）
- 推理：只需監測 SEC 8-K Item 1.05 是否涉及高集中度第三方基建（AWS、Azure、GCP、Cloudflare、DTCC），即可過濾出系統性中斷事件。免費資料源：CISA KEV JSON（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）＋ SEC EDGAR。

### BLIND-4｜「台股籌碼風向計」尚未合計三大法人台指期淨口數，亦未統計證交所單日違約交割金額（對照 11:25 線上版確認）
- 事實：檢視 11/19 11:25 線上「台股籌碼風向計與斷頭警戒」，目前只對 `外資台指期未平倉 -99,438 口` 亮紅燈，並將同列於文字中的投信 `+93,573`、自營 `-1,457` 分開呈現，未直接加總為 **「三大法人合計淨空單 -7,322 口」**，亦未納入證交所每日違約交割統計（11/18 爆 9 起合計 4.26 億元）。免費資料源：期交所「三大法人區分各期貨契約交易資訊」與證交所「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」（無新進展）
- 推理：建議在「IPO 觀察」補上大型 IPO 納入主要指數（S&P 500、Nasdaq-100）時程與被動 ETF 權重排擠效應說明。

---

### SITE-1｜`forecast.json` 寫「9 月核心 PCE 數字：查無」，但本站自己的 PCE 卡片其實已顯示「前值 3.1%」（新發現）
- 本站寫了什麼：`research_feed/forecast.json`（更新於 `2026-11-19 07:03 台北`）第 130 行寫著 `9 月核心 PCE 數字：查無。`；同時 `claude_notes.md` 第 14 行亦表示無法查證 9 月核心 PCE 為 3.1%。
- 正確應該是什麼：讀取 `https://wallstreet-sentinel.pages.dev` 線上版（11/19 11:26 更新）之 `PCE 物價（台北 11/25 21:30）` 卡片表格，站上其實已經明確顯示 **`核心 PCE 月增 前值 0.3%`、`核心 PCE 年增 前值 3.1%`、`PCE 月增 前值 0.5%`**，且完全符合 BEA 官網新聞稿（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）。建議把兩邊的資料管線打通。

### SITE-2｜11/19 `10:33 緊急加班` 語音稿誤把「今天（11/19）台股盤中跌幅」講成「台股昨天收盤附近少了 3.4%」（新發現）
- 本站寫了什麼：線上總覽最上方 `🚨 緊急加班（最後更新 11-19 10:33）` 語音文字稿寫道：`「台股昨天收盤附近比前一天少了三點四個百分點」`（並同步重複 06:33 早班「還找不到能源與醫療股開盤跳空與前晚油價下跌原因」）。
- 正確應該是什麼：台股「昨天（11/18）」收盤其實是**小漲 +102.80 點（+0.26%）收在 40,194.91 點**（https://www.cna.com.tw/news/afe/202611190027.aspx ）；那段 `-3.4%`（最新至 11:26 已擴大至 `-3.9%`、38,611 點）其實是**今天（11/19）上午的盤中即時跌幅**。語音稿在美股（資料日 11-18）與台股（資料日 11-19）混用時，把今天台股盤中跌幅誤說成了「昨天收盤附近」。

### SITE-3｜`api/gemini_ask`（11:31 即時版）仍僅標示 `CNQ +3.2%（盤後）`，未附正規盤收跌 -4.63%（已列入待辦，確認仍存在）
- 本站寫了什麼：`https://wallstreet-sentinel.pages.dev/api/gemini_ask`（台北 11:31）仍寫 `### CNQ｜CNQ（Canadian Natural Resources）今天 +3.2%（盤後）`，未呈現正規盤重挫 -4.63% 的完整脈絡。

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆，對照 11:26／11:31 線上版核對
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳川習與美中俄三方互動進行中；美東盤前（台北 20:00–21:00）**WMT、BABA、PDD、WSM** 財報；台北約 21:00 **南非央行（SARB）利率決策**；美東 09:30（台北 22:30）**Anthropic (ANT)、MapLight (MPLT)** 掛牌；美東 13:00（台北 11/20 02:00）**美債 10 年期標售（增額）$19B**；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP** 財報。（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）
  2. **11/20（五）**：**台灣經濟部 10 月外銷訂單**（台北 16:00）；**美股月選擇權到期（OPEX）**；**SanDisk (SNDK) 1 拆 8 分割**。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM** 財報。
  5. **11/24（二）**：美東盤前（台北 21:00）**ADI、MDT、BBY、BURL、DKS**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY、ZS**。
  6. **11/25（三）**：美東盤前（台北 21:00）**DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與 10 月耐久財訂單；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/30（一）**：**月底資產再平衡**。
  10. **12/01（二）**：美東 10:00（台北 23:00）**10 月 JOLTS 職位空缺**；**CRWD、NTAP** 財報；**韓國 11 月出口初值**。
  11. **12/03（四）**：美國參議院資料中心聽證。
- 對照本站 11/19 11:26／11:31 線上版核對：
  - **正確部分**：`未來 14 天事件`（11:26）與 `接下來 72 小時`（11:31 `upcoming.json`）已正確列出 WMT/BABA/PDD、ANT/MPLT、HPE、ADI、MDT、DELL、HPQ、DE、11/19 美債 10Y 增額、H.4.1、11/20 OPEX、11/25 GDP 與 PCE、11/30 月底再平衡、12/01 JOLTS；`休市與提早收盤` 亦正確列出 11/26 休市與 11/27 半天交易。
  - **漏掉部分**：`upcoming.json`（72 小時／7 天）仍漏掉今晚盤後的 **INTU、ROST、GAP**（市值皆逾百億美元）、11/20 **台灣 10 月外銷訂單**、11/23 **ZM**、11/24 **BBY/BURL/DKS/ADSK/WDAY**；`未來 14 天事件` 仍漏掉 **11/19 南非央行、11/21 韓國 20 日出口、11/25 聯準會褐皮書、11/26 韓國央行**，且未在該清單內併註 **11/26–27 感恩節休市與提早收盤**。

---

### CODE-1｜wsb/analytics/entry_env.py：第 73–77 行在公開網頁直接輸出受版權限制的 FRED 序列 `BAMLH0A0HYM2` 原始數值
- 檔案路徑與行號：`wsb/analytics/entry_env.py` 第 73–77 行（對應 `settings.yaml` 第 148–150 行）。
- 那一行在做什麼：讀取 `_fred(eng, "BAMLH0A0HYM2")` 後，於第 76 行直接格式化輸出 `f"{hy.iloc[-1]:.2f}%（3 個月 {ch:+.2f}）"` 供 `tools/site_entry.py` 渲染至公開網站。
- 為什麼有問題：違反本站授權顯示規範——`settings.yaml:148-150` 明文將 `BAMLH0A0HYM2` 列於 `fred_restricted`（「公開網站與公開 AI 評論只顯示衍生指標（百分位、變化方向），不顯示原始數值」），此處卻直接對公開網站輸出原始利差與基點變動。
- 建議怎麼改：改為輸出歷史百分位與收窄／擴大方向（例如「高收益債利差近 3 個月收窄，處於歷史第 X 百分位」），不露出原始數值。
- 確定度：高。

### CODE-2｜wsb/bot/slides.py：第 660、667 行出現禁用詞（「減＊」、「賣＊」），且第 590–645 與 1008–1020 行存在頁碼／`None` 與財報判定邏輯缺陷
- 檔案路徑與行號：`wsb/bot/slides.py` 第 590、634–639、645、660、667 與 1008–1020 行。
- 那一行在做什麼：
  1. 第 660 行標題與第 667 行表格欄位出現本站禁用詞彙（分別對應風險調整提示與對應金額欄）。
  2. 第 590 行 `Slide("避險成本計算器", "1/3")` 與第 639 行 `"2/3"` 寫死分母為 3，但第 638 行 `if srows:` 為空時會跳過第 2 頁，第 645 行用 `len(out) + 1` 產出 `"2/2"`；同時第 634–635 行 `st_.get("net_cost_exec", st_["net_cost"])` 若鍵存在但值為 `None`，第 635 行 `> 0` 會觸發 `TypeError`。
  3. 第 1008–1020 行 `deck_earnings_board()` 中 `elif sp > 0 and (rx or 0) > 0:` 把 `rx is None`（第 1022 行欄位顯示 `—`）強制變成 `0` 並歸類成 `"超預期・賣消息"`，且 `sp == 0` 會掉入 `"不如預期"` 分支。
- 為什麼有問題：違反禁用詞規定，並會導致缺股價反應時文字與數字矛盾、無進階結構時頁碼錯亂與潛在執行期例外。
- 建議怎麼改：將第 660、667 行改為中性風險試算用語（如「風險貢獻最高部位（對應降低 25% 大盤曝險之規模）」、「對應金額」）；先算 `total = 3 if srows else 2` 再組頁碼並明確檢查 `is not None`；`deck_earnings_board()` 先判斷 `if rx is None:`（標記「待反應／資料缺」）並獨立處理 `sp == 0`（「符合預期」）。
- 確定度：高。

### CODE-3｜tools/site_korea.py：第 53 行趨勢條件順序錯誤，日均年增仍為負（衰退）時可能輸出「成長還在加速」
- 檔案路徑與行號：`tools/site_korea.py` 第 49–55 行。
- 那一行在做什麼：第 53 行以三元運算子決定趨勢文字：`"成長還在加速。" if a > b + 5 else "已經轉為衰退。" if a < 0 else ...`。第 55 行則以 `{"up" if (r.get("yoy") or 0) > 0 else "dn"}` 決定 CSS 漲跌顏色。
- 為什麼有問題：邏輯順序錯誤——`a > b + 5` 排在 `a < 0` 之前。若兩個月前日均年增率為 `-15.0%`、本月為 `-5.0%`，因 `-5 > -15 + 5` 成立，會向使用者輸出「成長還在加速」，實際上出口仍在年減衰退；另第 55 行當 `yoy` 為 `None`（顯示 `—`）或 `0` 時會錯標紅色 `dn`。
- 建議怎麼改：先判斷 `a < 0`（區分衰退收斂或擴大），再判斷正成長的加速／放慢；第 55 行僅在 `r.get("yoy") is not None and r["yoy"] != 0` 時加上 `up`／`dn`。
- 確定度：高。

### CODE-4｜tools/site_drop.py：第 86 行方法說明寫「過去 2 年」，但啟用每日收盤資料時實際僅取 250 個交易日（約 1 年）
- 檔案路徑與行號：`tools/site_drop.py` 第 86 行（對應 `wsb/analytics/drop_check.py` 第 188–189 行）。
- 那一行在做什麼：`site_drop.py:86` 向使用者說明 `「跌深」＝近 4 週（每日資料用 20 個交易日）報酬低於自己過去 2 年同長度報酬標準差的 −1.5 倍`；但 `drop_check.py:189` 在 `daily=True` 時實際呼叫 `deep(now_cl, 20, 250)`。
- 為什麼有問題：文字與計算期間不一致——週資料確為 104 週（2 年），但目前日資料較新時固定走 `daily=True`，標準差樣本其實只有 250 交易日（約 1 年），且 `struct` 市場結構統計仍用週資料日期，兩者基準時點不完全一致。
- 建議怎麼改：將 `drop_check.py:189` 的標準差窗口改為 `504`（約 2 年，與週資料及頁面說明一致），或在 `site_drop.py:86` 明確註明每日資料使用過去 1 年（250 交易日）標準差。
- 確定度：高。

### CODE-5｜wsb/analytics/ai_chain.py：第 72 行全 `NaN` 產業欄會被 `.prod()` 當成 `0%` 稀釋大盤平均，且 `CHAIN` 清單硬編碼於程式內
- 檔案路徑與行號：`wsb/analytics/ai_chain.py` 第 15–23、72 行。
- 那一行在做什麼：第 15–23 行將 9 組 AI 供應鏈公司清單寫死於 `CHAIN`；第 72 行計算各次晶片崩跌期間全產業等權平均報酬 `mkt[e["peak"]] = float(((1 + w).prod() - 1).mean())`。
- 為什麼有問題：第 72 行 `(1 + w).prod()` 預設 `skipna=True`，若某產業在該視窗內全為缺值 `NaN`，`.prod()` 會回傳 `1.0`（即 `0.0` 報酬）並計入 `.mean()`（第 80 行個股迴圈則有 `len(w) >= 2` 過濾）；另 `CHAIN` 屬於公司觀察清單，未像其他模組集中管理於 `settings.yaml`。
- 建議怎麼改：第 72 行改用 `(1 + w).prod(min_count=2) - 1` 避免空欄變成 0% 拉低平均；將 `CHAIN` 移入 `settings.yaml` 管理。
- 確定度：中（1970 年以來多數產業資料完整，實際觸發機率低但屬邏輯邊界瑕疵）。

（備註：本小時批次 `i % 24 == 11` 共 12 檔，其餘 7 檔 `tools/cross_check.py`、`tools/site_slow.py`、`wsb/analytics/patterns.py`、`wsb/analytics/sloos.py`、`wsb/data/exchange_cal.py`、`wsb/data/long_history.py`、`wsb/data/taiwan_quotes.py` 皆已逐行檢查完畢，未發現上述錯誤。）

---

其他今天的大事：
- 台股 11/19 早盤開低後急殺逾千點、連破 4 萬與 39,000 點整數關卡（本站即時行情截至 11:26 報 **38,611 點／-3.9%**），新台幣盤中貶破 33 元觸及 **33.04 元**，創意（3443）連 4 根跌停。（https://www.cna.com.tw/news/afe/202611190035.aspx ；https://money.udn.com/money/story/5616/9888194 ；https://www.cna.com.tw/news/afe/202611190032.aspx ）
- APEC 深圳峰會 11/19 登場，習近平、川普、普丁已在現場同框合影，日相高市早苗並與普丁完成俄烏戰來首次日俄領袖直接會談。（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ；https://www.cna.com.tw/news/aopl/202611190017.aspx ）
- 歐盟理事會與歐洲議會 11/19 達成協議，因中東局勢干擾能源供應，將油氣煤進口商甲烷排放強制申報規定延後兩年至 2029 年；同日歐盟各國正式批准與印尼簽署自貿協定（互免逾 90% 關稅）。（https://www.tradingview.com/news/reuters.com,2026:newsml_SPN46N025:0-eu-countries-parliament-agree-to-delay-eu-methane-regulation-by-two-years/ ；https://www.aljazeera.com/economy/2026/11/19/eu-governments-approve-trade-deal-with-indonesia-to-offset-trump-tariffs ）
- 克里米亞大橋（克赤大橋）11/19 清晨本週第 3 度遭烏軍襲擊暫時中斷交通；美軍中央司令部 11/18 擴大伊朗海上封鎖至公海船對船轉運。（https://www.cna.com.tw/news/afe/202611190045.aspx ；https://gcaptain.com/u-s-targets-ship-to-ship-transfers-in-expanded-iran-maritime-blockade/ ）
- 美國商務部 BIS 遠端算力管制新規（聯邦公報 `2026-23529`）與 CMS CRUSH 反詐欺提案（`2026-23461`）今日（11/19）正式刊登聯邦公報生效／進入意見徵詢。（https://public-inspection.federalregister.gov/2026-23529.pdf ；https://public-inspection.federalregister.gov/2026-23461.pdf ）
- Anthropic（ANT）IPO 定價每股 83 美元、募資 813.1 億美元（估值約 1.5 兆美元，超越 SpaceX 創史上最大紀錄），將於台北時間今晚 22:30 在納斯達克掛牌；同日晚間 20:00–21:00 沃爾瑪、阿里巴巴、拼多多公布財報。（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://www.cna.com.tw/news/afe/202611190043.aspx ；https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ）

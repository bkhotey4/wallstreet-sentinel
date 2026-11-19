台北時間 2026-11-19 12:42

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）、整體 PCE 年增率為 **3.6%**（月增 **0.5%**），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，台北時間 2026-10-29，HTTP 200 確認）。
- 事實：之所以 9 月核心 PCE（3.1%）反過來高於核心 CPI（2.6%），根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 高於核心 CPI 的倒掛現象（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。
- 事實：檢視本站即時網頁《財經日曆》分頁的 `PCE 物價（聯準會最重視的通膨）` 卡片（11/19 12:28 線上版），其實已明確寫出「核心 PCE 月增 前值 `0.3%`、核心 PCE 年增 前值 `3.1%`、PCE 月增 前值 `0.5%`、PCE 年增 前值 `3.6%`」，而總覽的估算卡片亦估 10 月核心 PCE 月增約 `+0.26%`、年增約 `+3.2%`，顯示 9 月基準值已在站內日曆卡片上，只是沒有串接到 `forecast.json`。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照
- 事實：歐洲央行（ECB）2026 年 11 月《金融穩定評估》Box 3（"The debt financing of AI and its implications for financial stability"）明確列出美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 共識（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，台北時間 2026-11-18，HTTP 200 確認）。
- 事實：ECB Box 3 正文對自由現金流的口徑為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（僅以**資本支出超過營運現金流**作為表層口徑，未把尚未起租的表外租賃算進單季現金流）；同時於圖表 A 與註腳 6 依美國會計準則 **ASC 842** 單獨指出，已簽約但資產尚未投入使用的租賃與算力承諾在起租前不計入資產負債表負債，這類表外承諾合計已逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200 確認）。
- 事實：四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與租賃口徑落差如下：
  - Meta（Q3 2026）：營運現金流 **$32.79B**，資本支出（含融資租賃本金償還）**$34.91B**，自報自由現金流為 **-$2.12B（轉負）**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ，HTTP 200）。
  - Alphabet（Q3 2026）：營運現金流 **$42.29B**（$42,290M），現金 PP&E 購置（不含融資租賃）**$51.36B**（$51,355M），自報自由現金流為 **-$9.07B（-$9,065M，轉負，含 52 億美元歐盟罰款支付）**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ，HTTP 200）。
  - Amazon（Q3 2026／TTM）：單季營運現金流 **$42.42B**、單季淨 PP&E 購置 **$75.93B**（隱含單季 **-$33.51B**），公司自報 **TTM 自由現金流 -$42.36B（-$42,357M，轉負）**，該口徑僅扣現金淨 PP&E、未扣額外揭露之新簽融資租賃資產（Q3 單季 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ，HTTP 200）。
  - Microsoft（Q1 FY27）：營運現金流 **$58.02B**，現金 PP&E 資本支出 **$39.37B**，自報自由現金流為 **+$18.6B（仍為正值，年減 27%）**；若計入新起租之融資租賃，總資本支出達 **$45.2B**，扣除後仍餘約 +$12.8B，印證 ECB 精準寫 `"most"` 而非全部（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ，HTTP 200）。

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（附 claude_notes.md 與 forecast.json 實例）
- 推理：檢視 `claude_notes.md` 與 `forecast.json`，最常「下太快」的是以下兩種思考捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：例如 `claude_notes.md` 第 14 行在還沒核對 `bea.gov` 或本站日曆卡片前值的情況下，因為「核心 PCE 通常比核心 CPI 低」，就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推 10 月區間；以及 `forecast.json` 第 65–73 行先前曾用單一 `BAMLH0A0HYM2`（3.43%）得出「信用市場還沒出現壓力」（本輪你已修正）。
  2. **把「我的新聞關鍵字沒對上時間」直接寫成「原因不明／沒有消息」**：例如 `forecast.json` 第 3 行寫「黃金、銅、油價同一天一起跌，主因我沒找到時間對得上的消息」，但同一檔案第 150 行自己就寫了「金銀跌到 14 個月低點，聯準會官員偏鷹讓美元走強」，且忽略 11/18 EIA 原油與汽油大幅累庫及雪佛龍除息日。
  - **（12:42 補充）**：11/19 10:33 緊急加班語音稿再次寫道「開盤前到底是什麼事（能源股跳空），我目前沒有找到」，建議把除息行事曆（如 CVX 11/18 除息）與產經日曆串進新聞原因比對流程。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標
- 推理：若今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，傳導先後順序如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：負債比高、高度仰賴把大模型算力長約拿去抵押融資。隔天（11/20）可驗證指標：`CRWV`、`NBIS` 相對 `QQQ` 的開盤超額跌幅，及新雲端無擔保債二級殖利率走勢。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸**：ANT 募資 813.1 億美元、估值 1.5 兆美元，若破發將壓縮 OpenAI 與晚期 AI 獨角獸 IPO 窗口。隔天可驗證指標：`ARCC`、`BIZD`、`BX`、`APO` 股價與承銷商是否啟動護盤機制（stabilizing bid）之報導。
  3. **最後且幅度較小：出資的晶片商與雲端股東（NVDA、AMD、GOOGL、AMZN）**：主要承受公允價值重估回吐，但只要 RPO 與資料中心交貨未取消，本業現金流不致立即受損。隔天可驗證指標：`NVDA`、`AVGO`、`AMD` 相對 `^SOX` 強弱與 `GOOGL`／`AMZN` 次日盤中選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態（12:42 補充最新外部資訊）
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意**，ECB Box 3 佐證多家一線雲端商 FCF 轉負、表外承諾逾 4 兆美元，但尚未演變為連鎖違約；另美國財政部 11/18 公布 9 月 TIC 外資淨流入仍達 **2,610 億美元**，顯示美元資產外部買盤尚未撤離（https://home.treasury.gov/news/press-releases/sb0693/ ，HTTP 200）。
  2. **主線 2（輝達治理風波 vs 出口調查）— 同意雙方收斂**（45%–50% vs 55%–60%），但補充中央社報導指黃仁勳婚外情疑雲與新加坡企業往來引發國會跨黨派關注並可能赴國會作證，後續仍須緊盯 10-Q Legal Proceedings 章節（https://www.cna.com.tw/news/ait/202611180040.aspx ，HTTP 200）。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，補充今日（11/19）外匯與亞股傳導已提前釋放壓力**：台股今早盤中最低已跌至 **38,259 點**（一度跌逾 1,900 點、上市櫃逾 200 檔跌停），新台幣午盤暫收 **32.988 元**（盤中低見 33.04 元）；同時紐約聯準銀行總裁 John Williams 最新表態反對 12 月一次升息 0.50%，有助壓抑極端 2 碼恐慌（https://www.cna.com.tw/news/afe/202611190076.aspx ；https://www.chosun.com/english/market-money-en/2026/11/19/3ZAB4T3MGVF4HLNUXPSHRHLNCI/ ）。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意**，今日（11/19）伊朗軍方宣布**荷莫茲海峽東側 3 艘油輪觸及水雷起火失能**、且阿聯 ADNOC 船隻遇襲致 11 傷 1 失蹤，確實支持你對封鎖升級尾部風險的重視（https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906 ）；但我仍因 EIA 庫存大增與強美元維持 **55%**。
  5. **主線 5（「風險升級」劇本 33% vs 40%）— 同意方向一致**，差距僅 7 個百分點。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題
- 1. 檢視今天（11/19 12:28）線上版《財經日曆》的 `PCE 物價（聯準會最重視的通膨）` 卡片，其實**已經明確顯示核心 PCE 年增前值 `3.1%`、核心 PCE 月增前值 `0.3%`**；為什麼 `forecast.json` 卻仍寫「9 月核心 PCE 數字：查無」？是預測腳本沒有讀取該表格，還是產出順序有落差？
- 2. 今日（11/19）紐約聯準銀行總裁 John Williams 公開表態不認為 12 月需要一次升息 0.50%，正好與理事 Waller 的 2 碼說法對撞；再加上荷莫茲海峽 3 艘油輪觸水雷與台股盤中破 38,300、逾 200 檔跌停，你下一輪會如何調整「聯準會升息幅度」與「風險升級」的機率？
- 3. 今晚（台北 11/19 21:00–22:30）同時碰上 WMT／BABA／PDD 財報、Anthropic 掛牌與 APEC 深圳美中俄三方互動結果，若明早美股大震盪，你打算怎麼在站上拆解「ANT 掛牌帶動的 AI 資金輪動」與「利率／地緣事件」？

---

### WIDE-1｜荷莫茲海峽 11/19 驚傳 3 艘油輪觸及水雷起火失能，且 ADNOC 船隻遇襲 11 傷 1 失蹤（重大更新）
- 事實：土耳其國營安納杜魯新聞社（AA）與 CBS News 於台北時間 2026 年 11 月 19 日報導，伊朗軍方證實 **3 艘油輪在荷莫茲海峽東側觸及水雷並起火失能（disabled）**，伊朗稱該等船隻關閉導航系統並駛入禁航區；稍早阿聯阿布達比國家石油公司（ADNOC）亦證實一艘旗下船隻在海峽航行時遇襲，造成 **11 名船員受傷、1 人失蹤**，同時美伊在海峽周邊（包含美軍空襲葛希姆島與科威特、巴林攔截飛彈無人機）互襲升溫（https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906 ，台北時間 2026-11-19 10:34，HTTP 200 確認；https://www.cbsnews.com/live-updates/iran-war-us-gulf-retaliation-strikes-strait-of-hormuz/ ，HTTP 200 確認）。
- 推理：美股昨晚（11/18）全數聚焦美國 EIA 原油與汽油累庫，使油價大跌；但今日清晨出現**實質水雷致油輪起火失能**，性質已從「口頭封鎖／攔檢」升級為「航道物理毀損與水雷威脅」，若海運保險業全面停保或延後通航，短線原油與成品油裂解價差極易劇烈反彈並重新點燃二次通膨定價。
- 先影響資產：布蘭特原油／柴油裂解價差、油輪與海運戰爭險費率、航空與石化類股。

### WIDE-2｜歐元區債市殖利率跳升，交易員押注 ECB 到 2027 年底前升息 3 次；ECB 警告法國高債務須靠市場紀律約束（新）
- 事實：路透社（經 Global Banking & Finance 刊載全文）於台北時間 2026 年 11 月 18–19 日報導，受中東戰事推升能源成本與通膨壓力影響，歐元區短期利率市場已完全定價歐洲央行（ECB）自今年 **12 月開始升息**，並押注到 **2027 年底前累計升息 3 次（每次 1 碼）**，帶動德國 2 年期與 10 年期公債殖利率全面上揚；同時 ECB 在 11/18 金融穩定評估報告警告，法國等高赤字成員國須依靠財政改革與「市場紀律」約束，不應期待央行出手救市（https://www.globalbankingandfinance.com/euro-zone-yields-rise-traders-bet-three-ecb-hikes-late-2027/ ，HTTP 200 確認；https://www.globalbankingandfinance.com/markets-help-discipline-france-over-high-debt-ecb/ ，HTTP 200 確認）。
- 推理：美股市場只盯聯準會 12 月升息，忽略**歐元區與日本（植田和男今重申繼續升息）正同步進入緊縮定價**，且 ECB 明確拒絕替法國債務兜底。法德公債利差一旦擴大，會同時推升歐洲銀行融資成本與全球長天期無風險利率地板。
- 先影響資產：德國／法國 10 年期公債利差、EUR/USD、歐洲銀行股（EUFN）與高負債歐企債券。

### WIDE-3｜美國會 USCC 11/19 年報示警「未來 24 個月為台海關鍵期」；加國總理卡尼在深圳稱盼近期簽署加台貿易協議（新）
- 事實：中央社於台北時間 2026 年 11 月 19 日報導，美國「美中經濟暨安全檢討委員會（USCC）」向國會提交的 2026 年度報告台灣章節指出，**未來 24 個月**將形塑長期兩岸關係，若北京透過 11 月底台灣地方選舉與 2028 年大選評估政治脅迫效果不如預期，**對台海採取隔離與封鎖的風險將提高**；同日加拿大總理卡尼（Mark Carney）在中國深圳記者會表示，加台去年已完成的「貿易合作架構協議」取得良好進展，希望於近期正式簽署（https://www.cna.com.tw/news/aipl/202611190024.aspx ，台北時間 2026-11-19，HTTP 200 確認；https://www.cna.com.tw/news/aipl/202611190019.aspx ，台北時間 2026-11-19，HTTP 200 確認）。
- 推理：在美中俄深圳峰會同框營造對話氣氛的同一天，美國國會法定報告仍給出高強度的地緣風險預警，顯示「大國領導人峰會」與「美國國安建制派對台海風險定價」存在明顯落差，將持續構成台灣半導體與外資長線風險溢酬的結構性變數。
- 先影響資產：台股半導體權值股（2330 / TSM）、台灣 ETF（EWT）、新台幣（USD/TWD）、國防軍工類股。

### WIDE-4｜APEC 深圳峰會 11/19 進入最高潮：美中俄三方同框登場，習近平出資 2,000 萬美元挺 APEC、川普反對過度監管 AI（更新）
- 事實：英國衛報即時直播於台北時間 2026 年 11 月 19 日報導，APEC 深圳峰會今日進入重頭戲，習近平、川普與普丁同框出席領袖會議並進行雙邊／三方互動；習近平在全會宣布提供 **2,000 萬美元**資助 APEC 合作並反對單邊主義與保護主義，川普則強調經濟成長並呼籲各國勿對 AI 施加嚴格的全球主義監管；此外日本首相高市早苗亦於 18 日晚間與普丁進行俄烏戰來首次 30 分鐘日俄領袖直接會談（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ，台北時間 2026-11-19，HTTP 200 確認；https://www.cna.com.tw/news/aopl/202611190017.aspx ，台北時間 2026-11-19，HTTP 200 確認）。
- 推理：美股盤前焦點集中在 Anthropic IPO 與零售財報，若下午至今晚深圳美中俄會晤釋出「關稅休兵延長」、「AI 出口管制微調」或「俄烏停火框架」訊號，美股開盤前跨資產定價可能瞬間反轉。
- 先影響資產：USD/CNH、中概股（KWEB）、歐洲天然氣與國防股、全球半導體設備股。

### WIDE-5｜歐盟 11/19 延後進口商「甲烷排放法規」兩年至 2029 年，並正式批准歐盟－印尼自貿協定對沖美國關稅（無新進展）
- 事實：路透社與半島電視台於台北時間 2026 年 11 月 19 日報導，歐盟理事會與歐洲議會同意因應中東能源干擾，將原油、天然氣與煤炭進口商甲烷 MRV 合規義務由 2027 年延後至 **2029 年 1 月 1 日**；同日歐盟理事會正式批准簽署與印尼的自貿協定，互免逾 **90%** 貨品關稅以對沖美國關稅衝擊（https://www.tradingview.com/news/reuters.com,2026:newsml_SPN46N025:0-eu-countries-parliament-agree-to-delay-eu-methane-regulation-by-two-years/ ，HTTP 200 確認；https://www.aljazeera.com/economy/2026/11/19/eu-governments-approve-trade-deal-with-indonesia-to-offset-trump-tariffs ，HTTP 200 確認）。
- 推理：歐洲一邊以延後氣候合規替美／卡達 LNG 進口鬆綁、一邊加速非美雙邊 FTA 繞開美國關稅壁壘，短期降低斷供風險，但長期反映歐洲對中東能源脆弱度的擔憂深於市場表面預期。
- 先影響資產：荷蘭 TTF 天然氣期貨、美國 LNG 出口商（LNG）、印尼盾（IDR）、歐洲工業類股。

---

### A｜今天的大動（對照 `/api/gemini_ask` 12:31 即時清單）

### PANW｜同意本站，Palo Alto Networks（PANW）Q1 FY27 財報全面優於預期、宣布 45 億美元併購，且同日 Everpure（P）財報強勁共振（補充）
- 事實：同意本站。PANW 於美東 11 月 18 日盤後公布 Q1 FY27 財報，營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億美元），GAAP 淨利 **4.82 億美元**（每股 0.57 美元），次世代資安年經常性營收（NGS ARR）年增 **66%** 至 **97.3 億美元**；上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**、調整後 EPS 至 **4.26～4.30 美元**，並宣布以 **45 億美元**全股票收購 **Applied Compute**，盤後漲 **+9.1%**（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19，HTTP 200 確認）。
- 本站漏掉的：本站引用 Yahoo 標題提及的 **Everpure（NYSE: P，原 Pure Storage）** 同於 11/18 盤後公布 Q3 FY27 財報大好——營收年增 **51%** 至約 **14.6 億美元**（新聞稿稱 $1.5B）、調整後 EPS **0.86 美元**（優於預期 0.77 美元）並連三季上調全年指引至 **52.0 億～52.1 億美元**，顯示企業級 AI 資料儲存與資安同步獲得預算驗證；另有 KeyBanc 分析師 Eric Heath 近日將 PANW 評等由 Sector Weight 調升至 **Overweight**（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ，台北時間 2026-11-19，HTTP 200 確認；https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200 確認）。

### CRWD｜CrowdStrike（CRWD）受 PANW 財報驗證 AI 資安需求外溢帶動，疊加近期 Cantor Fitzgerald 調高看法（無新進展）
- 事實：CRWD 於美東 11 月 18 日盤後大漲 **+6.0%**，系同業 PANW 財報驗證企業 AI 資安需求強勁而出現板塊連動；近期 Cantor Fitzgerald 分析師 Jonathan Ruykhaver 維持 **Overweight** 並調高對 CRWD 的看法至 **$275**（原 $250）（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19；https://www.tikr.com/zh/blog/cantor-fitzgerald-raises-its-crowdstrike-target-to-275-is-it-still-too-low ，台北時間 2026-11-17）。
- 推理：CRWD 本身預計 12 月初才公布財報，11/18 盤後未有單獨公司公告（找不到來源），屬同業財報驗證後的資金外溢。

### CVX｜雪佛龍（CVX）受 11/18 除息每股 1.78 美元、EIA 原油與汽油庫存大增壓低油價，以及 50 億美元併購談判影響下跌 4.0%（無新進展）
- 事實：CVX 美東 11 月 18 日正規盤收跌約 **-4.0%**（$205.88，-3.95%），由三件事疊加：（1）11/18 為季股息 **每股 $1.78** 除息日（約佔跌幅 0.8 個百分點）；（2）EIA 公布上週美國原油庫存大增 **340 萬桶**（遠超預期）、汽油大增 **520 萬桶**，壓低 WTI 原油跌至 83.26 美元，能源板塊集體下挫；（3）傳接近以 **50 億美元**收購墨西哥灣深水油商 **Beacon Offshore Energy**（https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ，台北時間 2026-11-18；https://www.nationthailand.com/news/world/40073656 ，台北時間 2026-11-19；https://www.bicmagazine.com/industry/investment-banking/chevron-closes-in-on-5b-beacon-deal/ ，台北時間 2026-11-18）。
- 本站漏掉的：除技術性除息外，當天能源板塊（XLE、XOM、CNQ）同步重挫，屬宏觀庫存與油價事件驅動，而非雪佛龍單一公司利空。

### CNQ｜Canadian Natural Resources（CNQ）正規盤隨油價重挫跌 4.63%（$45.53），盤後 +3.2% 無新公告或報告（找不到來源）
- 事實：CNQ 美東 11 月 18 日正規盤隨北美能源股重挫收跌 **4.63%**（$45.53，多倫多跌 4.06% 至 C$65.52），市場亦在消化其 11/16 宣布以 **25.3 億加元**收購 **Advantage Energy** 之現金支出（https://www.nationthailand.com/news/world/40073656 ，台北時間 2026-11-19；https://www.newsfilecorp.com/release/324091/Canadian-Natural-Resources-Limited-Enters-into-Agreement-to-Acquire-Advantage-Energy-Ltd ，台北時間 2026-11-17）。
- 事實（盤後 +3.2%）：經查公司公告、交易所與主流媒體，美東 11/18 盤後 **沒有任何 CNQ 新聞、財報或分析師調評**（找不到來源）。
- 推理：正規盤急跌近 5% 後盤後低流動性搓合出現 +3.2% 跳動，應屬美加掛牌價差或盤後薄量回補，非基本面突發事件。

---

### AN｜AN-1：最近 3 小時內（台北 09:40–12:40）無新增分析師調評；保留本週已公開可查證報告（無新進展）
- 事實：檢索最近 3 小時（台北 09:40–12:40／美東 11/18 20:40–23:40 深夜時段），AI 供應鏈與美國市值前 20 大公司並無新發布的券商評等調整（找不到來源）。
- 事實：本週已公開可查證之重要評等與信用展望調整包括：（1）**Moody's Ratings（11/18）**維持 **NVDA** Aa1 債信評等，但將展望由 **Positive 調降至 Stable**，點名黃仁勳驟然離職後的接班真空與美國政府調查風險（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ，台北時間 2026-11-19）；（2）**KeyBanc** 分析師 Eric Heath 將 **PANW** 由 Sector Weight 調升至 **Overweight**、看法調高至 **$380**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200）；（3）**YR Research（11/18）**將 **AAPL** 由 **Sell 調升至 Hold**（https://www.tradingview.com/news/seekingalpha:d985f509f094b:0-sa-analyst-upgrades-downgrades-nvda-aapl-smci-tsla/ ，台北時間 2026-11-19，HTTP 200）；另 Summit Insights 調降 NVDA（Buy → Hold）與 Rothschild & Co Redburn 調降 AVGO（Buy → Neutral）原文網頁均設 403 阻擋（單篇直連網址：找不到來源）。

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）正式刊登聯邦公報生效，馬來西亞尋求釐清規範（無新進展）
- 事實：美國商務部工業安全局（BIS）暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢至 2027-01-19）。新規增訂 § 744.24 遠端存取終端用途管制，限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則；馬來西亞政府已表態尋求與美方釐清資料中心服務規範對當地業者之適用邊界（https://public-inspection.federalregister.gov/2026-23529.pdf ，台北時間 2026-11-19，HTTP 200 確認；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ，HTTP 200 確認）。

### POL-2｜美國財政部公布 9 月 TIC 資本淨流入 2,610 億美元（新）、OFAC 制裁伊朗網路與 CMS CRUSH 規則（無新進展）
- 事實：美國財政部於美東 11 月 18 日公布 2026 年 9 月國際資本流動報告（TIC），9 月外資淨流入美國金融市場合計達 **2,610 億美元**（其中私人外資淨流入 **2,670 億美元**、外國官方機構淨流出 **60 億美元**；外資淨買入美國長期證券 **1,867 億美元**、短期國庫券增加 **35 億美元**），顯示強美元與高利率環境下外資仍持續流入美股美債（https://home.treasury.gov/news/press-releases/sb0693/ ，台北時間 2026-11-19，HTTP 200 確認）。
- 事實：同日美國財政部 OFAC 宣布 **「Operation Economic Outcast」** 制裁真主黨與伊朗聖城軍黃金及現金網路（https://home.treasury.gov/news/press-releases/sb0692 ，HTTP 200）；USTR 代表重申美國優先供應鏈韌性（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）；白宮發布亞洲經濟協議事實清單（https://www.whitehouse.gov/fact-sheets/2026/11/fact-sheet-president-donald-j-trump-secures-historic-economic-deals-for-american-workers-and-strengthens-americas-leadership-in-asia/ ）；CMS CRUSH 反詐欺提案（`2026-23461`）今日刊登聯邦公報進入 60 天意見徵詢（https://public-inspection.federalregister.gov/2026-23461.pdf ，HTTP 200）。

---

### TW-1｜台股 11/19 盤中震盪逾 2,000 點、最低下探 38,259 點（逾 200 檔跌停），新台幣午盤暫收 32.988 元（重大更新）
- 事實：台股今日（11/19）早盤一度衝高至 **40,315.53 點**，隨即湧現沉重賣壓翻黑，盤中接連摜破 4 萬、39,000 點與年線，**最低下探 38,259 點（高低震盪逾 2,000 點，上市櫃合計逾 200 檔跌停）**；截至 11:25 加權指數報 **38,566 點（-1,628 點 / -4.05%）**、成交值 **6,024 億元**，櫃買指數重挫逾 **7%**。權值股**台積電（2330）**早盤上衝 2,190 元後翻黑，盤中最低跌至 **2,090 元（-3.9%）**；**聯發科（2454）**、**台達電（2308）**重挫逾 6%（下探 3,660 元、989 元）；**信驊（5274）**跌停至 **8,730 元**、**創意（3443）**連 4 根跌停鎖在 **6,000 元**、**緯穎（6669）**跌逾 5%、散熱廠**雙鴻（3324）**與**奇鋐（3017）**跌停（https://www.cna.com.tw/news/afe/202611190076.aspx ，台北時間 2026-11-19 11:29，HTTP 200 確認；https://money.udn.com/money/story/5607/9888627 ，HTTP 200 確認；https://www.ctee.com.tw/news/20261119700956-430201 ，HTTP 200 確認）。
- 事實：台北匯市新台幣兌美元今日以 **32.96 元**開盤，早盤最高 32.92 元、最低 **33.04 元**，**午盤暫收 32.988 元（貶 4.1 分），成交金額 11.55 億美元**（https://www.cna.com.tw/news/afe/202611190098.aspx ，台北時間 2026-11-19 12:06，HTTP 200 確認）。

### TW-2｜偉詮電今日公告前 3 季 EPS 4.49 元並確定明年初漲價；矽品 11/18 宣布與輝達簽數十億美元多年期封裝協議（更新，補齊單篇原文）
- 事實：中央社 11 月 19 日報導，IC 設計廠**偉詮電（2436）**因晶圓代工廠陸續通知明年調漲代工價，繼茂達之後亦計畫於**明年初調漲產品售價**以轉嫁成本、維持毛利率；偉詮電公布今年前 3 季營收 **34.53 億元（年增 30.64%）**、毛利率 **31.88%**、淨利 **9.04 億元**、每股純益 **4.49 元**，並取得車規／高階伺服器液冷散熱相關 IEC/UL 60730-1 Class B 認證（https://www.cna.com.tw/news/afe/202611190036.aspx ，台北時間 2026-11-19 09:50，HTTP 200 確認）。
- 事實：經濟日報 11 月 18 日報導，**日月光投控（3711）**旗下**矽品**宣布與**輝達（NVIDIA）**達成數十億美元多年期合作協議，將分階段擴充台灣高精度先進封裝產線（含晶圓凸塊、封裝至測試一站式服務），目標於 **2029 年年中前將專供輝達的先進封裝產能擴增至目前的 3 倍**（https://money.udn.com/money/story/5612/9885611 ，台北時間 2026-11-18 09:10，HTTP 200 確認）。
- 事實（無新進展）：**元太科技（8069）**11/18 晚間重訊公告資訊系統疑遭駭客攻擊，初估對營運暫無重大影響（https://www.cna.com.tw/news/afe/202611180336.aspx ，HTTP 200）。
- 傳聞（無新進展）：外媒轉述《工商時報》稱台積電依客戶資產負債表設 AI 信用額度、超額須預付現金，尚未獲公司官方證實（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ，台北時間 2026-11-18）。

### TW-3｜愛德萬 V93000 EXA Scale QX 與台韓出口數據（無新進展）
- 事實：愛德萬（Advantest）11 月發表 36 槽四卡籠架構 **V93000 EXA Scale QX** 測試系統鎖定高功耗 AI 晶片；韓國 11 月前 10 天出口年增 **111.9%**（半導體年增 **331.2%**），台灣 10 月出口年增 **58.9%** 至 **967.6 億美元**（https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ；https://cyprusshippingnews.com/2026/11/13/south-koreas-exports-surge-toward-1-trillion-as-chip-shipments-more-than-quadruple/ ）。

---

### EARN-WMT｜沃爾瑪（WMT）Q3 FY27 財報（今晚美東 11/19 07:00／台北 20:00，無新進展）
- 事實：美東 **2026-11-19 07:00 財報、08:00 電話會議**（台北 **11/19 20:00／21:00**）；TradingView 彙整市場共識營收約 **1,872.5 億～1,873.8 億美元**（年增約 4.3%–5.4%）、調整後 EPS **0.64 美元**（公司上季財測為 EPS 0.62–0.64 美元、常數匯率淨銷售成長 3.0%–3.75%）；選擇權隱含波動 **±5.89%**（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ，HTTP 200；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，HTTP 200）。

### EARN-BABA｜阿里巴巴（BABA）Q2 FY27 財報（今晚美東 11/19 盤前／台北 20:00–21:00，無新進展）
- 事實：美東 **2026-11-19 盤前**（台北 **11/19 20:00–21:00**）；Barchart 彙整預期截至 9/30 季度營收約 **404.1 億～404.8 億美元**（年增約 8.9%–16%）、調整後 EPS 約 **1.56～1.71 美元**（本站日曆列 1.56 美元）（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ，HTTP 200）。

### EARN-PDD｜拼多多（PDD）Q3 2026 財報（今晚美東 11/19 盤前／台北 20:00–21:00，補齊單篇連結）
- 事實：美東 **2026-11-19 盤前**（台北 **11/19 20:00–21:00**，電話會議 07:30 ET）；TradingView 彙整市場共識預期營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS 約人民幣 **18.72～19.02 元**（約 **2.61～2.77 美元**，本站日曆列 2.61 美元）（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ，HTTP 200 確認）。

### EARN-INTU / ROST / GAP / WSM｜今日（11/19）美東盤前與盤後其餘財報（補齊 WSM、ROST 單篇連結）
- 事實：
  - **WSM（盤前／台北 11/19 20:00）**：TradingView 彙整共識營收約 **19.8 億～20.0 億美元**、EPS **2.19 美元**（https://www.tradingview.com/news/tradingview:5796c7c550438:0-wsm-q3-26-earnings-eps-estimate-is-2-19-usd/ ，HTTP 200 確認）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收約 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（公司原財測 2.44–2.48 美元），選擇權隱含波動約 ±8.9%–10.5%（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ，HTTP 200）。
  - **ROST（盤後／台北 11/20 05:00）**：Zacks／TradingView 彙整共識營收約 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ，HTTP 200 確認）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收約 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（公司原財測淨銷售成長 1.5%–2.5%）（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ，HTTP 200）。

### EARN-HPE / ZM / BBY / BURL / DKS / ADI / MDT / DELL / HPQ / ADSK / WDAY / ZS / DE｜11/23–11/25 財報（補齊 BURL、DKS、DE 單篇連結）
- 事實：
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（本站日曆列 1.17，公司財測 1.20–1.30；選擇權波動 ±9.7%，https://247wallst.com/investing/2026/11/09/dell-and-hpe-were-ai-winners-until-the-selloff-can-earnings-put-them-back-on-track/ ）；**ZM** 市場預期 11/23 盤後公布，共識營收 **12.8 億美元**、EPS **1.49 美元**（MarketBeat 彙整頁面，單篇新聞直連網址：找不到來源）。
  - **11/24 盤前（台北 11/24 21:00）**：**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**（https://www.tradingview.com/news/tradingview:6917007d5e261:0-burl-q3-26-earnings-revenue-estimate-is-2-97b-usd/ ，HTTP 200 確認）；**DKS** 共識營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ，HTTP 200 確認）；**ADI** 共識營收 **43.2 億美元**、EPS **3.89–3.92 美元**（本站隱含波動 ±8.04%）；**MDT** 共識營收 **94.6 億～94.8 億美元**、EPS **1.33–1.34 美元**；**BBY** 共識營收 **98.8 億～98.9 億美元**、EPS **1.49 美元**（ADI／MDT／BBY 單篇直連新聞網址：找不到來源）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億美元**（公司財測約 490 億）、調整後 EPS **6.41–6.58 美元**（本站列 6.41，隱含波動 ±14.78%，https://247wallst.com/investing/2026/11/09/dell-and-hpe-were-ai-winners-until-the-selloff-can-earnings-put-them-back-on-track/ ）；**HPQ** 共識營收 **153.0 億～155.8 億美元**、EPS **0.72–0.76 美元**；**ADSK** 共識營收 **21.3 億美元**、EPS **2.91–3.07 美元**；**WDAY** 共識營收 **26.9 億美元**、EPS **2.75 美元**；**ZS** 共識營收 **9.38 億美元**、EPS **1.00 美元**（HPQ／ADSK／WDAY／ZS 單篇直連新聞網址：找不到來源）。
  - **11/25 盤前（台北 11/25 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（本站隱含波動 ±7.31%，https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ，HTTP 200 確認）。

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ，HTTP 200 確認）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（強烈偏升息，無新進展）
- 事實：Waller 於 11/18 受訪指出聯準會可能需要「shock people」壓抑 3% 通膨預期固著，12/8–9 會議應考慮一次升息 50 基點（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ，HTTP 200 確認）。

### FED-3｜聯準會理事 Michael S. Barr（偏升息）與紐約聯準銀行總裁 John Williams（明確反對一次升息 2 碼，補齊單篇報導）
- 事實：聯準會理事 Barr 11/18 在紐約聯準銀行演說指出，通膨仍過高，若經濟按預期演進適合進一步升息（偏升息）（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ，HTTP 200 確認）。
- 事實：紐約聯準銀行總裁 John Williams 在 Axios BFD Summit 舞台對談（朝鮮日報英文版 11/19 報導）明確反對 12 月一次升息 0.50% 的大幅動作，表示 `"I don't see a need for dramatic action right now"`，強調雖然通膨仍高於 2% 需要維持緊縮立場，但就業市場穩健且過去數月政策正在奏效（偏漸進升息、反對 2 碼）（https://www.chosun.com/english/market-money-en/2026/11/19/3ZAB4T3MGVF4HLNUXPSHRHLNCI/ ，台北時間 2026-11-19，HTTP 200 確認）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼約 90%–95%、升息 2 碼約 5%–10%（無新進展）
- 事實：聯邦基金期貨幾乎完全定價 12/9 升息 1 碼（約 90%–95%），升息 2 碼約 5%–10%，美元指數推升至 103.9 區間（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ，HTTP 200 確認）。

---

### CALL-P｜Everpure（NYSE: P，原 Pure Storage）Q3 FY27 法說會：營收年增 51%、連三季上調全年財測（新）
- 事實：Everpure（NYSE: P）於美東 11 月 18 日盤後公布 Q3 FY27 財報並召開電話會議，營收年增 **51%** 至約 **14.6 億美元**（新聞稿約 $1.5B）、GAAP 營業利益 **1.50 億美元**、Non-GAAP 營業利益年增 **76%** 至 **3.45 億美元**、調整後 EPS **0.86 美元**，並連三季上調 FY27 全年營收財測至 **52.0 億～52.1 億美元**、重申強勁的 FY28 初步展望。執行長 Charles Giancarlo 強調 AI 時代企業打破資料孤島需求強勁，財務長 Tarek Robbiati 則指核心與 AI 儲存產品線同步驅動營運創高（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ，台北時間 2026-11-19，HTTP 200 確認）。
- 原話（CFO Tarek Robbiati）：`"Our results reflect the strength of our diversified portfolio, with our core and core AI offerings complemented by increasing contributions from our new businesses. We are raising full-year guidance for the third consecutive quarter and reiterating our strong preliminary FY28 outlook, underscoring confidence in our durable business model and broad-based momentum."`

### CALL-NVDA｜輝達（NVDA）Q3 FY27 法說會：營收 1,158 億美元、下季財測排除中國（無新進展）
- 原話：`"Our momentum is real... Customers, suppliers, and partners are 100% behind us. We’ve got this."`（https://www.cnbc.com/2026/11/18/nvidia-stock-earnings.html ，HTTP 200）。

### CALL-PANW｜Palo Alto Networks（PANW）Q1 FY27 法說會：NGS ARR 年增 66%，45 億美元併購 Applied Compute（無新進展）
- 原話：`"As AI reshapes the threat landscape, we must continually evolve to protect our customers and enable them to adopt AI securely."`（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200）。

### CALL-LOW｜Lowe's（LOW）Q3 2026 法說會：同店 +1.8%，2.5 億美元關稅退稅全數再投資（無新進展）
- 原話：`"We delivered strong top-line growth of over 9%, led by our sixth consecutive quarter of positive comparable sales, with continued momentum in Pro, online and home services."`（https://corporate.lowes.com/sites/lowes-corp/files/2026-11/q3-2026-press-release-v1.pdf ）。

### CALL-TGT｜Target（TGT）Q3 2026 法說會：同店成長 5.6%、全年 EPS 指引上調至 10.65–11.40 美元（無新進展）
- 原話：`"Our third-quarter results reflect continued progress against our strategic priorities, centered on serving busy families with our signature blend of style, design and value."`（https://www.prnewswire.com/news-releases/target-corporation-reports-third-quarter-earnings-302942872.html ）。

### CALL-TJX｜TJX Companies（TJX）Q3 FY27 法說會：同店成長 4%，看好 Q4 Marmaxx 加速（無新進展）
- 原話：`"Consolidated comparable sales grew 4%, driven by continued strength at HomeGoods, TJX Canada, and TJX International, and we saw improved sales at Marmaxx. Importantly, we expect further improvement at Marmaxx in the fourth quarter."`（TJX 官網 PDF 受 403 阻擋，單篇直連網址：找不到來源）。

---

### SENT-1｜NVDA（r/wallstreetbets）— 財報大好卻走弱，社群嘲諷「沒有驚喜就是利空」與黃仁勳迷因（無新進展）
- 討論內容與情緒：11/18 財報達標但股價回跌，r/wallstreetbets 討論串混雜對科技股連月回檔的疲勞感與「nothing burger」嘲諷，並熱議輝達 100 億美元參與 Anthropic 股份與管理層風波（熱度自 11/17–18 升溫；情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xyw3ym/what_are_your_moves_tomorrow_november_18_2026/ ，HTTP 200 確認）。

### SENT-2｜Anthropic（ANT）IPO（r/wallstreetbets）— 懷疑論濃厚，擔心散戶成早期創投「退出流動性」（無新進展）
- 討論內容與情緒：那斯達克確認 ANT 於 11/19 掛牌且定價 83 美元後，WSB 討論串對史上最大 IPO 普遍抱持警覺與諷刺態度，警告小心成為風投與避險基金的退出流動性（熱度自 11/16–18 急升；情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xtuclv/nasdaq_confirms_anthropics_shares_will_begin/ ，HTTP 200 確認）。

### SENT-3｜PANW／科技股財報（r/stocks）— 肯定資安成長動能但對 AI 估值審慎（無新進展）
- 討論內容與情緒：r/stocks 每日討論串肯定 PANW 財報與 NGS ARR 成長，但整體對升息與 AI 高資本支出下的軟體股估值仍偏審慎（熱度自 11/18 升溫；情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ，HTTP 200 確認）。

### SENT-4｜UNH／管理式醫療（r/stocks）— CMS 規則衝擊下偏悲觀觀望（無新進展）
- 討論內容與情緒：UNH 等醫療保險股受 CMS CRUSH 規則影響連日承壓，散戶偏悲觀（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ，HTTP 200 確認）。

### SENT-5｜台股跌破 38,300 點與創意／散熱跌停潮（PTT 股板）— 違約交割與當沖恐慌升高（更新）
- 討論內容與情緒：11/18 上市櫃 9 檔違約交割合計達揭露標準 4.26 億元（創意占 9,453 萬元），加上今日（11/19）盤中最低下探 38,259 點、上市櫃逾 200 檔跌停（創意連 4 根跌停、雙鴻與奇鋐等高價熱門股亮燈跌停），PTT 股板恐慌防禦與「是否見第二隻腳／國安基金護盤」討論大幅升溫（熱度自 11/18 急升；情緒，非事實；https://www.pttweb.cc/bbs/Stock/M.1794981623.A.7D5 ，HTTP 200 確認）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，HTTP 200 確認）。
- 事實：核心 PCE（3.1%）高於核心 CPI（2.6%）之結構主因，係 2026 年住房／房租通膨降溫拉低權重較大的 CPI，而醫療服務、金融與軟體科技服務權重在 PCE 籃子較高且價格較黏著（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。

### TASK-B2｜11/19 台股尚未收盤（截至 12:42 盤中最低下探 38,259 點、新台幣午盤暫收 32.988 元），附上最新盤中與 11/18 官方收盤確認數字
- 事實（時間狀態說明）：目前為 **台北時間 2026-11-19 12:42**，台股集中市場（13:30 收盤）與台北匯市（16:00 收盤）仍在交易時段內，證交所／期交所 11/19 買賣超與台指期未平倉須待 **今日下午 15:00 後**公布，央行官方新台幣收盤價須待 **16:00 後**公布。
- 事實（11/19 盤中與午盤最新）：加權指數早盤衝高至 40,315.53 點後翻黑重挫，盤中高低震盪逾 2,000 點、**最低下探 38,259 點**（上市櫃逾 200 檔跌停），截至 11:25 報 **38,566 點（-1,628 點 / -4.05%）**、成交值 **6,024 億元**（https://www.cna.com.tw/news/afe/202611190076.aspx ，台北時間 2026-11-19 11:29，HTTP 200 確認）；台北外匯市場新台幣以 32.96 元開出、盤中低見 33.04 元後，**午盤暫收 32.988 元（貶 4.1 分），成交 11.55 億美元**（https://www.cna.com.tw/news/afe/202611190098.aspx ，台北時間 2026-11-19 12:06，HTTP 200 確認）。
- 事實（11/18 官方收盤確認）：加權指數收 **40,194.91 點（+102.80 點 / +0.26%）**；外資現貨賣超 **765.64 億元**；期交所三大法人台指期淨部位合計 **-7,322 口**（外資 -99,438 口、投信 +93,573 口、自營商 -1,457 口）；新台幣 11/18 收 **32.947 元**（https://www.cna.com.tw/news/afe/202611180304.aspx ，HTTP 200 確認）。

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；保留掛牌前夕關聯股收盤表現（無新進展）
- 事實：Anthropic（代號 **ANT**）已定價 **每股 83.00 美元**（發行 9.8 億股、IPO 募資 **813.1 億美元**、完全稀釋估值約 **1.5 兆美元**），將於 **美東 2026-11-19 09:30（台北 11/19 22:30）** 正式掛牌；截至台北時間 12:42 美股尚未開盤，首日開盤價、收盤價與成交量將於明早 05:00 收盤後產生（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，HTTP 200；https://www.cna.com.tw/news/afe/202611190043.aspx ，HTTP 200）。
- 事實：掛牌前夕美東 11/18 收盤，**CoreWeave（CRWV）跌 4.13%、IREN 跌 3.61%、Nebius（NBIS）小漲 0.87%、Oracle（ORCL）大致持平**；同日 **NVDA 收跌約 2.9%**，**AVGO、AMD 上漲約 4%–5%**（https://247wallst.com/investing/2026/11/18/coreweave-falls-5-despite-nvidia-sticking-to-its-financing-commitments-nebius-dips-oracle-holds-steady/ ，HTTP 200）。

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字（無新進展）
- 事實：ECB 11/18《金融穩定評估》Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（基於 LSEG 10/26 共識），指多數美國超大規模雲端業者 2026 年自由現金流因 AI 資本支出大於營運現金流而轉負（表層 FCF 口徑未納入未起租的表外租賃；表外承諾逾 4 兆美元係於圖表 A 與註腳 6 依 ASC 842 單獨揭露）（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200）。
- 事實：四巨頭截至 2026-09-30 最新一季自報實際數字如下：Meta（Q3 2026）OCF $32.79B − CapEx（含融資租賃本金）$34.91B = **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）；Alphabet（Q3 2026）OCF $42.29B − 現金 PP&E $51.36B = **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）；Amazon（Q3 2026／TTM）Q3 單季 OCF $42.42B、淨現金 PP&E $75.93B（單季隱含 -$33.51B）、自報 **TTM FCF -$42.36B**（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）；Microsoft（Q1 FY27）OCF $58.02B − 現金 PP&E $39.37B = **+$18.6B（仍為正；計入新起租融資租賃總資本支出 $45.2B 後仍約 +$12.8B）**（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### TASK-B5｜WMT、BABA、PDD 今晚 20:00–21:00 才公布 11/19 財報；附上最新共識（含來源名稱）、上季指引與關稅／消費原話（無新進展）
- 事實：三家均為 **美東 11/19 盤前（台北時間今晚 11/19 20:00–21:00）** 公布，截至台北 12:42 尚未發布實際財報。
- 事實（沃爾瑪 WMT，Q3 FY27）：TradingView 彙整市場共識營收 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（公司上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）；執行長 John Furner 對關稅退稅與消費者壓力的原話為 `"Customers are feeling some pressure, so we're proud of our investments... We'll do everything we can to keep prices as low as we can for customers throughout the rest of the year."`（https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ；https://www.businessinsider.com/walmart-using-tariff-refund-price-cuts-customer-experience-sales-2026-8 ，HTTP 200）。
- 事實（阿里巴巴 BABA，Q2 FY27）：Barchart 彙整共識營收約 **404.1 億～404.8 億美元**（年增約 8.9%–16%）、調整後 EPS **1.56～1.71 美元**，市場聚焦阿里雲 AI 資本支出與中國消費補貼戰（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ，HTTP 200）。
- 事實（拼多多 PDD，Q3 2026）：TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS **2.61～2.77 美元**，市場聚焦跨境關稅與小額免稅新規對 Temu 利潤率的影響（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ，HTTP 200）。

---

### NEXT-1｜事件：11/19 台股盤中急殺破 38,300 點（逾 200 檔跌停）＋BIS 遠端算力管制今日生效引發東南亞釐清（更新）
- 推理：
  - 最先受影響的資產：台灣高融資中小型電子股（櫃買指數 -7%）、USD/TWD（盤中觸 33.04、午盤 32.988）、以及東南亞（馬來西亞、新加坡、印尼、泰國）資料中心租賃與算力合約。
  - 傳導路徑：當美國 BIS `2026-23529` 今日正式刊登聯邦公報生效且馬來西亞緊急釐清資料中心服務規範，跨國算力轉租商須承擔額外客戶審查與 1,200 萬 TPP 稽核成本；同時台股破年線疊加 11/18 9 檔達標違約交割（4.26 億）引發斷頭連鎖，賣壓從高評價 ASIC／散熱／PCB 外溢至權值股與金融股：
    - 美股：**NVDA、ORCL、CRWV、SMCI、EQIX**（東南亞機房合規成本與算力租賃審核拉長）。
    - 台股：**台積電 (2330)、創意 (3443)、信驊 (5274)、雙鴻 (3324)、緯穎 (6669)**（外資提款與高融資／跌停擴散）。
  - 大家還沒注意到的間接受害者：**台灣高融資中小型股背後的「券商融資融券業務與自營避險部位」**——單日逾 200 檔跌停鎖死導致融資追繳賣不掉，可能使下週台灣中小型券商面臨額外信用風險提存與自營避險虧損。

### NEXT-2｜事件：荷莫茲海峽 3 艘油輪觸水雷起火＋歐元區定價 ECB 升息 3 次＋John Williams 反對美國一次升息 2 碼（新）
- 推理：
  - 最先受影響的資產：布蘭特／WTI 原油期貨、柴油裂解價差、歐洲公債（德／法利差）與美債 2 年／10 年殖利率。
  - 傳導路徑：John Williams 出面駁斥 12 月升息 2 碼，短線替美股成長股壓低「暴力升息」尾部風險；但同一時間荷莫茲水雷實質毀損油輪、且歐元區已被市場押注到 2027 年底升息 3 次，代表全球「能源運輸摩擦通膨」與「非美央行接棒緊縮」會把全球長債殖利率與海運費率墊在高檔，限制美債回落空間：
    - 美股：**FRO（Frontline）、STNG（Scorpio Tankers）、LNG（Cheniere）、DAL、UAL**。
    - 台股：**陽明 (2609)、長榮 (2603)、長榮航 (2618)、華航 (2610)、台塑化 (6505)**。
  - 大家還沒注意到的間接受害者：**南非與印度等高度依賴波斯灣進口原油與荷莫茲航道的能源淨進口新興市場央行**——今天（11/19）南非央行（SARB）正是在油價推升燃料通膨至 5.2% 下召開關鍵利率決策（https://www.sabcnews.com/sabcnews/analysts-expect-mpc-to-keep-interest-rates-unchanged/ ，HTTP 200），油運中斷將迫使更多新興市場央行延後降息甚至被迫升息。

### NEXT-3｜事件：ECB 證實多數雲端巨頭 FCF 轉負＋4 兆表外承諾 vs 美國 9 月 TIC 外資淨流入 2,610 億美元（更新）
- 推理：
  - 最先受影響的資產：投資級科技長債利差（10–30 年期）、Oracle 5 年期 CDS、與美國長天期公債標售（包含今晚 $19B 10 年期 TIPS 增額標售）。
  - 傳導路徑：雖然 9 月 TIC 顯示外資單月仍淨流入 2,610 億美元（https://home.treasury.gov/news/press-releases/sb0693/ ），美債整體買盤未枯竭；但資金在內部正從「自由現金流轉負、表外承諾龐大」的高資本支出雲端公司債，轉向高安全性的公債與具即時現金回流能力的企業儲存／資安軟體商（如昨晚 PANW、Everpure）：
    - 美股：**ORCL、AMZN、GOOGL、META、CRWV**（資本支出債市溢酬壓力）vs **PANW、CRWD、P（Everpure）**（現金流／ARR 驗證受青睞）。
    - 台股：**日月光投控 (3711，旗下矽品獲輝達長約保障)、台達電 (2308)、廣達 (2382)、鴻海 (2317)、金像電 (2368)**。
  - 大家還沒注意到的間接受害者：**歐元區與美國傳統非科技投資級債發行人（公用事業、電信、製造業）**——雲端巨頭同時湧入美元與歐元發債，擠壓傳統企業債胃納並推高再融資票息。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 已由 60% 降至 45%）」
- 最強反方證據：BEA 官方新聞稿已證實 9 月核心 PCE 年增確為 **3.1%**（`https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026`），The Conference Board 預估 10 月將升至 **3.3%**（`https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026`），且本站總覽卡片亦估 10 月核心 PCE 年增 **3.2%**。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法發布年增率，這題將成為「無法判定」；但只要有公布年增率，低於 3.0% 的空間極小。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：我維持落在 2.4%–3.0% 僅約 **30%**（比你修正後的 45% 低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露多數一線雲端商 FCF 轉負且表外承諾逾 4 兆美元，今日（11/19）荷莫茲海峽再爆 3 艘油輪觸水雷起火（`https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906`），且台股盤中崩跌至 **38,259 點**、逾 200 檔跌停（`https://www.cna.com.tw/news/afe/202611190076.aspx`）。
- 另一種同樣說得通的解釋：就算 Williams 壓低 12 月升息 2 碼機率、美國垃圾債指數因能源權重撐盤未破 4%，「投資級科技債利差走寬＋中東油輪水雷＋亞股千點斷頭」就足以構成實質的「風險升級」。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：我維持「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你的 80% 低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：11/18 美國 EIA 原油庫存暴增 340 萬桶、汽油暴增 520 萬桶後，WTI 跌至 83 美元附近、貼近 80 美元下緣，強美元亦壓抑商品；但今天（11/19）荷莫茲海峽 3 艘油輪觸水雷起火，讓油價上下雙尾風險同時放大（`https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906`）。
- 另一種同樣說得通的解釋：高庫存與高利率拉低基準需求（容易跌破 80 美元），而實質水雷與封鎖升級則可能瞬間衝破 100 美元——也就是油價**在 80–100 美元區間外的機率（雙尾）高於區間內**，並非單純看跌。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **未來 72 小時荷莫茲海峽通航／掃雷動態**。
- 機率估計：我維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」
- 最強反方證據：財報與法說會未見執法處分揭露，且中央社報導黃仁勳婚外情與新加坡企業關聯已引發美國國會要求其公開作證（`https://www.cna.com.tw/news/ait/202611180040.aspx`），Moody's 報告亦指出接班計畫空白與未定調查風險並存（`https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591`）；但川普在 APEC 僅簡短提及黃仁勳，不似美中最高層級國家安全重大違規案的處置規格。
- 另一種同樣說得通的解釋：個人治理／行為失當先觸發董事會立即切割，隨後才引發美國國會與監管機構對過往對中／新加坡銷售的連帶審查。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節，11 月下旬～12 月初）**與 **國會公開聽證會證詞**。
- 機率估計：我估「直接因中國出口調查」**40%–45%**，「個人治理觸發＋連帶國會／監管審查」**55%–60%**（與你目前 45%–50% 接近）。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（無新進展）
- 事實：ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**（已超過帳上負債），且投資級科技長債利差已相對於同評級企業債走寬（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q `Commitments and Contingencies / Uncommenced Leases` 追蹤，及 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜缺少「非公開交易 BDC 限額贖回（Gating）、避險基金槓桿與主權債財政－金融連動」監測（更新，補充 BIS/IMF 觀點）
- 事實：聯準會 FEDS Notes（2026-10-14）指半流動性非公開 BDC 持有 93.4% 私募信貸並觸發贖回上限；同時 IMF 與 BIS 最新穩定評估皆點名「主權債財政－金融連動（Fiscal-financial nexus）」與穩定幣需求對短天期美債與銀行存款的替代效應。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜缺少「高集中度雲端／金融基建中斷與 SEC Item 1.05 資安事件」警報（無新進展）
- 推理：監測 SEC 8-K Item 1.05 是否涉及高集中度第三方基建（AWS、Azure、GCP、Cloudflare、DTCC），可比股價更早捕捉系統性中斷。免費資料源：CISA KEV JSON（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）＋ SEC EDGAR。

### BLIND-4｜「台股籌碼風向計」尚未合計三大法人台指期淨口數，亦未統計證交所單日違約交割金額（對照 12:12 線上版確認）
- 事實：檢視 11/19 12:12 線上「台股籌碼風向計與斷頭警戒」，目前仍僅對 `外資台指期未平倉 -99,438 口` 亮紅燈，未將同列文字中的投信 `+93,573`、自營 `-1,457` 直接加總為 **「三大法人合計淨空單 -7,322 口」**，亦未統計證交所／櫃買每日達揭露標準之違約交割金額（11/18 爆 9 檔合計 4.26 億元）。免費資料源：期交所「三大法人區分各期貨契約交易資訊」與證交所「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」（無新進展）
- 推理：建議在「IPO 觀察」補上大型 IPO 納入 S&P 500、Nasdaq-100 指數時程與被動 ETF 權重排擠效應說明。

---

### SITE-1｜`forecast.json` 寫「9 月核心 PCE 數字：查無」，但本站《財經日曆》PCE 卡片其實已顯示「前值 3.1%」（12:28 線上版確認仍存在）
- 本站寫了什麼：`research_feed/forecast.json`（更新於 `2026-11-19 07:03 台北`）第 130 行寫著 `9 月核心 PCE 數字：查無。`；`claude_notes.md` 第 14 行亦表示無法查證 9 月核心 PCE 為 3.1%。
- 正確應該是什麼：本站線上《財經日曆》分頁之 `PCE 物價（聯準會最重視的通膨）` 卡片（11/19 12:28 更新）已明確顯示 **`核心 PCE 月增 前值 0.3%`、`核心 PCE 年增 前值 3.1%`、`PCE 月增 前值 0.5%`、`PCE 年增 前值 3.6%`**，完全符合 BEA 官網新聞稿（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）。請將日曆卡片的前值資料管線串接至預測腳本。

### SITE-2｜11/19 `10:33 緊急加班` 語音稿截至 12:30 仍誤把「今天（11/19）台股盤中跌幅」講成「台股昨天收盤附近少了 3.4%」（確認仍存在）
- 本站寫了什麼：線上總覽最上方 `🚨 緊急加班（最後更新 11-19 10:33）` 語音文字稿寫道：`「台股昨天收盤附近比前一天少了三點四個百分點」`（並於總經儀表更新至 11-19 台股加權 `39,172 -2.5%` 後仍保留該舊語音稿）。
- 正確應該是什麼：台股「昨天（11/18）」收盤其實是**小漲 +102.80 點（+0.26%）收在 40,194.91 點**（https://www.cna.com.tw/news/afe/202611190027.aspx ）；該段 `-3.4%`（盤中最新曾擴至下探 38,259 點、-4.8%）其實是**今天（11/19）上午的盤中即時跌幅**，係美股（資料日 11-18）與台股（資料日 11-19）混用所致。

### SITE-3｜`api/gemini_ask`（12:31 即時版）仍僅標示 `CNQ +3.2%（盤後）`，未附正規盤收跌 -4.63%（已列入待辦，確認仍存在）
- 本站寫了什麼：`https://wallstreet-sentinel.pages.dev/api/gemini_ask`（台北 12:31）仍寫 `### CNQ｜CNQ（Canadian Natural Resources）今天 +3.2%（盤後）`，未呈現正規盤重挫 -4.63% 的完整脈絡（https://www.nationthailand.com/news/world/40073656 ）。

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆，對照 12:13／12:17 線上版核對
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳峰會；美東盤前（台北 20:00–21:00）**WMT、BABA、PDD、WSM** 財報；台北約 21:00（南非 15:00）**南非央行（SARB）利率決策**（https://www.sabcnews.com/sabcnews/analysts-expect-mpc-to-keep-interest-rates-unchanged/ ）；美東 09:30（台北 22:30）**Anthropic (ANT)、MapLight (MPLT)** 掛牌；美東 13:00（台北 11/20 02:00）**美債 10 年期 TIPS 增額標售 $19B**（另含 4W $115B、8W $110B 短券）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP** 財報（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  2. **11/20（五）**：**台灣經濟部 10 月外銷訂單**（台北 16:00，預估 1,125–1,159 億美元，https://money.udn.com/money/story/10869/9879179 ）；**美股月選擇權到期（OPEX）**；**密大消費者信心指數終值**（美東 10:00／台北 23:00）；**SanDisk (SNDK) 1 拆 8 分割**。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM** 財報。
  5. **11/24（二）**：美東盤前（台北 21:00）**ADI、MDT、BBY、BURL、DKS**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY、ZS**。
  6. **11/25（三）**：美東盤前（台北 21:00）**DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與 10 月耐久財訂單；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**；台北 11/26 **宏于電機（台股）掛牌**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/28（六）**：**台灣 2026 九合一地方選舉投票日**。
  10. **11/29（日）**：**OPEC+ 聯合部長級監督委員會（JMMC）會議**。
  11. **11/30（一）**：**MSCI 季度調整台股收盤生效（台北 13:30）與月底資產再平衡**。
  12. **12/01（二）**：美東 10:00（台北 23:00）**ISM 製造業 PMI 與 10 月 JOLTS 職位空缺**；**CRWD、NTAP** 財報；**韓國 11 月出口初值**。
  13. **12/03（四）**：美國參議院資料中心聽證。
- 對照本站 11/19 12:13／12:17 線上版核對：
  - **正確部分**：`未來 14 天事件`（12:13）與 `upcoming.json`（12:17）已正確列出 WMT/BABA/PDD、ANT/MPLT、HPE、ADI、MDT、DELL、HPQ、DE、11/19 美債 10Y 增額 $19B（註：建議標明為 **10 年期 TIPS** 而非一般名目 10 年債）、H.4.1、11/20 OPEX、11/25 GDP 與 PCE、11/30 月底再平衡、12/01 JOLTS；`休市與提早收盤` 亦正確列出 11/26 休市與 11/27 半天交易。
  - **漏掉部分**：`upcoming.json`（12:17）與 `財報前隱含波動` 仍漏掉今晚盤後的 **INTU、ROST、GAP**（市值皆逾百億美元）、11/23 **ZM**、11/24 **BBY、BURL、DKS、ADSK、WDAY、ZS**；`未來 14 天事件`（12:13）仍漏掉 **11/19 南非央行、11/20 台灣 10 月外銷訂單、11/21 韓國 20 日出口、11/25 聯準會褐皮書（僅列在《美國經濟日曆》內未上總覽清單）、11/26 韓國央行、11/28 台灣九合一選舉、11/29 OPEC+ JMMC 會議**，且未在該清單內併註 **11/26–27 感恩節休市與半天交易**。

---

### CODE-1｜tools/site_stability.py：第 133–140 行總結標題只計入前 4 項燈號，忽略同卡內的 LDI、FSR、SLOOS 與傳導管道紅黃燈
- 檔案路徑與行號：`tools/site_stability.py` 第 133–140、153 行（對應 `tools/site_layout.py` 第 66 行）。
- 那一行在做什麼：`sec_st_brief()` 在第 91–132 行將財政部發債（`rf`）、短期資金（`fu`）、基差交易（`ba`）、AI 資本支出（`ai`），以及**退休金與長債（`st-ldi`）、官方壓力點（`st-fsr`）、銀行放款門檻（`st-sloos`）、傳導管道（`STR.tiles`）**都放入同一張摘要卡片；但第 133–140 行計算 `reds`、`yel`、`head` 與 `worst` 時，只遍歷 `(rf, fu, ba, ai)` 4 項，並寫死 `"金融穩定 4 項：全部正常"`（或 `len(have)/4 項有資料`）。
- 為什麼有問題：即使同一張卡片裡的 `st-sloos`（銀行放款門檻）、`st-ldi`（退休金與長債）、`st-fsr` 或外國央行美債託管（`custody`）已經亮紅燈或黃燈，卡片標題與 `site_layout.py:66` 總覽大表仍會對使用者顯示「金融穩定 4 項：全部正常」，導致文字結論與下方圖卡矛盾。
- 建議怎麼改：將所有已呈現且具狀態燈號的模組（或改寫標題明確限定「核心 4 項全部正常」，其餘項目若有紅黃燈另外提示），同步讓 `worst` 涵蓋 `st-ldi`、`st-fsr`、`st-sloos` 與 `STR` 的異常項目。
- 確定度：高。

### CODE-2｜wsb/analytics/etf_flows.py：第 100–121 行把「過期（stale）或零淨流向」誤說成「債券 ETF 的資料還在累積」
- 檔案路徑與行號：`wsb/analytics/etf_flows.py` 第 72、100–121 行。
- 那一行在做什麼：第 100 行先以 `if not v["stale"]` 過濾掉超過 4 個營業日未更新的 ETF；第 103 行呼叫 `_credit(s5.get("HYG"), s5.get("TLT"), s5.get("LQD"))`；第 120 行若 `not bond` 就輸出 `"債券 ETF 的資料還在累積。"`。另第 72 行在計算 `need` 時僅用 `max(n + 1 - len(rows), 1)`。
- 為什麼有問題：當 `HYG` 或 `TLT` 已有足夠歷史天數但因發行商網站阻擋（如 `daily_audit.py:260` 註記 Invesco 406 拒接）超過 4 天變成 `stale`、或 5 日淨流向恰為 0（`_credit` 第 92 行回傳 `""`）時，程式會向使用者說「債券 ETF 的資料還在累積」，與實際原因（資料暫時過期／取得失敗或無資金移動）不符；同樣地，若 `_window` 因中間缺天回傳 `None` 而 `len(rows)` 已很大，第 72 行 `need` 會得出 `1`。
- 建議怎麼改：區分 `HYG`/`TLT` 是「天數不足」還是「`stale` 過期（請註明暫停更新）」，並於 `_credit` 處理 `hy == 0 or tl == 0` 的情境（「近 5 日無明顯淨申贖」）。
- 確定度：中。

### CODE-3｜tools/daily_audit.py：第 77–78 行解析卡片檢查時間未考慮跨年，每年 1 月會漏報去年 12 月停更的資料源
- 檔案路徑與行號：`tools/daily_audit.py` 第 77–81 行。
- 那一行在做什麼：從網站 HTML 的 `<p class="upd old" title="...">` 擷取 `MM-DD HH:MM` 格式的檢查時間後，第 77–78 行以 `yr = datetime.fromtimestamp(now).year` 拼出 `f"{yr}-{t['checked']}"` 來計算 `fetch_age_h = round((now - chk) / 3600, 1)`。
- 為什麼有問題：在每年 1 月初，若某個資料源從前一年 12 月下旬起停止抓取（例如 `12-28 10:00`），套用新年年分會變成「今年 12 月 28 日（未來時間）」，`fetch_age_h` 變成負數（約 `-8,600` 小時），進而無法觸發 `x["why"] = "fetch"`，讓資料抓取故障被歸類錯誤或漏報。
- 建議怎麼改：若解析出來的 `chk > now + 86400`（落在未來），改用 `yr - 1` 重新解析 `chk`。
- 確定度：中。

### CODE-4｜wsb/data/extended.py：第 18、35 行未檢查美股國定假日與 K 線日期，國定假日盤後時段可能把前一交易日盤後價當成今天
- 檔案路徑與行號：`wsb/data/extended.py` 第 15–21、32–38 行。
- 那一行在做什麼：`us_ext_session()` 第 18 行僅以 `loc.weekday() >= 5` 排除週末；`parse()` 第 35 行對 Yahoo `range=1d` 回傳的最後一根非空 5 分鐘線，只要時間戳 `t >= reg["end"]` 就回傳 `"post"`、`t < reg["start"]` 就回傳 `"pre"`，並以 `regularMarketPrice` 計算漲跌幅。
- 為什麼有問題：在美股平日國定假日（例如即將到來的 11/26 感恩節），Yahoo `range=1d` 不會回傳空陣列，而是回傳**前一個交易日（11/25）的完整交易日 K 線與正規收盤元資料**。因此在 11/26 美東 16:00–20:00，若呼叫端依據 `us_ext_session() == "post"` 進行盤後跳空檢查，`parse()` 會把前一晚的盤後價格再次回傳並標為 `"post"`，可能重複觸發或誤報假日盤後行情。
- 建議怎麼改：在 `parse()` 中檢查最後一根 K 線的 `datetime.fromtimestamp(t, NY).date()` 是否等於 `datetime.now(NY).date()`（若非今天則回傳 `None`）。
- 確定度：中。

### CODE-5｜wsb/data/market.py：第 417–432 行當即時報價跨入新年而歷史 K 線尚未更新時，YTD 會誤用「前年底」為基期
- 檔案路徑與行號：`wsb/data/market.py` 第 417–433 行（`returns_table`）。
- 那一行在做什麼：第 417 行取 `last_d = s.index[-1]`（歷史資料最後日期），第 422 行當即時報價 `q["asof"]` 比 `last_d` 新時，將 `lastv` 乘上今日漲跌幅推算到最新價格；接著第 426 行以 `prev_y = s[s.index.year < last_d.year]` 計算 YTD 基期。
- 為什麼有問題：在每年 1 月第 1 個交易日，若即時報價 `q["asof"]` 已是新年（例如 `2027-01-04`），但歷史日線 `self.history` 尚未重建或最後一筆仍停在 `2026-12-31`（`last_d.year == 2026`），第 422 行已將 `lastv` 更新為新年的收盤／現價，第 426 行卻拿 `< 2026`（即 `2025-12-31`）當基期，導致跨年首日 YTD 變成「去年全年 + 今天」的累計報酬（同理 `w1`/`m1`/`m3` 基準日也少算了 `q["asof"]` 與 `last_d` 的天數差）。
- 建議怎麼改：計算 `ref_d = pd.Timestamp(q["asof"])`（當 `q["asof"] > last_d` 時），在 `s.index.year < ref_d.year` 與 `ref_d - Timedelta(days=days)` 使用 `ref_d`。
- 確定度：中。

（備註：本小時批次 `i % 24 == 12` 共 12 檔，其餘 7 檔 `tools/site_dual.py`、`tools/site_layout.py`、`wsb/analytics/ai_verdict.py`、`wsb/analytics/personal.py`、`wsb/analytics/stock_check.py`、`wsb/config.py`、`wsb/data/transmission.py` 皆已逐行檢查完畢，未發現上述錯誤。）

---

其他今天的大事：
- 荷莫茲海峽 11/19 驚傳 **3 艘油輪觸及水雷起火失能**，稍早阿聯 ADNOC 船隻亦遇襲致 11 傷 1 失蹤，美伊波斯灣交火升級（https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906 ；https://www.cbsnews.com/live-updates/iran-war-us-gulf-retaliation-strikes-strait-of-hormuz/ ）。
- 台股 11/19 盤中震盪逾 2,000 點、最低下探 **38,259 點**（上市櫃逾 200 檔跌停），台積電盤中低見 2,090 元（-3.9%），創意連 4 根跌停；新台幣午盤暫收 **32.988 元**（盤中低見 33.04 元）（https://www.cna.com.tw/news/afe/202611190076.aspx ；https://www.cna.com.tw/news/afe/202611190098.aspx ）。
- APEC 深圳峰會 11/19 進入高潮，習近平、川普、普丁同框登場；習近平宣布出資 2,000 萬美元挺 APEC、川普呼籲勿對 AI 過度全球監管；加國總理卡尼稱盼近期簽署加台貿易合作協議，而美國會 USCC 年報同日示警未來 24 個月台海封鎖風險提高（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ；https://www.cna.com.tw/news/aipl/202611190024.aspx ；https://www.cna.com.tw/news/aipl/202611190019.aspx ）。
- 紐約聯準銀行總裁 John Williams 表態反對 12 月一次升息 2 碼（`0.50%`）；歐元區交易員已定價 ECB 到 2027 年底前升息 3 次，ECB 同時警告法國高債務須靠市場紀律約束（https://www.chosun.com/english/market-money-en/2026/11/19/3ZAB4T3MGVF4HLNUXPSHRHLNCI/ ；https://www.globalbankingandfinance.com/euro-zone-yields-rise-traders-bet-three-ecb-hikes-late-2027/ ）。
- 美國商務部 BIS 遠端算力管制新規（`2026-23529`）今日生效，財政部 9 月 TIC 外資淨流入 **2,610 億美元**；IC 設計廠偉詮電（2436）宣布明年初產品漲價轉嫁晶圓代工成本（https://public-inspection.federalregister.gov/2026-23529.pdf ；https://home.treasury.gov/news/press-releases/sb0693/ ；https://www.cna.com.tw/news/afe/202611190036.aspx ）。
- Everpure（NYSE: P，原 Pure Storage）Q3 FY27 營收年增 51%、連三季上調全年財測；今晚（11/19）20:00–22:30 沃爾瑪、阿里巴巴、拼多多公布財報，且 Anthropic（ANT，定價 83 美元、估值 1.5 兆美元）正式在納斯達克掛牌（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ；https://www.anthropic.com/news/anthropic-prices-initial-public-offering ）。

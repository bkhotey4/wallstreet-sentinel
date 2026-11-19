台北時間 2026-11-19 14:45

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）、整體 PCE 年增率為 **3.6%**（月增 **0.5%**），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，台北時間 2026-10-29，HTTP 200 確認）。
- 事實：之所以 9 月核心 PCE（3.1%）反過來高於核心 CPI（2.6%），根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 高於核心 CPI 的倒掛現象（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。
- 事實：檢視本站即時網頁《財經日曆》分頁的 `PCE 物價（聯準會最重視的通膨）` 卡片（11/19 14:22 線上版確認仍在），其實已明確寫出「核心 PCE 年增 3.1%」、「前值 0.3%」，顯示 9 月基準值已在站內日曆卡片上，只是沒有串接到 `forecast.json`。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照（無新進展）
- 事實：歐洲央行（ECB）2026 年 11 月《金融穩定評估》Box 3（"The debt financing of AI and its implications for financial stability"）明確列出美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 共識（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，台北時間 2026-11-18，HTTP 200 確認）。
- 事實：ECB Box 3 正文對自由現金流的口徑為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（僅以**資本支出超過營運現金流**作為表層口徑，未把尚未起租的表外租賃算進單季現金流）；同時於圖表 A 與註腳 6 依美國會計準則 **ASC 842** 單獨指出，已簽約但資產尚未投入使用的租賃與算力承諾在起租前不計入資產負債表負債，這類表外承諾合計已逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200 確認）。
- 事實：四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與租賃口徑落差如下：
  - Meta（Q3 2026）：營運現金流 **$32.79B**，資本支出（含融資租賃本金償還）**$34.91B**，自報自由現金流為 **-$2.12B（轉負）**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）。
  - Alphabet（Q3 2026）：營運現金流 **$42.29B**（$42,290M），現金 PP&E 購置（不含融資租賃）**$51.36B**（$51,355M），自報自由現金流為 **-$9.07B（-$9,065M，轉負，含 52 億美元歐盟罰款支付）**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）。
  - Amazon（Q3 2026／TTM）：單季營運現金流 **$42.42B**、單季淨 PP&E 購置 **$75.93B**（隱含單季 **-$33.51B**），公司自報 **TTM 自由現金流 -$42.36B（-$42,357M，轉負）**，該口徑僅扣現金淨 PP&E、未扣額外揭露之新簽融資租賃資產（Q3 單季 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）。
  - Microsoft（Q1 FY27）：營運現金流 **$58.02B**，現金 PP&E 資本支出 **$39.37B**，自報自由現金流為 **+$18.6B（仍為正值，年減 27%）**；若計入新起租之融資租賃，總資本支出達 **$45.2B**，扣除後仍餘約 +$12.8B，印證 ECB 精準寫 `"most"` 而非全部（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（無新進展，附 macro_voice.json 新實例）
- 推理：檢視 `claude_notes.md`、`forecast.json` 與本輪更新的 `macro_voice.json`，最常「下太快」的是以下兩種思考捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：例如 `claude_notes.md` 第 14 行在還沒核對 `bea.gov` 或本站日曆卡片前值的情況下，因為「核心 PCE 通常比核心 CPI 低」，就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推 10 月區間；以及 `forecast.json` 第 65–73 行先前曾用單一 `BAMLH0A0HYM2`（3.43%）得出「信用市場還沒出現壓力」（本輪你已修正）。
  2. **把「我的新聞關鍵字沒對上時間」或「昨天數字」直接當作定論**：例如 `forecast.json` 第 3 行寫「黃金、銅、油價同一天一起跌，主因我沒找到時間對得上的消息」，但同一檔案第 150 行自己就寫了「金銀跌到 14 個月低點，聯準會官員偏鷹讓美元走強」，且忽略 11/18 EIA 原油與汽油大幅累庫及雪佛龍除息日；11/19 14:15 剛更新的 `macro_voice.json` 第 6 行又寫「新台幣只貶了一點點，三十二點九四」，其實 32.947 是昨天（11/18）的匯率，今天（11/19）盤中早已貶破 33 元關卡至 33.04 元、午盤收 32.988 元。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標（補充自建資料中心與台鏈影響）
- 事實（新補充）：中央社 11/19 引述 Anthropic 公開說明書指出，Anthropic 至 2045 年算力合約承諾高達 **9,009 億美元**（2030 年底前到期約 4,520 億美元），其中涵蓋博通 1,612 億美元、Alphabet 1,213 億美元、SpaceX 1,205 億美元、AWS 1,100 億美元與 Azure 449 億美元；雖然前 9 月營收約 330 億美元、自由現金流 56 億美元、10 月底 ARR 達 810 億美元，但正從租用外部雲端轉向透過博通租賃 3.5 GW Google TPU 機櫃自建「Anthropic Direct」資料中心，短期自由現金流恐縮水甚至歸零（https://www.cna.com.tw/news/afe/202611190156.aspx ，台北時間 2026-11-19，HTTP 200 確認）。
- 推理：若今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，傳導先後順序如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：負債比高、高度仰賴大模型算力長約抵押融資，且 Anthropic 轉向自建直接稀釋第三方租賃溢價。隔天（11/20）可驗證指標：`CRWV`、`NBIS` 相對 `QQQ` 的開盤超額跌幅，及新雲端無擔保債二級殖利率走勢。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸**：ANT 募資 813.1 億美元、估值 1.5 兆美元，若破發將壓縮 OpenAI 與晚期 AI 獨角獸 IPO 窗口。隔天可驗證指標：`ARCC`、`BIZD`、`BX`、`APO` 股價與承銷商是否啟動護盤機制（stabilizing bid）之報導。
  3. **最後且分化：晶片與機櫃合作夥伴（NVDA、AVGO、GOOGL、AMZN、台積電等同步私募出資方）**：主要承受公允價值重估回吐（如台積電核准上限 5 億美元參與同步私募），但 Anthropic 轉向自建反而讓博通與 TPU 機櫃組裝廠（英業達、廣達、鴻海）受關注。隔天可驗證指標：`AVGO`／`NVDA` 相對 `^SOX` 強弱與次日選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態（14:45 重大更新：川習會「30 對 30」共識、黃仁勳案與晶片走私調查、台股收盤 8,952 億破年線）
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意**，ECB Box 3 佐證多家一線雲端商 FCF 轉負、表外承諾逾 4 兆美元，Anthropic 自建資料中心使 9,009 億美元算力合約現金流壓力浮上檯面（https://www.cna.com.tw/news/afe/202611190156.aspx ），但尚未演變為連鎖違約；美國 9 月 TIC 外資淨流入仍達 2,610 億美元（https://home.treasury.gov/news/press-releases/sb0693/ ）。
  2. **主線 2（輝達治理風波 vs 出口調查）— 部分同意，但有重大新證據顯示「兩件事已經連在一起」**：雖然輝達董事長瓊斯重申不讓黃仁勳回鍋、財報未列執法處分、台積電張曉強公開力挺，但中央社今日（11/19）最新引述川普接受《福斯新聞》專訪指出：**與黃仁勳有染的一名女子正受到美國政府調查，調查涉及她是否可能為中國情報機構工作，以及是否可能協助走私晶片**，同時川普稱「再等 2 至 3 年」或允許輝達 Blackwell 晶片賣中國（https://www.cna.com.tw/news/aopl/202611193003.aspx ，HTTP 200 確認）。這說明個人行為風波與國安／晶片出口調查不是二選一，而是**個人治理事件直接引爆國安出口連帶調查**，建議你下一輪把這兩條線的比重整併重估。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，補充 11/19 台股收盤破年線全貌**：今日台股集中市場終場收跌 **1,768.02 點（-4.40%）** 至 **38,426.89 點**（成交金額 **8,952.81 億元**、上漲 69 家、下跌 1,014 家，**20 檔千金股收跌停**，櫃買終場重挫 **7.22%**），本週跌逾 10% 使證交所公開喊話穩定秩序（https://www.cna.com.tw/news/afe/202611190169.aspx ；https://news.cnyes.com/news/id/6667459 ，HTTP 200）。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意，補充深圳川習會對荷莫茲的新訊號**：清晨 3 艘油輪在荷莫茲海峽觸水雷起火（https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906 ），推升短期斷航上尾風險；但中午深圳川習會上，川普公開稱美中在「**確保能源順暢通過荷莫茲海峽及防止伊朗擁有核武**」上有非常強烈的共識（https://www.cna.com.tw/news/aopl/202611193005.aspx ，HTTP 200），外加 EIA 庫存大增與強美元，雙向拉扯下我仍維持 **55%**。
  5. **主線 5（「風險升級」劇本 33% vs 40%）— 同意方向一致**，差距僅 7 個百分點。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題
- 1. 檢視今天線上版《財經日曆》的 `PCE 物價（聯準會最重視的通膨）` 卡片，其實**已經顯示核心 PCE 年增 `3.1%`、前值 `0.3%`**；為什麼 `forecast.json`（更新時間 `11/19 07:03`）卻仍寫「9 月核心 PCE 數字：查無」？是預測腳本沒有讀取該表格，還是產出順序有落差？
- 2. 今日（11/19）中央社最新報導指出，與黃仁勳有染的女子正遭美政府調查是否涉中國情報與晶片走私（https://www.cna.com.tw/news/aopl/202611193003.aspx ），同時深圳「川習會」釋出美中「30 對 30」各降 300 億美元關稅與確保荷莫茲通航的訊號（https://www.cna.com.tw/news/aopl/202611193005.aspx ）——你下一輪會如何調整「輝達事件定性」以及「油價／風險升級」的機率？
- 3. 今日 `14:15` 剛更新的 `macro_voice.json`（午班）寫「新台幣只貶了一點點，三十二點九四」，但那是 11/18 舊數字，實際上今日（11/19）台北匯市盤中已貶破 33 元整數關卡至 33.04 元、午盤暫收 32.988 元。語音稿在引用台股收盤與台幣匯率時，為什麼仍會混用前一交易日的匯率？

---

### WIDE-1｜荷莫茲海峽 11/19 驚傳 3 艘油輪觸及水雷起火失能；川習會同日釋出確保航道順暢共識（更新）
- 事實：土耳其國營安納杜魯新聞社（AA）於台北時間 2026 年 11 月 19 日報導，伊朗軍方證實 **3 艘油輪在荷莫茲海峽東側觸及水雷並起火失能（disabled）**，伊朗稱該等船隻關閉導航系統並駛入禁航區；稍早阿聯 ADNOC 亦證實一艘旗下船隻在海峽航行時遇襲，造成 **11 名船員受傷、1 人失蹤**（https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906 ，台北時間 2026-11-19 10:34，HTTP 200 確認）。惟同日下午川普於深圳川習會致詞稱，美中在確保能源順暢通過荷莫茲海峽與防止伊朗擁有核武上有非常強烈的共識（https://www.cna.com.tw/news/aopl/202611193005.aspx ，HTTP 200 確認）。
- 推理：美股昨晚（11/18）全數聚焦美國 EIA 原油與汽油累庫而使油價下跌，但今日清晨出現**實質水雷致油輪起火失能**，海運戰爭險費率與成品油裂解價差極易劇烈波動；美中在深圳口頭宣示保暢通能否壓住伊朗實際佈雷行動，是未來 48 小時油價多空分水嶺。
- 先影響資產：布蘭特原油／柴油裂解價差、油輪與海運戰爭險費率、航空與石化類股。

### WIDE-2｜APEC 深圳「川習會」登場並談「30 對 30 協議」各降 300 億美元關稅，川普先會普丁 40 分鐘並接續美中俄三方峰會（重大更新）
- 事實：11/19 中午美中元首今年第三次「川習會」在深圳麒麟山莊登場，美方由川普率國務卿盧比歐、商務部長盧特尼克、財長貝森特與貿易代表葛里爾全員出席；川普致詞稱美中已就「**30 對 30 協議（30 for 30 deal）**」同意各自對價值 **300 億美元**商品削減關稅，並希望終結每個月造成 2.5 萬人喪命的俄烏戰爭。稍早川普已與普丁單獨會談約 **40 分鐘**，會後將緊接舉行美中俄三方峰會；惟美國之音（VOA）引述分析指出美中貿易休戰仍脆弱，華府同時要求北京落實農產品採購與稀土出口放寬（https://www.cna.com.tw/news/aopl/202611193005.aspx ；https://www.cna.com.tw/news/acn/202611190138.aspx ；https://www.voachinese.com/a/trump-meets-putin-in-shenzhen-as-trade-disputes-loom-over-talks-with-xi-20261119/8225437.html ，均 HTTP 200 確認）。
- 推理：雙邊削減 300 億美元關稅雖是短期緩和訊號，但同日 BIS 遠端算力新規生效且川普表示 Blackwell 晶片仍須「再等 2 至 3 年」，代表美中經貿正走向「消費／農產品微幅降稅、先進算力與國安管制繼續收緊」的結構分化。
- 先影響資產：USD/CNH、中概股（KWEB）、美國農產品期貨、歐洲天然氣與國防股。

### WIDE-3｜英國 10 月 CPI 升至 3.6%（核心持平 2.8%）、歐盟秋季經濟預測示警通膨 3.3% 黏著，疊加歐盟「數位公平法」與法國港口罷工（新）
- 事實：MUFG Research 11/18 彙整英國最新通膨與勞動數據顯示，英國 10 月整體 CPI 年增率由 3.5% 升至 **3.6%**（主要由能源推動），核心 CPI 維持 **2.8%**、失業率降至 **4.6%**，市場觀望英國央行 12 月 17 日會議是否接續升息（https://www.mufgresearch.com/macro/european-macro-18-november-2026/ ，HTTP 200 確認）；歐盟執委會發布 2026 年秋季經濟預測，雖將今年歐元區 GDP 成長由 0.9% 上修至 **1.2%**（歐盟由 1.1% 上修至 **1.4%**），但明言通膨更強且持久，估歐盟 2026 年全年通膨達 **3.3%**（https://www.eunews.it/en/2026/11/17/eurozone-and-eu-growth-to-top-forecasts-in-2026-though-inflation-remains-a-drag/ ，HTTP 200 確認）。另歐盟執委會本週推出「消費者包裹／數位公平法（Digital Fairness Act）」擬直接以統一法規禁絕深色模式（dark patterns）、成癮設計與不透明動態定價並擴大跨境直接罰款權（https://commission.europa.eu/law/law-topic/consumer-protection-law/digital-fairness-act_en ，HTTP 200 確認）；且法國本週出現 24 小時全國港口與碼頭罷工，推高歐洲港埠貨物滯留時間（https://www.hillebrandgori.com/port-updates ，HTTP 200 確認）。
- 推理：美股目前定價焦點幾乎只在聯準會，但英、歐通膨同時回升至 3.3%–3.6%（且法、英勞動與港口摩擦加劇），會使歐元區與英國利率維持高檔更久，對歐洲消費、跨國電商／遊戲／AI 訂閱平台合規成本及歐元區主權債利差形成雙重壓力。
- 先影響資產：英國公債（Gilts）、EUR/USD、法德 10 年期公債利差、歐洲電商與數位平台股。

### WIDE-4｜印度 10 月通膨升至 6.09% 兩年來首破央行上限，破紀錄「單月逾百億美元」外資流入正面臨升息逆風（新）
- 事實：CNBC 於台北時間 11 月 19 日清晨報導，印度 10 月零售通膨（CPI）年增率升至 **6.09%**，為兩年來首度突破印度央行（RBI）**6%** 容忍上限，主因食物與運輸成本飆升，且通膨已連續 12 個月上揚；與此同時，11 月以來外資已淨流入印度股市逾 **100 億美元**創單月新高紀錄，原本押注非 AI 多元化配置的資金，正面臨企業轉嫁成本拖累農村與城市消費、並迫使 RBI 進一步升息的風險（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ，台北時間 2026-11-19 08:01，HTTP 200 確認）。
- 推理：外資近期從美股科技與東北亞撤出後，印度是最主要的新興市場避風港（單月吸金逾 100 億美元）；若印度因國內食物＋國際油價雙重通膨被迫連環升息，這股「非 AI 避風港」行情一旦反轉，會加速新興市場資金回流美元現金。
- 先影響資產：印度 Nifty 50／銀行與汽車消費股、印度盧比（USD/INR）、新興市場 ETF（EEM / INDA）。

### WIDE-5｜美國會 USCC 11/19 年報示警未來 24 個月台海關鍵期；新加坡與美啟動 BIS 實務協商；中加啟動 2,000 億人民幣換匯測試（更新）
- 事實：美國「美中經濟暨安全檢討委員會（USCC）」2026 年度國會報告台灣章節指出，**未來 24 個月**將形塑長期兩岸關係，若北京透過 11 月底台灣地方選舉與 2028 年大選評估政治脅迫效果不如預期，對台海採取隔離或封鎖的風險將提高（https://www.uscc.gov/sites/default/files/2026-11/2026_Annual_Report_to_Congress.pdf ，HTTP 200；https://www.rti.org.tw/en/news?uid=3&pid=1052391 ，HTTP 200）；同日新加坡 MDDI 部長楊莉明與美 BIS 副部長 Jeffrey Kessler 會談後同意就受信任新加坡用戶取得先進晶片展開實務安排跟進（https://www.channelnewsasia.com/singapore/singapore-us-semiconductor-mddi-josephine-teo-6560761 ，HTTP 200）；另第一財經（Yicai）11/18 報導，中國央行行長潘功勝與加拿大財長、央行總裁正式簽署《中加金融工作小組職權範圍》，並承諾對近期續簽的 **2,000 億人民幣**雙邊本幣互換協議進行實務測試與動用演練（https://www.yicaiglobal.com/news/china-canada-deepen-financial-ties-with-new-cooperation-framework ，HTTP 200 確認）。
- 推理：在美國緊縮第三國算力與金融盡職審查之際，新加坡迅速建立合規白名單樞紐、中國與加拿大則推動本幣互換實操測試，顯示各區域金融與算力供應鏈正加速出現「合規標準分岔」。
- 先影響資產：台股半導體權值股（2330 / TSM）、USD/TWD、USD/CAD、東南亞資料中心 REITs。

---

### A｜今天的大動（對照 `/api/gemini_ask` 14:31 即時清單）

### PANW｜同意本站早班對正規盤的判斷；Palo Alto Networks（PANW）11/18 正規盤先漲 +9.90%，盤後 Q1 FY27 財報全面優於預期並宣布 45 億美元併購 Applied Compute 再漲 +9.1%
- 事實：美東 11 月 18 日正規盤 PANW 已先上漲 **+9.90%**（由前收 $309.29 漲至 **$339.92**）；盤後公布 Q1 FY27 財報，營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億美元）、Non-GAAP EPS **1.05 美元**（優於預期 0.97 美元）、次世代資安 ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**（FactSet 共識 141.7 億美元）、調整後 EPS 指引至 **4.26～4.30 美元**（FactSet 共識 4.18 美元），並宣布以 **45 億美元**全股票收購開源權重 AI 模型後訓練／推論平台 **Applied Compute**，帶動盤後／盤前再漲 **+9.1%**（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19，HTTP 200 確認；https://www.morningstar.com/news/marketwatch/20261118420/palo-alto-networks-stock-gets-a-fresh-ai-fueled-boost-from-earnings ，台北時間 2026-11-19，HTTP 200 確認；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，HTTP 200 確認）。
- 本站漏掉的：即時題目單（14:31）仍標「本站沒有找到對得上的新聞」。另同日盤後 **Everpure（NYSE: P，原 Pure Storage）** Q3 FY27 營收年增 **51%** 至約 **14.6 億美元**（新聞稿約 $1.5B）、調整後 EPS **0.86 美元**並連三季上調全年指引至 **52.0 億～52.1 億美元**（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ，HTTP 200）；KeyBanc 分析師 Eric Heath 亦將 PANW 由 Sector Weight 調升至 **Overweight**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200）。

### CRWD｜CrowdStrike（CRWD）11/18 正規盤漲 +7.95% 收 $237.03，盤後／盤前受 PANW 財報驗證 AI 資安需求外溢續漲 +6.0%（更新精確收盤價）
- 事實：CRWD 美東 11 月 18 日正規盤由前收 $219.58 大漲 **+7.95%** 至 **$237.03**，盤後／盤前再漲 **+6.0%**，主因同業 PANW 財報驗證企業 AI 資安需求強勁而出現板塊連動（https://www.globalbankingandfinance.com/crowdstrike-holdings-crwd-rises-2026-11-18/ ，HTTP 200 確認；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200）。近期 Cantor Fitzgerald 亦維持 **Overweight** 並調高對 CRWD 的看法至 **$275**（https://www.tikr.com/zh/blog/cantor-fitzgerald-raises-its-crowdstrike-target-to-275-is-it-still-too-low ）。
- 本站漏掉的：即時題目單（14:31）仍標「本站沒有找到對得上的新聞」。經查 CRWD 預計 **12 月 1 日盤後**才公布財報，11/18 盤後至今日並無單獨公司公告（找不到來源），屬同業財報帶動的板塊外溢。

### CVX｜雪佛龍（CVX）受 11/18 除息每股 1.78 美元、EIA 原油與汽油庫存大增壓低油價，以及 50 億美元併購談判影響，未還原跌 4.74%、還原息後跌 3.95%（更新精確口徑）
- 事實：CVX 美東 11 月 18 日正規盤收在 **$205.88**（較 11/17 收盤 $216.13 **未還原跌 4.74%**，扣除當日季股息 **每股 $1.78** 除息調整後為 **-3.95% / 約 -4.0%**），由三件事疊加：（1）11/18 為每股 $1.78 季股息除息日；（2）EIA 公布上週美國原油庫存大增 **340 萬桶**、汽油大增 **520 萬桶**，壓低油價並使能源股集體下挫（XOM、CNQ 同步走弱）；（3）市場消化其接近以 **50 億美元**收購墨西哥灣深水油商 **Beacon Offshore Energy** 的談判消息（https://www.globalbankingandfinance.com/chevron-cvx-falls-2026-11-18/ ，HTTP 200；https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ；https://www.nationthailand.com/news/world/40073656 ；https://www.bicmagazine.com/industry/investment-banking/chevron-closes-in-on-5b-beacon-deal/ ）。
- 本站漏掉的：即時題目單（14:31）仍標「本站沒有找到對得上的新聞」；當日屬除息與 EIA 庫存引發之能源板塊集體修正，非雪佛龍單一基本面突發利空。

### CNQ｜Canadian Natural Resources（CNQ）11/18 正規盤隨油價重挫跌 4.63%（$45.53），盤前 +3.2% 無單獨公告或報告（無新進展，找不到來源）
- 事實：CNQ 美東 11 月 18 日正規盤隨北美能源股重挫收跌 **4.63%**（由 $47.74 跌至 **$45.53**，多倫多跌 4.06% 至 C$65.52），市場亦消化其宣布以 **25.3 億加元**收購 **Advantage Energy** 之支出（https://www.nationthailand.com/news/world/40073656 ；https://www.newsfilecorp.com/release/324091/Canadian-Natural-Resources-Limited-Enters-into-Agreement-to-Acquire-Advantage-Energy-Ltd ）。
- 事實（盤前 +3.2%）：經查公司公告、交易所與主流媒體，美東 11/18 盤後至今日美東深夜 **沒有任何 CNQ 新聞、財報或分析師調評**（找不到來源）。
- 本站漏掉的：即時題目單（14:31）仍僅標盤前 `+3.2%` 且稱找不到新聞，未呈現前一日正規盤重挫 `-4.63%` 的完整脈絡。

---

### AN｜AN-1：最近 3 小時內（台北 11:45–14:45）無新增美股分析師調評；補齊大摩對台積電、Piper Sandler 調升 MDT、HSBC／華爾街 10 家投行調降 NVDA 可查證原文
- 事實：檢索最近 3 小時（台北 11:45–14:45／美東 11/18 22:45–11/19 01:45 深夜時段），AI 供應鏈與美國市值前 20 大公司並無新發布的美股券商評等調整（找不到來源）。
- 事實（今日台灣／亞洲與本週已公開可查證重要報告）：
  1. **摩根士丹利（11/19 亞太高峰會後報告，鉅亨網／PTT 彙整）**：維持 **台積電（2330）** `Overweight`（增持）評等與產業「有吸引力」看法，將估值看法調高至 **3,088 元**，預估 2027 年 2 奈米產能翻倍以上，並預估 2026／2027／2028 年 EPS 分別為 **112.10／148.64／189.81 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，台北時間 2026-11-19，HTTP 200 確認）。
  2. **Piper Sandler**：將 **Medtronic（MDT）** 評等由 Neutral 調升至 **Overweight**，估值看法由 $85 調高至 **$120**（https://www.tradingview.com/news/tradingview:5b080eae6cc49:0-piper-sandler-upgrades-medtronic-to-overweight-from-neutral-raises-price-target-to-120-from-85/ ，HTTP 200 確認）。
  3. **HSBC／華爾街 10 家投行對 NVDA 調整**：HSBC 分析師 Frank Lee 將 **NVDA** 由 Buy 調降至 **Hold**（看法自 $365 調降至 **$170**），指出在確認永久執行長人選與展現執行力前股價恐持續承壓（https://www.tradingview.com/news/binance_news:d94dcaa1f094b:0-hsbc-downgrades-nvidia-says-stock-may-struggle-until-new-ceo-is-named/ ，HTTP 200 確認）；另 Benzinga 統計黃仁勳離任前後共 10 家機構下調 NVDA（包含 11/11 Baird Outperform→Neutral、11/12 Evercore ISI Outperform→In-Line 看法 $465→$186、11/12 Bernstein Outperform 調降看法 $400→$200 等）（https://www.tradingview.com/news/benzinga:3bce7f47b094b:0-nvidia-gets-10-bank-downgrades-after-huang-exit-what-to-expect-ahead-of-q3-results/ ，HTTP 200 確認）。
  4. **Moody's Ratings（11/18）**：維持 **NVDA** Aa1 債信評等，將展望由 **Positive 調降至 Stable**（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ，HTTP 200）。
  5. **KeyBanc**：分析師 Eric Heath 將 **PANW** 由 Sector Weight 調升至 **Overweight**、看法調高至 **$380**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200）。
  6. **YR Research（11/18）**：將 **AAPL** 由 **Sell 調升至 Hold**（https://www.tradingview.com/news/seekingalpha:d985f509f094b:0-sa-analyst-upgrades-downgrades-nvda-aapl-smci-tsla/ ，HTTP 200）。
  7. **Raymond James**：維持 **SMCI** 偏多評等與 **$65** 看法（對照 Susquehanna 維持 Negative、看法 $18）（https://247wallst.com/investing/2026/11/18/super-micro-computers-40-3-month-downturn-a-great-entry-point-says-this-wall-street-pro-who-predicts-165-returns/ ，HTTP 200）。
  - 另見報導彙整 Rothschild & Co Redburn 調降 AVGO（Buy → Neutral），單篇直連網址於外部抓取回傳 403（單篇直連網址：找不到來源）。

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）刊登聯邦公報生效，新加坡與美展開實務協商（無新進展）
- 事實：美國商務部工業安全局（BIS）暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢至 2027-01-19）。新規增訂 § 744.24 遠端存取終端用途管制，限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則（https://public-inspection.federalregister.gov/2026-23529.pdf ，HTTP 200；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ，HTTP 200；https://www.milbank.com/en/news/bis-issues-new-rule-restricting-remote-access-to-advanced-chips.html ，HTTP 200）。
- 事實：新加坡 MDDI 部長楊莉明已與美國 BIS 副部長 Jeffrey Kessler 會談並同意跟進「受信任用戶」實務安排；馬來西亞亦正尋求釐清規範（https://www.channelnewsasia.com/singapore/singapore-us-semiconductor-mddi-josephine-teo-6560761 ，HTTP 200；https://www.cna.com.tw/news/afe/202611190022.aspx ，HTTP 200）。

### POL-2｜美國財政部 FinCEN 發布強化客戶盡職審查（CDD）新規提案、9 月 TIC 淨流入 2,610 億美元與 OFAC 制裁（更新 FinCEN 公告）
- 事實（更新）：美國財政部金融犯罪執法網絡（FinCEN）發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，落實第 14406 號行政命令，60 天公眾意見徵詢），明確授權金融機構為防制風險或監管需求向法人客戶實質受益人蒐集額外資訊，並將「同一法人客戶開立新帳戶免重複驗證實質受益人」豁免規則法典化（https://home.treasury.gov/news/press-releases/sb0691 ，HTTP 200 確認）。
- 事實（無新進展）：美國財政部公布 9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ，HTTP 200）；OFAC 宣布「Operation Economic Outcast」制裁真主黨與伊朗聖城軍黃金及現金網路（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 重申美國優先供應鏈韌性（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）；白宮發布亞洲經濟協議事實清單（https://www.whitehouse.gov/fact-sheets/2026/11/fact-sheet-president-donald-j-trump-secures-historic-economic-deals-for-american-workers-and-strengthens-americas-leadership-in-asia/ ）；CMS CRUSH 反詐欺提案（`2026-23461`）11/19 刊登聯邦公報（https://public-inspection.federalregister.gov/2026-23461.pdf ，HTTP 200）。

---

### TW-1｜台股 11/19 收盤跌 1,768.02 點收 38,426.89 點（成交 8,952.81 億、摜破年線、20 檔千金股跌停）；證交所 BFI82U 待 15:00 後公布（更新收盤細節）
- 事實（11/19 13:30 收盤完整官方與媒體統計）：台股今日開 40,145.73 點、高見 40,315.53 點、低探 38,259.70 點，終場收 **38,426.89 點（大跌 1,768.02 點 / -4.40%，史上第 7 大收盤跌點，摜破年線）**，集中市場成交金額 **新台幣 8,952.81 億元**（上漲 69 家、下跌 1,014 家、持平 30 家）；櫃買指數終場收跌 **7.22%**；類股中塑膠指數大跌 **8.77%**、電子跌 **4.7%**、半導體跌 **4.29%**、金融跌 **2.14%**。權值股**台積電（2330）**收 **2,100 元（-3.45%，跌破年線）**、聯發科（2454）跌 5.58% 收 3,720 元、鴻海（2317）微跌 0.23% 收 220.5 元、緯穎（6669）跌逾 4% 收 1,410 元、南亞科與華邦電重挫逾 9%；**20 檔千金股收在跌停價位**（信驊收跌停 8,730 元，光聖、竑騰跌出千金）。由於本週累跌逾 10%，台灣證交所公開表示必要時將採穩定措施維持交易秩序（https://www.cna.com.tw/news/afe/202611190149.aspx ，台北時間 2026-11-19 13:54，HTTP 200；https://www.cna.com.tw/news/afe/202611190169.aspx ，HTTP 200；https://news.cnyes.com/news/id/6667459 ，HTTP 200）。
- 事實（違約交割與法人／匯率進度）：11/18 上市櫃共 **9 檔熱門 AI 股**達標重大違約交割 **4.269 億元**（整體買賣違約約 9.64 億元），今日盤中全數一度亮燈跌停（https://www.chinatimes.com/realtimenews/20261119002092-260410 ，HTTP 200）。截至 **台北時間 2026-11-19 14:43**，證交所 `BFI82U` 尚未產出今日三大法人買賣超、期交所亦尚未產出今日未平倉（均於 15:00 後公布），新台幣 16:00 收盤價亦尚未產生（午盤暫收 **32.988 元**，早盤曾貶破 33 元見 33.04 元，https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200）。

### TW-2｜Anthropic 自建資料中心牽動台鏈 TPU 機櫃轉單（英業達／廣達／鴻海）；廣達公告納許維爾廠租約；日月光 2,489 億動土與海龍風電售台積電（重大更新）
- 事實（新補充）：中央社 11/19 引述智璞產業趨勢研究所分析，Anthropic 至 2045 年算力需求換算晶圓約 **40 萬至 70 萬片**（集中於 2026–2028 年），占台積電 CoWoS 年產出 **1 至 2 成**、前段晶圓僅 **3% 至 6%**，對產能滿載的台積電屬客戶結構微調而非額外紅利，且台積電董事會核准上限 **5 億美元**參與其同步私募；反觀 Anthropic 直接向博通租賃 **3.5 GW** Google TPU 機櫃自建資料中心，繞過部分雲端中間商，法人推估深耕 Google TPU 主機板與機櫃組裝的**英業達、廣達、鴻海**與散熱／電源台廠可望受惠訂單移轉（https://www.cna.com.tw/news/afe/202611190156.aspx ，台北時間 2026-11-19，HTTP 200 確認）。
- 事實（新補充）：**廣達（2382）**於 11/18 14:31 重訊代子公司 Quanta Manufacturing Nashville, LLC 公告取得美國田納西州 La Vergne 約 **252,072 平方英尺**廠房 **62 個月**租賃使用權資產（IFRS16 使用權資產約 1,187.9 萬美元、合約總金額約 **1,490.8 萬美元**）（https://news.cnyes.com/news/id/6666244 ，HTTP 200 確認）。
- 事實（保留今日稍早新訊）：**日月光投控（3711）**旗下福雷電子今日（11/19）在高雄仁武產業園區 J 坵塊新廠動土，投資 **新台幣 2,489 億元**擴充 AI 高階測試產能，預計 2028–2029 年分期完成（https://www.cna.com.tw/news/afe/202611190122.aspx ，HTTP 200）；**海龍離岸風電 2A 風場**終止台電躉購改簽 CPPA 將綠電轉售予**台積電**（https://www.cna.com.tw/news/afe/202611190102.aspx ，HTTP 200）；**台積電**資深副總張曉強公開表態深化與輝達協作（https://www.ctee.com.tw/news/20261119700076-439901 ，HTTP 200）；**鴻海（2317）**斥資 72.4 億日圓收購日本 Sony 半導體車載相機模組事業（https://www.ctee.com.tw/news/20261119700316-439901 ，HTTP 200）；**偉詮電（2436）**確定明年初調漲售價（https://www.cna.com.tw/news/afe/202611190036.aspx ，HTTP 200）；**元太（8069）**11/18 晚間公告資安異常（https://www.cna.com.tw/news/afe/202611180336.aspx ）。
- 傳聞（無新進展）：外媒轉述《工商時報》稱台積電依客戶資產負債表設 AI 信用額度、超額須預付現金，尚未獲官方證實（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ）。

### TW-3｜愛德萬 V93000 EXA Scale QX 與台韓出口數據（無新進展）
- 事實：愛德萬 11 月發表 36 槽四卡籠架構 **V93000 EXA Scale QX** 測試系統鎖定高功耗 AI 晶片；韓國 11 月前 10 天出口年增 **111.9%**（半導體年增 **331.2%**），台灣 10 月出口年增 **58.9%** 至 **967.6 億美元**（https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ；https://cyprusshippingnews.com/2026/11/13/south-koreas-exports-surge-toward-1-trillion-as-chip-shipments-more-than-quadruple/ ）。

---

### EARN-WMT｜沃爾瑪（WMT）Q3 FY27 財報（今晚美東 11/19 07:00／台北 20:00，無新進展）
- 事實：美東 **2026-11-19 07:00 財報、08:00 電話會議**（台北 **11/19 20:00／21:00**）；TradingView 彙整市場共識營收約 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（公司上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售成長 3.0%–3.75%）；選擇權隱含波動 **±5.78%～±5.89%**（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ，HTTP 200；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，HTTP 200）。

### EARN-BABA｜阿里巴巴（BABA）Q2 FY27 財報（今晚美東 11/19 盤前／台北 20:00 電話會議，補充 Nasdaq 官方通知）
- 事實：美東 **2026-11-19 盤前**公布（電話會議美東 07:00／台北 **20:00**，https://www.nasdaq.com/press-release/alibaba-group-will-announce-september-quarter-2026-results-november-19-2026-2026-11 ，HTTP 200 確認）；Barchart 彙整預期營收約 **404.1 億～404.8 億美元**（年增約 8.9%–16%）、調整後 EPS 約 **1.56～1.71 美元**（本站日曆列 1.56 美元）（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ，HTTP 200）。

### EARN-PDD｜拼多多（PDD）Q3 2026 財報（今晚美東 11/19 盤前／台北 20:00–21:00，無新進展）
- 事實：美東 **2026-11-19 盤前**（電話會議 07:30 ET／台北 20:30）；TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS 約人民幣 **18.72～19.02 元**（約 **2.61～2.77 美元**，本站日曆列 2.61 美元）（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ，HTTP 200）。

### EARN-INTU / ROST / GAP / WSM｜今日（11/19）美東盤前與盤後其餘財報（無新進展）
- 事實：
  - **WSM（盤前／台北 11/19 20:00）**：TradingView 彙整共識營收約 **19.8 億～20.0 億美元**、EPS **2.19 美元**（https://www.tradingview.com/news/tradingview:5796c7c550438:0-wsm-q3-26-earnings-eps-estimate-is-2-19-usd/ ，HTTP 200）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收約 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（公司原財測 2.44–2.48 美元），選擇權隱含波動約 ±8.9%–10.5%（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ，HTTP 200）。
  - **ROST（盤後／台北 11/20 05:00）**：Zacks／TradingView 彙整共識營收約 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ，HTTP 200）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收約 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（公司原財測淨銷售成長 1.5%–2.5%）（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ，HTTP 200）。

### EARN-HPE / ZM / BBY / BURL / DKS / ADI / MDT / DELL / HPQ / ADSK / WDAY / DE｜11/23–11/25 財報（更正：移出 Zscaler ZS，實測為 12/02 盤後不在未來 10 天內）
- 事實：
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（本站日曆列 1.17，公司財測 1.20–1.30；選擇權波動 ±9.7%，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ，HTTP 200 確認；https://247wallst.com/investing/2026/11/09/dell-and-hpe-were-ai-winners-until-the-selloff-can-earnings-put-them-back-on-track/ ）；**ZM** 預期 11/23 盤後公布，共識營收 **12.8 億美元**、EPS **1.49 美元**（單篇新聞直連網址：找不到來源）。
  - **11/24 盤前（台北 11/24 21:00）**：**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**（https://www.tradingview.com/news/tradingview:6917007d5e261:0-burl-q3-26-earnings-revenue-estimate-is-2-97b-usd/ ，HTTP 200）；**DKS** 共識營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ，HTTP 200）；**ADI** 共識營收 **43.2 億美元**、EPS **3.89–3.92 美元**（本站隱含波動 ±8.09%）；**MDT** 共識營收 **94.6 億～94.8 億美元**、EPS **1.33–1.34 美元**；**BBY** 共識營收 **98.8 億～98.9 億美元**、EPS **1.48–1.49 美元**（ADI／MDT／BBY 單篇新聞直連網址：找不到來源）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億～492.5 億美元**（公司財測約 490 億）、調整後 EPS **6.41–6.60 美元**（本站列 6.41，隱含波動 ±14.85%，https://www.tradingview.com/news/tradingview:e525c4bdcb809:0-dell-q3-26-earnings-revenue-estimate-is-49-25b-usd/ ，HTTP 200）；**WDAY** 共識營收 **26.9 億美元**、EPS **2.75 美元**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ，HTTP 200）；**HPQ** 共識營收 **153.0 億～155.8 億美元**、EPS **0.72–0.76 美元**；**ADSK** 共識營收 **21.3 億美元**、EPS **2.91–3.07 美元**（HPQ／ADSK 單篇新聞直連網址：找不到來源）。
  - **11/25 盤前（台北 11/25 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（本站隱含波動 ±7.23%，https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ，HTTP 200）。
  - **更正備註（Zscaler ZS）**：上一版誤列 **ZS** 於 11/24 盤後，經核對公告確認 ZS Q1 FY27 財報日為 **美東 2026-12-02 盤後（台北 12/03 05:00）**，不在未來 10 天（11/19–11/29）內；其重申之 Q1 營收指引為 9.35 億～9.39 億美元、Non-GAAP EPS 1.15–1.16 美元（https://www.tradingview.com/news/tradingview:c28752bb00e6f:0-zscaler-hosts-2026-investor-day-reaffirms-q1-and-fiscal-2027-guidance/ ，HTTP 200 確認）。

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ，HTTP 200）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（強烈偏升息，無新進展）
- 事實：Waller 於 11/18 受訪指出聯準會可能需要「shock people」壓抑 3% 通膨預期固著，12/8–9 會議應考慮一次升息 50 基點（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ，HTTP 200）。

### FED-3｜聯準會理事 Michael S. Barr（偏升息）、紐約聯準銀行總裁 John Williams（反對一次升息 2 碼）；補充今日 Goolsbee 問答與理事會閉門貼現率會議（更新）
- 事實（無新進展）：Barr 11/18 在紐約聯準銀行演說指出通膨仍過高、若經濟按預期演進適合進一步升息（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ，HTTP 200）；Williams 舞台對談明確反對 12 月一次升息 0.50%（`"I don't see a need for dramatic action right now"`，偏漸進升息，https://www.chosun.com/english/market-money-en/20261119/3ZAB4T3MGVF4HLNUXPSHRHLNCI/ ，HTTP 200）。
- 事實（今日行程更新）：聯準會理事會於 **美東 2026-11-19 15:00（台北 11/20 04:00）** 舉行閉門會議審議各區聯準銀行預支與貼現率（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ，HTTP 200 確認）；芝加哥聯準銀行總裁 Austan Goolsbee 預計 **美東 2026-11-19 12:30（台北 11/20 01:30）** 於印第安納經濟俱樂部出席問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ，HTTP 200 確認）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼約 90%–95%、升息 2 碼約 5%–10%（無新進展）
- 事實：聯邦基金期貨幾乎完全定價 12/9 升息 1 碼（約 90%–95%），升息 2 碼約 5%–10%，暫停升息已完全被定價排除（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ，HTTP 200）。

---

### CALL-PANW｜Palo Alto Networks（PANW）Q1 FY27 法說會：NGS ARR 年增 66%、斥資 45 億美元併購 Applied Compute 搶進企業混合 AI 安全（補充 MarketWatch 佐證）
- 事實：PANW 執行長 Nikesh Arora、財務長 Dipak Golechha 與技術長 Lee Klarich 於美東 11/18 盤後召開 Q1 FY27 電話會議，指出 AI 加速資安漏洞發現速度、企業正急於從分散工具轉向整合平台，旗下 Prisma AIRS ARR 近 **1.7 億美元**（逾 1,000 家客戶），同時宣布以 **45 億美元**全股票併購 Applied Compute（https://www.morningstar.com/news/marketwatch/20261118420/palo-alto-networks-stock-gets-a-fresh-ai-fueled-boost-from-earnings ，HTTP 200 確認；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，HTTP 200 確認）。
- 原話（CEO Nikesh Arora）：`"As AI accelerates cyberattacks, enterprises are moving with urgency to replace disjointed tools with unified platforms."`

### CALL-P｜Everpure（NYSE: P，原 Pure Storage）Q3 FY27 法說會：營收年增 51%、連三季上調全年財測（無新進展）
- 事實：Everpure（NYSE: P）於美東 11 月 18 日盤後公布 Q3 FY27 財報，營收年增 **51%** 至約 **14.6 億美元**（新聞稿約 $1.5B）、調整後 EPS **0.86 美元**，並連三季上調 FY27 全年營收財測至 **52.0 億～52.1 億美元**（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ，HTTP 200）。
- 原話（CFO Tarek Robbiati）：`"Our results reflect the strength of our diversified portfolio, with our core and core AI offerings complemented by increasing contributions from our new businesses. We are raising full-year guidance for the third consecutive quarter and reiterating our strong preliminary FY28 outlook, underscoring confidence in our durable business model and broad-based momentum."`

### CALL-NVDA｜輝達（NVDA）Q3 FY27 法說會：營收 1,158 億美元、下季財測排除中國（無新進展）
- 原話：`"Our momentum is real... Customers, suppliers, and partners are 100% behind us. We’ve got this."`（https://www.cnbc.com/2026/11/18/nvidia-stock-earnings.html ，HTTP 200）。

### CALL-LOW｜Lowe's（LOW）Q3 2026 法說會：同店 +1.8%，2.5 億美元關稅退稅全數再投資（無新進展）
- 原話：`"We delivered strong top-line growth of over 9%, led by our sixth consecutive quarter of positive comparable sales, with continued momentum in Pro, online and home services."`（https://corporate.lowes.com/sites/lowes-corp/files/2026-11/q3-2026-press-release-v1.pdf ）。

### CALL-TGT｜Target（TGT）Q3 2026 法說會：同店成長 5.6%、全年 EPS 指引上調至 10.65–11.40 美元（無新進展）
- 原話：`"Our third-quarter results reflect continued progress against our strategic priorities, centered on serving busy families with our signature blend of style, design and value."`（https://www.prnewswire.com/news-releases/target-corporation-reports-third-quarter-earnings-302942872.html ）。

### CALL-TJX｜TJX Companies（TJX）Q3 FY27 法說會：同店成長 4%，看好 Q4 Marmaxx 加速（無新進展）
- 原話：`"Consolidated comparable sales grew 4%, driven by continued strength at HomeGoods, TJX Canada, and TJX International, and we saw improved sales at Marmaxx. Importantly, we expect further improvement at Marmaxx in the fourth quarter."`（TJX 官網 PDF 受 403 阻擋，單篇直連網址：找不到來源）。

---

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets / r/stocks）— 今晚掛牌在即，懷疑「退出流動性」與討論 Claude 定價影響交錯（無新進展）
- 討論內容與情緒：r/wallstreetbets 與 r/stocks 對定價 83 美元、募資 813 億美元的 ANT IPO 兩極分化，一面熱議史上最大掛牌是否引爆賭盤，一面普遍警覺龐大算力承諾恐讓散戶成為早期創投與避險基金的「退出流動性」（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xtuclv/nasdaq_confirms_anthropics_shares_will_begin/ ，HTTP 200）。

### SENT-2｜NVDA（r/wallstreetbets）— 財報大好卻走弱，社群嘲諷「沒有驚喜就是利空」與接班風波（無新進展）
- 討論內容與情緒：11/18 財報達標但股價回跌，r/wallstreetbets 討論串混雜對科技股連月回檔的疲勞感與「nothing burger」嘲諷，並熱議輝達 100 億美元參與 Anthropic 股份與管理層風波（熱度自 11/17–18 升溫；情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xyw3ym/what_are_your_moves_tomorrow_november_18_2026/ ）。

### SENT-3｜PANW／科技股財報（r/stocks）— 肯定資安與 AI 儲存動能但對軟體股估值審慎（無新進展）
- 討論內容與情緒：r/stocks 討論串肯定 PANW 平台化與 NGS ARR 成長，但整體對升息與 AI 高資本支出下的軟體股估值仍偏審慎（熱度自 11/18 升溫；情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-4｜UNH／管理式醫療（r/stocks）— CMS CRUSH 規則衝擊下偏悲觀觀望（無新進展）
- 討論內容與情緒：UNH 等醫療保險股受 CMS CRUSH 反詐欺規則影響連日承壓，散戶偏悲觀（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-5｜台股 11/19 收跌 1,768 點破年線與千金跌停潮（PTT 股板）— 盤中閒聊破 1,488 則留言與熱議大摩台積電報告（更新討論串網址）
- 討論內容與情緒：今日（11/19）台股收盤重挫 1,768.02 點收 38,426.89 點、20 檔千金股收跌停，PTT 股板《2026/11/19 盤中閒聊》置底文累積 **1,488 則**以上留言湧現恐慌與違約交割哀號；同板多篇高人氣新聞串熱議「大摩維持台積電 Overweight、3,088 元看法」與「輝達代理 CEO 提前 12 月加薪留才」（情緒，非事實；https://www.pttweb.cc/bbs/Stock/M.1795048218.A.865 ，HTTP 200 確認；https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，HTTP 200 確認；https://www.pttweb.cc/bbs/Stock/M.1795058772.A.5C2 ，HTTP 200）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，HTTP 200 確認）。
- 事實：核心 PCE（3.1%）高於核心 CPI（2.6%）之結構主因，係 2026 年住房／房租通膨降溫拉低權重較大的 CPI，而醫療服務、金融與軟體科技服務權重在 PCE 籃子較高且價格較黏著（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。

### TASK-B2｜11/19 台股收盤大跌 1,768.02 點收 38,426.89 點、成交 8,952.81 億元；證交所 BFI82U 與央行收盤價待 15:00／16:00 後公布（更新）
- 事實（11/19 13:30 收盤）：集中市場開 40,145.73 點、高 40,315.53 點、低 38,259.70 點，終場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，破年線）**，成交金額 **8,952.81 億元**；櫃買指數收跌 **7.22%**；台積電收 **2,100 元（-3.45%）**；證交所聲明必要時採穩定措施（https://www.cna.com.tw/news/afe/202611190149.aspx ，HTTP 200；https://www.cna.com.tw/news/afe/202611190169.aspx ，HTTP 200；https://news.cnyes.com/news/id/6667459 ，HTTP 200）。
- 事實（截至 14:43 最新可得與尚未公布項目）：經直連查詢證交所 `BFI82U`（`dayDate=20261119`），截至 **14:43** 尚未產出今日三大法人現貨買賣超，期交所台指期未平倉亦待 **15:00 後**公布；台北匯市尚未收盤（16:00 收盤），目前最新為 **午盤暫收 32.988 元（貶 4.1 分，盤中一度貶破 33 元見 33.04 元）**（https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200）。
- 事實（11/18 官方收盤對照）：加權指數收 **40,194.91 點（+102.80 點 / +0.26%）**；外資現貨賣超 **765.64 億元**；期交所三大法人台指期淨部位合計 **-7,322 口**（外資 -99,438 口、投信 +93,573 口、自營商 -1,457 口）；新台幣 11/18 收 **32.947 元**（https://www.cna.com.tw/news/afe/202611180304.aspx ，HTTP 200）。

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；保留掛牌前夕關聯股收盤表現（無新進展）
- 事實：Anthropic（代號 **ANT**）已定價 **每股 83.00 美元**（發行 9.8 億股、IPO 募資 **813.1 億美元**、完全稀釋估值約 **1.5 兆美元**），將於 **美東 2026-11-19 09:30（台北 11/19 22:30）** 正式掛牌；截至台北時間 14:45 美股尚未開盤，首日開盤價、收盤價與成交量將於明早 05:00 收盤後產生（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，HTTP 200；https://w.media/anthropic-ipo-priced-at-us-83-per-share-valuation-increases-to-us-1-5-trillion/ ，HTTP 200）。
- 事實：掛牌前夕美東 11/18 收盤，**CoreWeave（CRWV）跌 4.13%、IREN 跌 3.61%、Nebius（NBIS）小漲 0.87%、Oracle（ORCL）大致持平**；同日 **NVDA 收跌約 2.9%**，**AVGO、AMD 上漲約 4%–5%**（https://247wallst.com/investing/2026/11/18/coreweave-falls-5-despite-nvidia-sticking-to-its-financing-commitments-nebius-dips-oracle-holds-steady/ ，HTTP 200）。

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字（無新進展）
- 事實：ECB 11/18《金融穩定評估》Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（基於 LSEG 10/26 共識），指多數美國超大規模雲端業者 2026 年自由現金流因 AI 資本支出大於營運現金流而轉負（表層 FCF 口徑未納入未起租的表外租賃；表外承諾逾 4 兆美元係於圖表 A 與註腳 6 依 ASC 842 單獨揭露）（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200）。
- 事實：四巨頭截至 2026-09-30 最新一季自報實際數字如下：Meta（Q3 2026）OCF $32.79B − CapEx（含融資租賃本金）$34.91B = **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）；Alphabet（Q3 2026）OCF $42.29B − 現金 PP&E $51.36B = **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）；Amazon（Q3 2026／TTM）Q3 單季 OCF $42.42B、淨現金 PP&E $75.93B（單季隱含 -$33.51B）、自報 **TTM FCF -$42.36B**（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）；Microsoft（Q1 FY27）OCF $58.02B − 現金 PP&E $39.37B = **+$18.6B（仍為正；計入新起租融資租賃總資本支出 $45.2B 後仍約 +$12.8B）**（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### TASK-B5｜WMT、BABA、PDD 今晚 20:00–21:00 才公布 11/19 財報；附上最新共識（含來源名稱）、上季指引與關稅／消費原話（無新進展）
- 事實：三家均為 **美東 11/19 盤前（台北時間今晚 11/19 20:00–21:00）** 公布，截至台北 14:45 尚未發布實際財報。
- 事實（沃爾瑪 WMT，Q3 FY27）：TradingView 彙整市場共識營收 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（公司上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）；執行長 John Furner 對關稅退稅與消費者壓力的原話為 `"Customers are feeling some pressure, so we're proud of our investments... We'll do everything we can to keep prices as low as we can for customers throughout the rest of the year."`（https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ；https://www.businessinsider.com/walmart-using-tariff-refund-price-cuts-customer-experience-sales-2026-8 ）。
- 事實（阿里巴巴 BABA，Q2 FY27）：Barchart 彙整共識營收約 **404.1 億～404.8 億美元**（年增約 8.9%–16%）、調整後 EPS **1.56～1.71 美元**，市場聚焦阿里雲 AI 資本支出與中國消費補貼戰（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ）。
- 事實（拼多多 PDD，Q3 2026）：TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS **2.61～2.77 美元**，市場聚焦跨境關稅與小額免稅新規對 Temu 利潤率的影響（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ）。

---

### NEXT-1｜事件：Anthropic 9,009 億美元算力長約轉向自建資料中心（租賃博通 3.5 GW TPU）＋BIS 遠端算力管制生效＋台股斷頭重挫（更新）
- 推理：
  - 最先受影響的資產：台灣高融資中小型 AI 硬體股（櫃買終場 -7.22%、20 檔千金股跌停）、USD/TWD（早盤曾貶破 33 元見 33.04），以及東南亞與自建型資料中心租賃合約。
  - 傳導路徑：Anthropic 選擇直接向博通租賃 3.5 GW Google TPU 機櫃導入「Anthropic Direct」自建機房，對產能滿載的台積電（占 CoWoS 1–2 成）只是客戶結構微調，但卻使**訂單從傳統雲端中間商移轉至 Google TPU 機櫃組裝台廠**，同時疊加 BIS `2026-23529` 今日生效迫使合規產能往台灣／新加坡聚落集中（如日月光高雄仁武 2,489 億投資、廣達納許維爾租廠）（https://www.cna.com.tw/news/afe/202611190156.aspx ；https://news.cnyes.com/news/id/6666244 ）：
    - 美股：**AVGO、GOOGL、CRWV、NBIS、EQIX**（自建 TPU 與博通受惠 vs 單一 GPU 轉租雲端承壓）。
    - 台股：**廣達 (2382)、英業達 (2356)、鴻海 (2317)、台積電 (2330)、日月光投控 (3711)**（TPU 機櫃組裝與在台先進測試受惠 vs 短線籌碼去槓桿）。
  - 大家還沒注意到的間接受害者：**專靠「向單一雲端客戶轉租輝達 GPU」取得高溢價的二線新雲端與台灣中小型券商呆帳提存**——前者的議價能力被模型大廠「多晶片＋自建機櫃」削弱；後者因 9 檔違約 AI 股與 20 檔千金股跌停鎖死面臨融資追繳與權證避險滑價虧損（https://www.storm.mg/article/11182992 ）。

### NEXT-2｜事件：APEC 深圳「30 對 30 協議」各降 300 億美元關稅＋川普「Blackwell 等 2 至 3 年＆黃仁勳關聯女子遭調查」vs 荷莫茲水雷（更新）
- 推理：
  - 最先受影響的資產：離岸人民幣（USD/CNH）、布蘭特原油期貨與海運戰爭險費率、以及全球半導體設備／合規供應鏈股價。
  - 傳導路徑：深圳「川習會」一邊釋出 300 億美元對等降稅與確保荷莫茲通航的緩和訊號，另一邊川普同時點出 Blackwell 短期不放行且美國政府正在調查與黃仁勳有染女子是否涉及中國情報與晶片走私（https://www.cna.com.tw/news/aopl/202611193005.aspx ；https://www.cna.com.tw/news/aopl/202611193003.aspx ），代表貿易降稅不會換來先進算力鬆綁；而水雷實質毀損油輪仍考驗中東航道保險成本：
    - 美股：**NVDA、AMD、AVGO、FRO（Frontline）、STNG**。
    - 台股：**台積電 (2330)、聯發科 (2454)、長榮 (2603)、陽明 (2609)、台塑化 (6505)**。
  - 大家還沒注意到的間接受害者：**高度仰賴中國或東南亞中轉客戶、但缺乏「可信賴用戶」合規追蹤系統的二線 AI 伺服器與網通模組廠**——一旦美國調查延燒至實際走私節點，海關與出口稽核周期拉長將直接卡住營運資金週轉。

### NEXT-3｜事件：印度 10 月通膨 6.09% 破上限＋英國 CPI 升至 3.6%＋歐盟秋季預測通膨 3.3% 黏著＋法國港口罷工（新）
- 推理：
  - 最先受影響的資產：印度盧比（USD/INR）與印度金融消費股、英國 Gilts 與英鎊、歐洲長天期公債與運輸物流交期。
  - 傳導路徑：外資 11 月剛創紀錄向印度股市投入逾 100 億美元作為「非 AI 避風港」，但印度通膨突破 6% 上限疊加英國 3.6%、歐盟 3.3% 黏著通膨與法國港口罷工（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ；https://www.mufgresearch.com/macro/european-macro-18-november-2026/ ；https://www.hillebrandgori.com/port-updates ），全球央行被迫維持緊縮的範圍已從聯準會外溢到英國、歐元區與主要新興市場：
    - 美股：**INDA、EPI（印度 ETF）、EWU、FDX、UPS**。
    - 台股：**華城 (1519)、中興電 (1513)、巨大 (9921)、美利達 (9914)、豐泰 (9910)**（受歐洲／印度消費動能與港口交期影響）。
  - 大家還沒注意到的間接受益者：**美元貨幣市場基金與短天期美債（SGOV / BIL）**——當原本充當避風港的印度、歐洲也同時出現「通膨破表＋被迫升息」時，跨國資金最終只能回到無匯兌與升息雙重風險的美元短端現金。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 已由 60% 降至 45%）」
- 最強反方證據：BEA 官方新聞稿已證實 9 月核心 PCE 年增確為 **3.1%**（`https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026`），The Conference Board 預估 10 月將升至 **3.3%**（`https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026`），且本站《財經日曆》卡片亦已載明 9 月為 `3.1%` 並自估 10 月為 `3.2%`。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法發布年增率，這題將成為「無法判定」；但只要有公布年增率，低於 3.0% 的空間極小。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：我維持落在 2.4%–3.0% 僅約 **30%**（比你修正後的 45% 低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露多數一線雲端商 FCF 轉負且表外承諾逾 4 兆美元，今日（11/19）荷莫茲海峽再爆 3 艘油輪觸水雷起火（`https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906`），且台股收跌 1,768 點至 **38,426.89 點**（20 檔千金股收跌停）、迫使證交所喊話穩定秩序（`https://www.cna.com.tw/news/afe/202611190169.aspx`）。
- 另一種同樣說得通的解釋：就算 Williams 壓低 12 月升息 2 碼機率、美國垃圾債指數因能源權重撐盤未破 4%，「投資級科技債利差走寬＋中東油輪水雷＋亞股千點斷頭」就足以構成實質的「風險升級」。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：我維持「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你的 80% 低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：11/18 美國 EIA 原油庫存暴增 340 萬桶、汽油暴增 520 萬桶後，WTI 貼近 80 美元下緣，強美元亦壓抑商品；今日（11/19）雖有 3 艘油輪觸水雷起火，但深圳川習會同時釋出「美中確保荷莫茲能源通暢共識」（`https://www.cna.com.tw/news/aopl/202611193005.aspx`），使油價雙尾對撞更劇烈。
- 另一種同樣說得通的解釋：高庫存與高利率拉低基準需求（容易跌破 80 美元），而實質水雷與封鎖升級則可能瞬間衝破 100 美元——也就是油價**在 80–100 美元區間外的機率（雙尾）高於區間內**，並非單純看跌。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **未來 72 小時荷莫茲海峽通航／掃雷動態**。
- 機率估計：我維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」（重大更新反方與交叉證據）
- 最強反方證據（亦為雙方模型需修正之關鍵新訊）：中央社 11/19 引述《福斯新聞》報導川普親口指出，**與黃仁勳有染的一名女子正遭美國政府調查是否為中國情報機構工作、以及是否協助走私晶片**（`https://www.cna.com.tw/news/aopl/202611193003.aspx`）；同日輝達董事長瓊斯對員工重申「黃仁勳個人行為及缺乏坦誠」是董事會接受辭呈且永不回鍋的原因（`https://www.cna.com.tw/news/aopl/202611190029.aspx`）。
- 另一種同樣說得通的解釋：最初的確是「個人行為／缺乏坦誠」引發董事會 11/11 立即切割，但因牽涉對象本身被美方列為中國情報與晶片走私調查標的，**兩件事並非互斥，而是同一人物同時觸發公司治理與國安出口調查**；且台積電副總張曉強公開為輝達新團隊「站台」、輝達採購承諾增至 3,900 億美元，顯示公司本身目前尚未被列為制裁對象。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節，11 月下旬～12 月初）**與 **美國政府對該涉案女子／走私網絡之起訴或調查公告**。
- 機率估計：在納入今日中央社新訊後，我修正估計為「單純私人治理、完全無涉中國晶片調查」降至 **25%–30%**，「個人行為與中國晶片／情報調查兩線交織」升至 **70%–75%**（建議 `dots_read.json` 把兩種說法從對立改成因果交織）。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（無新進展）
- 事實：ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**（已超過帳上負債），且投資級科技長債利差已相對於同評級企業債走寬（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q `Commitments and Contingencies / Uncommenced Leases` 追蹤，及 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜缺少「非公開交易 BDC 限額贖回（Gating）、非銀金融槓桿（NBFI）與主權債財政－金融連動」監測（無新進展）
- 事實：金融穩定委員會（FSB）秘書長 John Schindler 在 RiskLive Asia 2026 演說與聯準會 FEDS Notes（2026-10-14）皆重點示警非銀行金融仲介（NBFI）、私募信貸不透明與避險基金槓桿（https://www.fsb.org/2026/10/innovation-and-resilience-managing-the-risks-of-a-changing-financial-system/ ，HTTP 200）。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜缺少「高集中度雲端／金融基建中斷與 SEC Item 1.05 資安事件」警報（無新進展）
- 推理：監測 SEC 8-K Item 1.05 是否涉及高集中度第三方基建（AWS、Azure、GCP、Cloudflare、DTCC），可比股價更早捕捉系統性中斷。免費資料源：CISA KEV JSON（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）＋ SEC EDGAR。

### BLIND-4｜「台股籌碼風向計」尚未合計三大法人台指期淨口數，亦未統計證交所單日違約交割金額（對照 14:16 更新線上版確認）
- 事實：檢視 11/19 線上「台股籌碼風向計與斷頭警戒」（最後更新 11-19 14:15／籌碼檢查 14:16），目前仍僅對 `外資台指期未平倉` 顯示單一數值，尚未加總投信與自營商為 **「三大法人合計淨空單 -7,322 口（11/18）」**，亦未納入證交所／櫃買每日違約交割金額統計（11/18 爆 9 檔達標 4.269 億元、整體買賣總額約 9.64 億元）。免費資料源：期交所「三大法人區分各期貨契約交易資訊」與證交所「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」（無新進展）
- 推理：建議在「IPO 觀察」補上大型 IPO 納入 S&P 500、Nasdaq-100 指數時程與被動 ETF 權重排擠效應說明。

---

### SITE-1｜`forecast.json` 寫「9 月核心 PCE 數字：查無」，但本站《財經日曆》PCE 卡片其實已顯示「核心 PCE 年增 3.1%」（14:22 線上版確認仍存在）
- 本站寫了什麼：`research_feed/forecast.json` 第 130 行仍寫著 `9 月核心 PCE 數字：查無。`。
- 正確應該是什麼：本站線上《財經日曆》分頁之 `PCE 物價（聯準會最重視的通膨）` 卡片（11/19 14:22 版）已明確顯示 `核心 PCE 年增 3.1%` 與 `前值 0.3%`，完全符合 BEA 官網新聞稿（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）。請將日曆卡片的前值資料管線串接至預測腳本。

### SITE-2｜11/19 `10:33 緊急加班` 語音稿截至 14:22 仍誤把「今天（11/19）台股盤中跌幅」講成「台股昨天收盤附近少了 3.4%」（確認仍存在）
- 本站寫了什麼：線上總覽 `🚨 緊急加班（2026-11-19 10:33 台北）` 語音文字稿仍寫著：`「台股昨天收盤附近比前一天少了三點四個百分點」` 且寫開盤前能源股跳空原因「我目前沒有找到」。
- 正確應該是什麼：台股「昨天（11/18）」收盤其實是**上漲 +102.80 點（+0.26%）收在 40,194.91 點**（https://www.cna.com.tw/news/afe/202611180304.aspx ）；`-3.4%`（今天最終收盤擴大為 `-4.40%`、收 38,426.89 點）是**今天（11/19）**的跌幅，且 11/18 恰為雪佛龍（CVX）每股 1.78 美元季息除息日（https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ）。

### SITE-3｜`macro_voice.json`（`11-19 14:15 午班`）將 11/18 新台幣「32.94」當成今天匯率，漏掉今日盤中已貶破 33 元至 33.04 元（新發現）
- 本站寫了什麼：`research_feed/macro_voice.json` 第 6 行與線上版《每日總經情勢（11-19 14:15）》寫道：`「新台幣只貶了一點點，三十二點九四，我沒查到外資今天買賣超的數字，只能說匯率沒有失控。」`
- 正確應該是什麼：**32.947 元**是 **11/18** 的收盤價；今日（11/19）台北匯市以 32.96 元開盤後，**盤中已貶破 33 元整數關卡至 33.04 元**、**午盤暫收 32.988 元（貶 4.1 分）**（https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200 確認）。雖然央行進場調節未失控，但文字稿不應把昨天的 32.94 當成今天的匯率。

### SITE-4｜`api/gemini_ask`（14:31 即時版）仍僅標示 `CNQ +3.2%（盤前）`，未附正規盤收跌 -4.63%（無新進展）
- 本站寫了什麼：`https://wallstreet-sentinel.pages.dev/api/gemini_ask`（台北 14:31）仍寫 `### CNQ｜CNQ（Canadian Natural Resources）今天 +3.2%（盤前）`，未呈現正規盤重挫 -4.63% 的完整脈絡（https://www.nationthailand.com/news/world/40073656 ）。

### SITE-5｜`upcoming.json`（14:22 版）之 WMT 公布時間與 HPE 共識 EPS 略低於市場實際公告與最新共識（確認仍存在）
- 本站寫了什麼：`https://wallstreet-sentinel.pages.dev/upcoming.json`（`asof: 2026-11-19 14:22`）將 `WMT` 時間列為 `2026-11-19T08:00`（台北 21:00），並將 `HPE` `eps_f` 列為 `1.17`。
- 正確應該是什麼：沃爾瑪官方公告 Q3 FY27 財報新聞稿於 **美東 07:00（台北 20:00）發布**、08:00（台北 21:00）才為電話會議（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ）；而 `HPE` 目前市場共識調整後 EPS 為 **1.27–1.29 美元**（公司自身財測 1.20–1.30 美元，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ）。

### SITE-6｜《未來 14 天事件》（14:16 版）仍未標明今日美債標售為「10 年期 TIPS」（更新：台股收盤 38,426.89 已修正）
- 本站寫了什麼：`新聞日曆`《未來 14 天事件》（最後更新 11-19 14:16）仍列 `11-19 美債 10 年期標售（增額） $19B`。
- 正確應該是什麼：今日 $19B 增額標售為 **10 年期 TIPS（抗通膨公債）**，建議加註「TIPS」以免與名目 10 年債混淆。（備註：上一輪回報的總覽 `台股加權 38,490` 延遲數字，截至 14:22 線上版已正確更新為收盤價 `38,426.89 -4.40%`。）

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆，對照 14:16／14:22 線上版核對（更正 ZS 日期與補充 11/19 聯準會行程）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳峰會（川習會＋美中俄三方峰會）；美東盤前（台北 20:00–21:00）**WMT、BABA、PDD、WSM** 財報；台北約 21:00（南非 15:00）**南非央行（SARB）利率決策**（https://www.sabcnews.com/sabcnews/analysts-expect-mpc-to-keep-interest-rates-unchanged/ ）；美東 09:30（台北 22:30）**Anthropic (ANT)、MapLight (MPLT)** 掛牌；美東 12:30（台北 11/20 01:30）芝加哥聯準銀行總裁 Goolsbee 問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；美東 13:00（台北 11/20 02:00）**美債 10 年期 TIPS 增額標售 $19B**；美東 15:00（台北 11/20 04:00）聯準會理事會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP** 財報（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  2. **11/20（五）**：**台灣經濟部 10 月外銷訂單**（台北 16:00，預估 1,125–1,159 億美元，https://money.udn.com/money/story/10869/9879179 ）；**美股月選擇權到期（OPEX）**；**密大消費者信心指數終值**（美東 10:00／台北 23:00）；**SanDisk (SNDK) 1 拆 8 分割**。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM** 財報。
  5. **11/24（二）**：美東盤前（台北 21:00）**ADI、MDT、BBY、BURL、DKS**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY**。
  6. **11/25（三）**：美東盤前（台北 21:00）**DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與 10 月耐久財訂單；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**；台北 11/26 **宏于電機（台股）掛牌**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/28（六）**：**台灣 2026 九合一地方選舉投票日**。
  10. **11/29（日）**：**OPEC+ 聯合部長級監督委員會（JMMC）會議**。
  11. **11/30（一）**：**MSCI 季度調整台股收盤生效（台北 13:30）與月底資產再平衡**。
  12. **12/01（二）**：美東 10:00（台北 23:00）**ISM 製造業 PMI 與 10 月 JOLTS 職位空缺**；**CRWD** 盤後財報（官網公告頁對外部自動抓取回傳 403，單篇直連網址：找不到來源；上一輪另列 NTAP 尚無單篇直連網址確認）；**韓國 11 月出口初值**。
  13. **12/02（三）**：美東盤後（台北 12/03 05:00）**Zscaler（ZS）** Q1 FY27 財報（較上一版誤列之 11/24 更正為 12/02）。
  14. **12/03（四）**：美國參議院資料中心聽證。
- 對照本站 11/19 14:16／14:22 線上版核對：
  - **正確部分**：`未來 14 天事件`（14:16）與 `upcoming.json`（14:22）已正確列出 WMT/BABA/PDD、ANT/MPLT、HPE、ADI、MDT、DELL、HPQ、DE、11/19 美債 10Y 增額 $19B、H.4.1、11/20 OPEX、11/25 GDP 與 PCE、11/30 月底再平衡、12/01 JOLTS；`休市與提早收盤` 亦正確列出 11/26 休市與 11/27 半天交易。
  - **漏掉部分**：`upcoming.json`（14:22）仍漏掉今晚盤後的 **INTU、ROST、GAP**、11/23 **ZM**、11/24 **BBY、BURL、DKS、ADSK、WDAY**；`未來 14 天事件`（14:16）仍漏掉 **11/19 南非央行、11/20 台灣 10 月外銷訂單、11/21 韓國 20 日出口、11/25 聯準會褐皮書、11/26 韓國央行、11/28 台灣九合一選舉、11/29 OPEC+ JMMC 會議**，且未併註 **11/26–27 感恩節休市與半天交易**。

---

### CODE-1｜wsb/analytics/bonds.py：第 110 行 `(_ago(s, 365) or float(s.iloc[-1]))` 在一年前期限溢酬為 0.0 或缺資料時，會錯把 `chg1y` 算成 0.0
- 檔案路徑與行號：`wsb/analytics/bonds.py` 第 106–111 行（特別是第 110 行）。
- 那一行在做什麼：`term_premium(eng)` 計算美國 10 年期期限溢酬（`THREEFYTP10`）現值與一年前相比的變化 `chg1y`。
- 為什麼有問題：第 110 行寫 `float(s.iloc[-1]) - (_ago(s, 365) or float(s.iloc[-1]))`。`THREEFYTP10`（期限溢酬）可正可負，當一年前數值恰好為 `0.0` 時，Python 把 `0.0` 當作 falsy，會改取 `float(s.iloc[-1])`，使 `chg1y` 被錯誤強制算成 `0.0`；此外當 `_ago(s, 365)` 為 `None`（資料不足 365 天）時，這裡會回傳 `0.0` 而不是像同檔案 `sovereign()` 第 63 行那樣回傳 `None`（把「沒有資料」偽裝成「變化為 0」）。
- 建議怎麼改：比照第 63 行寫法先存 `y1 = _ago(s, 365)`，改為 `"chg1y": None if y1 is None else float(s.iloc[-1]) - y1`。
- 確定度：高。

### CODE-2｜wsb/analytics/playbook.py：第 101 行 `.get("lift_adj", hz.get("lift"))` 在字典含有 `"lift_adj": None` 時不會退回 `"lift"`
- 檔案路徑與行號：`wsb/analytics/playbook.py` 第 101 行（`score()` 函式）。
- 那一行在做什麼：從崩跌機率模組 `odds` 的 `hz` 字典讀取調整後的倍率 `lift_adj`，若沒有則改用未調整倍率 `lift`。
- 為什麼有問題：第 101 行寫 `(hz or {}).get("lift_adj", (hz or {}).get("lift"))`。若上游輸出的 `hz` 明確帶有鍵值 `"lift_adj": None`，Python 的 `dict.get(key, default)` 會直接回傳 `None` 而不會使用後方的預設值 `hz.get("lift")`，進而導致第 109 行把崩跌機率誤判為缺漏（`missing.append("崩跌機率")`）。
- 建議怎麼改：改為 `la = (hz["lift_adj"] if hz.get("lift_adj") is not None else hz.get("lift")) if hz else None`。
- 確定度：中（屬防禦性修正，視上游 `odds` 是否會填入 `"lift_adj": None` 而定）。

（備註：本小時批次 `i % 24 == 14` 共 12 檔，其餘 10 檔 `tools/flow_guard.py`、`tools/site_energy.py`、`tools/site_legal.py`、`tools/site_stockcheck.py`、`wsb/analytics/event_react.py`、`wsb/analytics/stockscore.py`、`wsb/data/bis_news.py`、`wsb/data/fed_research.py`、`wsb/data/mops_rt.py`、`wsb/data/tw_bank.py` 皆已逐行檢查完畢——並交叉確認 `wsb/analytics/energy_chain.py` 與 `wsb/data/freshness.py`、`wsb/data/taiwan.py` 的單位與初始化邏輯相符，未發現上述錯誤。）

---

其他今天的大事：
- APEC 深圳峰會 11/19 中午「川習會」登場：川普宣布美中就「30 對 30 協議」同意各自對價值 300 億美元商品削減關稅，稱雙方在確保荷莫茲海峽能源順暢通航與防伊朗擁核武上有強烈共識；稍早川普與普丁會談約 40 分鐘，會後將接續美中俄三方峰會；另川普受訪稱 Blackwell 晶片或須「再等 2 至 3 年」才考慮允許售中，且與黃仁勳有染女子正遭美方調查是否涉中國情報與晶片走私（https://www.cna.com.tw/news/aopl/202611193005.aspx ；https://www.cna.com.tw/news/aopl/202611193003.aspx ；https://www.voachinese.com/a/trump-meets-putin-in-shenzhen-as-trade-disputes-loom-over-talks-with-xi-20261119/8225437.html ）。
- 台股 11/19 收盤重挫 **1,768.02 點（-4.40%）至 38,426.89 點**（史上第 7 大跌點，摜破年線），成交金額 **8,952.81 億元**、20 檔千金股收跌停、櫃買收跌 7.22%；新台幣早盤貶破 33 元見 33.04 元、午盤暫收 32.988 元；證交所表態必要時採穩定措施（https://www.cna.com.tw/news/afe/202611190149.aspx ；https://www.cna.com.tw/news/afe/202611190169.aspx ；https://news.cnyes.com/news/id/6667459 ）。
- Anthropic 自建資料中心牽動台鏈與晶片陣營板塊：至 2045 年算力承諾高達 9,009 億美元並透過博通租賃 3.5 GW TPU 機櫃，台積電 CoWoS 估占 1–2 成而廣達、英業達、鴻海有望承接機櫃組裝轉單；廣達 11/18 公告斥資 1,490.8 萬美元承租田納西廠房 62 個月，日月光今日高雄仁武 2,489 億元新廠動土，海龍風電 2A 轉售綠電予台積電（https://www.cna.com.tw/news/afe/202611190156.aspx ；https://news.cnyes.com/news/id/6666244 ；https://www.cna.com.tw/news/afe/202611190122.aspx ；https://www.cna.com.tw/news/afe/202611190102.aspx ）。
- 全球非美市場與監管風險同步升溫：荷莫茲海峽 3 艘油輪觸及水雷起火失能（https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906 ）；英國 10 月 CPI 升至 3.6%（https://www.mufgresearch.com/macro/european-macro-18-november-2026/ ）；印度 10 月通膨達 6.09% 兩年首破央行上限，考驗單月破紀錄逾 100 億美元外資流入（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ）；美國財政部 FinCEN 發布強化金融機構客戶盡職審查提案，BIS `2026-23529` 遠端算力管制新規今日刊登聯邦公報生效（https://home.treasury.gov/news/press-releases/sb0691 ；https://public-inspection.federalregister.gov/2026-23529.pdf ）。
- 今晚（11/19）20:00–22:30 沃爾瑪（WMT）、阿里巴巴（BABA）、拼多多（PDD）公布財報，且 Anthropic（ANT，定價 83 美元、估值 1.5 兆美元）正式在納斯達克掛牌（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://www.nasdaq.com/press-release/alibaba-group-will-announce-september-quarter-2026-results-november-19-2026-2026-11 ）。

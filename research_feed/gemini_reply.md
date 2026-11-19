台北時間 2026-11-19 15:42

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）、整體 PCE 年增率為 **3.6%**（月增 **0.5%**），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，台北時間 2026-10-29，HTTP 200 確認）。
- 事實：之所以 9 月核心 PCE（3.1%）反過來高於核心 CPI（2.6%），根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 高於核心 CPI 的倒掛現象（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。
- 事實：檢視本站即時網頁《財經日曆》分頁的 `PCE 物價（聯準會最重視的通膨）` 卡片（11/19 15:07 線上版確認仍在），其實已明確寫出「核心 PCE 年增 3.1%」、「前值 0.3%」，顯示 9 月基準值已在站內日曆卡片上，只是沒有串接到 `forecast.json`。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照（無新進展）
- 事實：歐洲央行（ECB）2026 年 11 月《金融穩定評估》Box 3（"The debt financing of AI and its implications for financial stability"）明確列出美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 共識（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，台北時間 2026-11-18，HTTP 200 確認）。
- 事實：ECB Box 3 正文對自由現金流的口徑為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（僅以**資本支出超過營運現金流**作為表層口徑，未把尚未起租的表外租賃算進單季現金流）；同時於圖表 A 與註腳 6 依美國會計準則 **ASC 842** 單獨指出，已簽約但資產尚未投入使用的租賃與算力承諾在起租前不計入資產負債表負債，這類表外承諾合計已逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200 確認）。
- 事實：四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與租賃口徑落差如下：
  - Meta（Q3 2026）：營運現金流 **$32.79B**，資本支出（含融資租賃本金償還）**$34.91B**，自報自由現金流為 **-$2.12B（轉負）**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）。
  - Alphabet（Q3 2026）：營運現金流 **$42.29B**（$42,290M），現金 PP&E 購置（不含融資租賃）**$51.36B**（$51,355M），自報自由現金流為 **-$9.07B（-$9,065M，轉負，含 52 億美元歐盟罰款支付）**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）。
  - Amazon（Q3 2026／TTM）：單季營運現金流 **$42.42B**、單季淨 PP&E 購置 **$75.93B**（隱含單季 **-$33.51B**），公司自報 **TTM 自由現金流 -$42.36B（-$42,357M，轉負）**，該口徑僅扣現金淨 PP&E、未扣額外揭露之新簽融資租賃資產（Q3 單季 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）。
  - Microsoft（Q1 FY27）：營運現金流 **$58.02B**，現金 PP&E 資本支出 **$39.37B**，自報自由現金流為 **+$18.6B（仍為正值，年減 27%）**；若計入新起租之融資租賃，總資本支出達 **$45.2B**，扣除後仍餘約 +$12.8B，印證 ECB 精準寫 `"most"` 而非全部（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（無新進展，附 macro_voice.json 實例）
- 推理：檢視 `claude_notes.md`、`forecast.json` 與 `macro_voice.json`，最常「下太快」的是以下兩種思考捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：例如 `claude_notes.md` 第 14 行在還沒核對 `bea.gov` 或本站日曆卡片前值的情況下，因為「核心 PCE 通常比核心 CPI 低」，就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推 10 月區間；以及 `forecast.json` 第 65–73 行先前曾用單一 `BAMLH0A0HYM2`（3.43%）得出「信用市場還沒出現壓力」（第 3 輪你已修正）。
  2. **把「我的新聞關鍵字沒對上時間」或「昨天數字」直接當作定論**：例如 `forecast.json` 第 3 行寫「黃金、銅、油價同一天一起跌，主因我沒找到時間對得上的消息」，但同一檔案第 150 行自己就寫了「金銀跌到 14 個月低點，聯準會官員偏鷹讓美元走強」，且忽略 11/18 EIA 原油與汽油大幅累庫及雪佛龍除息日；11/19 `14:15` 更新的 `macro_voice.json` 第 6 行寫「新台幣只貶了一點點，三十二點九四」，其實 32.947 是昨天（11/18）的匯率，今天（11/19）盤中早已貶破 33 元關卡至 33.04 元、午盤收 32.988 元。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標（無新進展）
- 事實：中央社 11/19 引述 Anthropic 公開說明書指出，Anthropic 至 2045 年算力合約承諾高達 **9,009 億美元**（2030 年底前到期約 4,520 億美元），其中涵蓋博通 1,612 億美元、Alphabet 1,213 億美元、SpaceX 1,205 億美元、AWS 1,100 億美元與 Azure 449 億美元；雖然前 9 月營收約 330 億美元、自由現金流 56 億美元、10 月底 ARR 達 810 億美元，但正從租用外部雲端轉向透過博通租賃 3.5 GW Google TPU 機櫃自建「Anthropic Direct」資料中心，短期自由現金流恐縮水甚至歸零（https://www.cna.com.tw/news/afe/202611190156.aspx ，台北時間 2026-11-19，HTTP 200 確認）。
- 推理：若今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，傳導先後順序如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：負債比高、高度仰賴大模型算力長約抵押融資，且 Anthropic 轉向自建直接稀釋第三方租賃溢價。隔天（11/20）可驗證指標：`CRWV`、`NBIS` 相對 `QQQ` 的開盤超額跌幅，及新雲端無擔保債二級殖利率走勢。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸**：ANT 募資 813.1 億美元、估值 1.5 兆美元，若破發將壓縮 OpenAI 與晚期 AI 獨角獸 IPO 窗口。隔天可驗證指標：`ARCC`、`BIZD`、`BX`、`APO` 股價與承銷商是否啟動護盤機制（stabilizing bid）之報導。
  3. **最後且分化：晶片與機櫃合作夥伴（NVDA、AVGO、GOOGL、AMZN、台積電等同步私募出資方）**：主要承受公允價值重估回吐（如台積電核准上限 5 億美元參與同步私募），但 Anthropic 轉向自建反而讓博通與 TPU 機櫃組裝廠（英業達、廣達、鴻海）受關注。隔天可驗證指標：`AVGO`／`NVDA` 相對 `^SOX` 強弱與次日選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態（15:42 最新補充：11/19 證交所三大法人賣超 461 億、期貨淨空單擴至 -8,883 口、金管會緊急升級 3.5% 限空令）
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意**，ECB Box 3 佐證多家一線雲端商 FCF 轉負、表外承諾逾 4 兆美元，Anthropic 自建資料中心使 9,009 億美元算力合約現金流壓力浮上檯面（https://www.cna.com.tw/news/afe/202611190156.aspx ），但尚未演變為連鎖違約；美國 9 月 TIC 外資淨流入仍達 2,610 億美元（https://home.treasury.gov/news/press-releases/sb0693/ ）。
  2. **主線 2（輝達治理風波 vs 出口調查）— 部分同意，兩條線已證實交織**：中央社 11/19 引述川普接受《福斯新聞》專訪指出，**與黃仁勳有染的一名女子正受到美國政府調查，調查涉及她是否可能為中國情報機構工作，以及是否可能協助走私晶片**，同時川普稱「再等 2 至 3 年」或允許輝達 Blackwell 晶片賣中國（https://www.cna.com.tw/news/aopl/202611193003.aspx ，HTTP 200 確認）。個人治理風波與國安／晶片出口調查不是二選一，而是**同一人物同時觸發公司治理與國安調查**，建議下一輪整併重估。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，補充 11/19 15:00 後官方法人籌碼與金管會限空令**：今日台股收跌 **1,768.02 點（-4.40%）至 38,426.89 點**（成交 **8,952.81 億元**、20 檔千金股收跌停）；15:00 後證交所公布三大法人合計賣超 **461.03 億元**（外資賣超 **243.12 億元**、投信買超 **15.13 億元**、自營商賣超 **233.03 億元**），期交所公布三大法人臺股期貨合計淨空單由昨日 -7,322 口擴大至 **-8,883 口**（外資 -99,219 口、投信 +91,791 口、自營商 -1,455 口）；金管會更於盤後緊急宣布自 **11/20 起實施限空令升級版**（當日收盤跌幅達 **3.5%** 以上個股，次日禁止平盤下融券及借券放空；每日盤中借券上限由 **3% 降至 1%**）（https://www.cna.com.tw/news/afe/202611190200.aspx ；https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ，HTTP 200 確認）。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意，補充荷莫茲消息查證區分**：House of Saud 11/19 報導清楚區分：英國海事貿易行動辦公室（UKMTO）**已獨立證實** 11/18 早上一艘阿聯 ADNOC 船隻遇襲（11 傷、1 失蹤），但伊朗軍方晚間宣稱「另有 3 艘油輪在海峽東側觸及水雷起火」**尚未公布船名與船籍、缺乏獨立證實**（https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ，HTTP 200 確認）；且深圳川習會川普公開稱美中在「確保能源順暢通過荷莫茲海峽及防止伊朗擁有核武」上有強烈共識（https://www.cna.com.tw/news/aopl/202611193005.aspx ），外加 EIA 庫存大增與強美元，雙向拉扯下我仍維持 **55%**。
  5. **主線 5（「風險升級」劇本 33% vs 40%）— 同意方向一致**，差距 7 個百分點（但日本央行總裁植田和男今日國會最新鷹派談話加上金管會升級限空令，顯示非美市場金融緊縮與波動外溢正在擴大）。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題（保留，補充 15:07 線上版觀察）
- 1. 檢視今天 `15:07` 線上版《財經日曆》的 `PCE 物價（聯準會最重視的通膨）` 卡片，其實**已經顯示核心 PCE 年增 `3.1%`、前值 `0.3%`**；為什麼 `forecast.json` 卻仍寫「9 月核心 PCE 數字：查無」？是預測腳本沒有讀取該表格，還是產出順序有落差？
- 2. 今日（11/19）中央社報導與黃仁勳有染的女子正遭美政府調查是否涉中國情報與晶片走私（https://www.cna.com.tw/news/aopl/202611193003.aspx ），同時深圳「川習會」釋出「30 對 30」降稅與確保荷莫茲通航訊號（https://www.cna.com.tw/news/aopl/202611193005.aspx ），加上下午金管會升級 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）——你下一輪會如何調整「輝達事件定性」以及「油價／風險升級」的機率？
- 3. 截至 `15:07` 線上版更新，`macro_voice.json`（14:15 午班）仍寫「新台幣只貶了一點點，三十二點九四，沒查到外資今天買賣超」；但 32.947 是昨天（11/18）的數字（今天盤中已見 33.04、午盤 32.988），且 15:00 後證交所已公布外資賣超 243.12 億元。語音稿在引用台股收盤與台幣匯率時，為什麼仍會混用前一交易日的匯率？

---

### WIDE-1｜荷莫茲海峽 ADNOC 船隻遇襲獲 UKMTO 證實、伊朗另稱 3 油輪觸水雷；川習會同日宣示保航道順暢（更新可驗證來源與事實區分）
- 事實：House of Saud 於 2026 年 11 月 19 日報導，英國海事貿易行動辦公室（UKMTO）已正式證實一艘阿聯 ADNOC 旗下船隻於 11 月 18 日早上在荷莫茲海峽附近遇襲（**11 名船員受傷、1 人失蹤**）；同日晚間伊朗軍方另宣稱在荷莫茲海峽東側有 **3 艘油輪觸及水雷起火失能**，但報導明言伊朗方面並未公布該 3 艘船隻之船名或船籍，尚待獨立查證（https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ，台北時間 2026-11-19，HTTP 200 確認）。另同日下午川普於深圳川習會致詞稱，美中在確保能源順暢通過荷莫茲海峽與防止伊朗擁有核武上有非常強烈的共識（https://www.cna.com.tw/news/aopl/202611193005.aspx ，HTTP 200 確認）。
- 推理：美股昨晚（11/18）全數聚焦美國 EIA 原油與汽油累庫而使油價下跌，但實質船隻遇襲加上水雷威脅（即便 3 艘觸雷尚待獨立證實）仍會立即推高海運戰爭險費率與成品油裂解價差；美中在深圳口頭宣示保暢通能否壓住伊朗實際佈雷行動，是未來 48 小時油價多空分水嶺。
- 先影響資產：布蘭特原油／柴油裂解價差、油輪與海運戰爭險費率、航空與石化類股。

### WIDE-2｜APEC 深圳「川習會（30 對 30 協議）」與史上首次美中俄三方領袖峰會登場（更新三方峰會來源）
- 事實：11/19 中午美中元首今年第三次「川習會」在深圳麒麟山莊登場，美方由川普率國務卿盧比歐、商務部長盧特尼克、財長貝森特與貿易代表葛里爾出席；川普致詞稱美中已就「**30 對 30 協議（30 for 30 deal）**」同意各自對價值 **300 億美元**商品削減關稅，並希望終結俄烏戰爭（https://www.cna.com.tw/news/aopl/202611193005.aspx ，HTTP 200 確認）。稍早川普與普丁單獨會談約 **40 分鐘**（克宮稱 42 分鐘），下午接續舉行**美中俄首次三方領袖峰會**聚焦核武軍控、烏克蘭與伊朗局勢；惟美國之音（VOA）與中央社引述學者指出，美中貿易休戰仍脆弱，且三方峰會不易出現中俄聯手「二對一」或重大具約束力條約（https://www.cna.com.tw/news/acn/202611190138.aspx ；https://www.cna.com.tw/news/acn/202611190062.aspx ；https://www.voachinese.com/a/trump-meets-putin-in-shenzhen-as-trade-disputes-loom-over-talks-with-xi-20261119/8225437.html ；https://www.hindustantimes.com/world-news/apec-summit-2026-live-updates-donald-trump-vladimir-putin-xi-jinping-meeting-today-19th-nov-trade-policy-ukraine-war-101795049823233.html ，均 HTTP 200 確認）。
- 推理：雙邊削減 300 億美元關稅雖是短期緩和訊號，但同日 BIS 遠端算力新規生效且川普表示 Blackwell 晶片仍須「再等 2 至 3 年」，代表美中經貿正走向「消費／農產品微幅降稅、先進算力與國安管制繼續收緊」的結構分化；若三方會談在核軍控或俄烏／伊朗問題上釋出任何停火框架，將直接改寫歐洲天然氣與原油風險溢價。
- 先影響資產：USD/CNH、中概股（KWEB）、美國農產品期貨、歐洲天然氣與國防股。

### WIDE-3｜日本央行總裁植田和男 11/19 國會重申繼續升息、示警通膨突破 2% 上行風險，同日熊本發生規模 5.7 地震（新）
- 事實：路透社／Channel NewsAsia 於 2026 年 11 月 19 日報導，日本央行（BOJ）總裁植田和男今日在國會答詢時重申央行持續升息的決心，直言金融環境仍屬寬鬆，並公開警告潛在通膨有突破 2% 目標的上行風險（`"It's important to anchor underlying inflation around our 2 per cent target to avoid risk of an inflation overshoot from materialising and hurting the economy"`），強化市場對 **12 月 17–18 日**會議升息至 **1.50%** 的預期（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ，台北時間 2026-11-19，HTTP 200 確認）。另新華社／China Daily Asia 報導，日本熊本縣於當地時間 11/19 清晨 2:22（台北 01:22）發生初步規模 **5.7 地震**，日本氣象廳示警留意餘震、未發布海嘯警報（https://www.chinadailyasia.com/hk/article/642914 ，台北時間 2026-11-19 14:27，HTTP 200 確認）。
- 推理：美股目前幾乎只定價聯準會 12/9 升息，卻容易忽略 **日本央行 12/17–18 緊接著升息至 1.50%** 的「美日同步緊縮」風險；一旦日圓套利資金與日本機構資金回流日債，全球長天期公債殖利率與高本益比科技股將面臨第二波流動性抽水；此外熊本為日本晶圓代工重鎮（台積電 JASM 所在地），雖然此次 M5.7 未傳出重大停工或海嘯，但後續餘震是否干擾設備校準值得緊盯。
- 先影響資產：USD/JPY、日本 10 年期公債（JGB）、全球高槓桿科技股、日股銀行與半導體設備商。

### WIDE-4｜英國 10 月 CPI 升至 3.6%、歐盟秋季經濟預測示警通膨 3.3% 黏著，疊加歐盟「數位公平法」與法國港口罷工（無新進展）
- 事實：MUFG Research 11/18 彙整顯示，英國 10 月整體 CPI 年增率由 3.5% 升至 **3.6%**（能源推動），核心 CPI 維持 **2.8%**、失業率降至 **4.6%**（https://www.mufgresearch.com/macro/european-macro-18-november-2026/ ，HTTP 200 確認）；歐盟執委會秋季預測雖將 2026 年歐元區 GDP 成長上修至 **1.2%**（歐盟 **1.4%**），但估歐盟全年通膨達 **3.3%**（https://www.eunews.it/en/2026/11/17/eurozone-and-eu-growth-to-top-forecasts-in-2026-though-inflation-remains-a-drag/ ，HTTP 200 確認）。另歐盟執委會推出「數位公平法（Digital Fairness Act）」擬禁絕深色模式與不透明動態定價（https://commission.europa.eu/law/law-topic/consumer-protection-law/digital-fairness-act_en ，HTTP 200 確認），且法國出現 24 小時全國港口與碼頭罷工（https://www.hillebrandgori.com/port-updates ，HTTP 200 確認）。
- 推理：英、歐通膨同時回升至 3.3%–3.6%（加上法、英港口摩擦），使歐洲利率維持高檔更久，對歐洲消費與跨國電商／平台合規成本形成壓力。
- 先影響資產：英國公債（Gilts）、EUR/USD、法德 10 年期公債利差、歐洲電商與數位平台股。

### WIDE-5｜印度 10 月通膨 6.09% 破央行上限考驗百億美元外資潮，疊加強烈氣旋「阿克萬（Akvan）」逼近東岸撤離逾 8 萬人（更新氣旋事件）
- 事實：CNBC 11/19 清晨報導，印度 10 月零售通膨（CPI）年增率升至 **6.09%**，兩年來首度突破印度央行（RBI）**6%** 上限，與此同時 11 月外資淨流入印度股市已逾 **100 億美元**創單月紀錄，正面臨成本通膨與 RBI 升息逆風（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ，台北時間 2026-11-19 08:01，HTTP 200 確認）。同日《The Hindu》即時報導，孟加拉灣強烈氣旋風暴 **「阿克萬（Akvan）」** 預計於 **11 月 20 日中午**在印度奧里薩邦（Odisha）Gopalpur 附近登陸，奧里薩邦已緊急撤離逾 **8 萬名**民眾（https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ，台北時間 2026-11-19，HTTP 200 確認）。
- 推理：印度是目前全球資金從東北亞 AI 股撤出後最主要的「非 AI 避風港」；但國內通膨剛破 6% 上限，緊接著又遇強烈氣旋登陸東岸威脅農產、港口與電力運輸，可能進一步推升食物價格並強化 RBI 升息理由，若外資避風港動搖，將加速新興市場資金回流美元現金。
- 先影響資產：印度 Nifty 50／銀行與消費股、印度盧比（USD/INR）、新興市場 ETF（INDA / EEM）。

---

### A｜今天的大動（對照 `/api/gemini_ask` 15:31 即時清單）

### PANW｜同意本站早班對正規盤的判斷；Palo Alto Networks（PANW）11/18 正規盤先漲 +9.90%，盤後 Q1 FY27 財報全面優於預期並宣布 45 億美元併購 Applied Compute 再漲 +9.1%
- 事實：美東 11 月 18 日正規盤 PANW 已先上漲 **+9.90%**（由前收 $309.29 漲至 **$339.92**）；盤後公布 Q1 FY27 財報，營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億美元）、Non-GAAP EPS **1.05 美元**（優於預期 0.97 美元）、次世代資安 ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**（FactSet 共識 141.7 億美元）、調整後 EPS 指引至 **4.26～4.30 美元**（FactSet 共識 4.18 美元），並宣布以 **45 億美元**全股票收購開源權重 AI 模型平台 **Applied Compute**，帶動盤後／盤前再漲 **+9.1%（一度 +11%）**（https://www.prnewswire.com/news-releases/palo-alto-networks-reports-fiscal-first-quarter-2027-financial-results-302944393.html ，HTTP 200 確認；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200 確認；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，HTTP 200 確認；https://www.tradingview.com/news/stocktwits:77181b970094b:0-panw-stock-soars-11-after-hours-on-q1-earnings-beat-4-5b-acquisition-announcement/ ，HTTP 200 確認）。
- 本站漏掉的：即時題目單（15:31）仍標「本站沒有找到對得上的新聞」。另同日盤後 **Everpure（NYSE: P，原 Pure Storage）** Q3 FY27 營收年增 **51%** 至約 **14.6 億美元**（新聞稿約 $1.5B）、調整後 EPS **0.86 美元**並連三季上調全年指引至 **52.0 億～52.1 億美元**（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ，HTTP 200）；KeyBanc 分析師 Eric Heath 亦將 PANW 由 Sector Weight 調升至 **Overweight**、看法調高至 **$380**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200）。

### CRWD｜CrowdStrike（CRWD）11/18 正規盤漲 +7.95% 收 $237.03，盤後／盤前受 PANW 財報驗證 AI 資安需求外溢續漲 +6.0%（無新進展）
- 事實：CRWD 美東 11 月 18 日正規盤由前收 $219.58 大漲 **+7.95%** 至 **$237.03**，盤後／盤前再漲 **+6.0%**，主因同業 PANW 財報驗證企業 AI 資安需求強勁而出現板塊連動（https://www.globalbankingandfinance.com/crowdstrike-holdings-crwd-rises-2026-11-18/ ，HTTP 200 確認；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200）。近期 Cantor Fitzgerald 亦維持 **Overweight** 並調高對 CRWD 的看法至 **$275**（https://www.tikr.com/zh/blog/cantor-fitzgerald-raises-its-crowdstrike-target-to-275-is-it-still-too-low ）。
- 本站漏掉的：即時題目單（15:31）仍標「本站沒有找到對得上的新聞」。經查 CRWD 預計 **12 月 1 日盤後**才公布財報，11/18 盤後至今日並無單獨公司公告（找不到來源），屬同業財報帶動的板塊外溢。

### CVX｜雪佛龍（CVX）受 11/18 除息每股 1.78 美元、EIA 原油與汽油庫存大增壓低油價，以及 50 億美元併購談判影響，未還原跌 4.74%、還原息後跌 3.95%（無新進展）
- 事實：CVX 美東 11 月 18 日正規盤收在 **$205.88**（較 11/17 收盤 $216.13 **未還原跌 4.74%**，扣除當日季股息 **每股 $1.78** 除息調整後為 **-3.95% / 約 -4.0%**），由三件事疊加：（1）11/18 為每股 $1.78 季股息除息日；（2）EIA 公布上週美國原油庫存大增 **340 萬桶**、汽油大增 **520 萬桶**，壓低油價並使能源股集體下挫（XOM、CNQ 同步走弱）；（3）市場消化其接近以 **50 億美元**收購墨西哥灣深水油商 **Beacon Offshore Energy** 的談判消息（https://www.globalbankingandfinance.com/chevron-cvx-falls-2026-11-18/ ，HTTP 200；https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ，HTTP 200；https://www.nationthailand.com/news/world/40073656 ，HTTP 200；https://www.bicmagazine.com/industry/investment-banking/chevron-closes-in-on-5b-beacon-deal/ ，HTTP 200）。
- 本站漏掉的：即時題目單（15:31）仍標「本站沒有找到對得上的新聞」；當日屬除息與 EIA 庫存引發之能源板塊集體修正，非雪佛龍單一基本面突發利空。

### CNQ｜Canadian Natural Resources（CNQ）11/18 正規盤隨油價重挫跌 4.63%（$45.53），盤前 +3.2% 無單獨公告或報告（無新進展，找不到來源）
- 事實：CNQ 美東 11 月 18 日正規盤隨北美能源股重挫收跌 **4.63%**（由 $47.74 跌至 **$45.53**，多倫多跌 4.06% 至 C$65.52），市場亦消化其宣布以 **25.3 億加元**收購 **Advantage Energy** 之支出（https://www.nationthailand.com/news/world/40073656 ，HTTP 200 確認；https://www.newsfilecorp.com/release/324091/Canadian-Natural-Resources-Limited-Enters-into-Agreement-to-Acquire-Advantage-Energy-Ltd ）。
- 事實（盤前 +3.2%）：經查公司公告、交易所與主流媒體，美東 11/18 盤後至今日美東深夜 **沒有任何 CNQ 新聞、財報或分析師調評**（找不到來源）。
- 本站漏掉的：即時題目單（15:31）仍僅標盤前 `+3.2%` 且稱找不到新聞，未呈現前一日正規盤重挫 `-4.63%` 的完整脈絡。

---

### AN｜AN-1：最近 3 小時內（台北 12:42–15:42）無新增美股分析師調評；補上 Summit Insights 調降 NVDA（Buy → Hold）可查證原文
- 事實：檢索最近 3 小時（台北 12:42–15:42／美東 11/18 23:42–11/19 02:42 深夜時段），AI 供應鏈與美國市值前 20 大公司並無新發布的美股券商評等調整（找不到來源）。
- 事實（本週與今日最新可查證重要報告）：
  1. **Summit Insights Group（11/18 新補充）**：將 **NVDA** 評等由 Buy 調降至 **Hold**，理由為黃仁勳離任後的領導過渡不確定性、美國商務部出口新規對東南亞雲端業者的潛在阻力，以及 2027 年客製化 ASIC 競爭壓力（https://www.tikr.com/fr/blog/is-summit-insights-wrong-to-give-up-on-nvidia-wall-street-still-sees-251 ，HTTP 200 確認）。
  2. **摩根士丹利（11/19 亞太高峰會後報告）**：維持 **台積電（2330）** `Overweight`（增持）評等與產業「有吸引力」看法，將估值看法調高至 **3,088 元**，預估 2027 年 2 奈米產能翻倍以上，並預估 2026／2027／2028 年 EPS 分別為 **112.10／148.64／189.81 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，台北時間 2026-11-19，HTTP 200 確認）。
  3. **Piper Sandler**：將 **Medtronic（MDT）** 評等由 Neutral 調升至 **Overweight**，估值看法由 $85 調高至 **$120**（https://www.tradingview.com/news/tradingview:5b080eae6cc49:0-piper-sandler-upgrades-medtronic-to-overweight-from-neutral-raises-price-target-to-120-from-85/ ，HTTP 200 確認）。
  4. **HSBC／華爾街多家投行對 NVDA 調整**：HSBC 分析師 Frank Lee 將 **NVDA** 由 Buy 調降至 **Hold**（看法自 $365 調降至 **$170**），指出在確認永久執行長人選與展現執行力前股價恐持續承壓（https://www.tradingview.com/news/binance_news:d94dcaa1f094b:0-hsbc-downgrades-nvidia-says-stock-may-struggle-until-new-ceo-is-named/ ，HTTP 200 確認）；另 Benzinga 統計黃仁勳離任前後共 10 家機構下調 NVDA（包含 11/11 Baird Outperform→Neutral、11/12 Evercore ISI Outperform→In-Line 看法 $465→$186、11/12 Bernstein Outperform 調降看法 $400→$200 等）（https://www.tradingview.com/news/benzinga:3bce7f47b094b:0-nvidia-gets-10-bank-downgrades-after-huang-exit-what-to-expect-ahead-of-q3-results/ ，HTTP 200 確認）。
  5. **Moody's Ratings（11/18）**：維持 **NVDA** Aa1 債信評等，將展望由 **Positive 調降至 Stable**（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ，HTTP 200）。
  6. **KeyBanc**：分析師 Eric Heath 將 **PANW** 由 Sector Weight 調升至 **Overweight**、看法調高至 **$380**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200）。
  7. **YR Research（11/18）**：將 **AAPL** 由 **Sell 調升至 Hold**（https://www.tradingview.com/news/seekingalpha:d985f509f094b:0-sa-analyst-upgrades-downgrades-nvda-aapl-smci-tsla/ ，HTTP 200）。
  8. **Raymond James**：維持 **SMCI** 偏多評等與 **$65** 看法（對照 Susquehanna 維持 Negative、看法 $18）（https://247wallst.com/investing/2026/11/18/super-micro-computers-40-3-month-downturn-a-great-entry-point-says-this-wall-street-pro-who-predicts-165-returns/ ，HTTP 200）。
  - 另見報導彙整 Rothschild & Co Redburn 調降 AVGO（Buy → Neutral），單篇直連網址於外部抓取回傳 403（單篇直連網址：找不到來源）。

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）刊登聯邦公報生效，新加坡與美展開實務協商（無新進展）
- 事實：美國商務部工業安全局（BIS）暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢至 2027-01-19）。新規增訂 § 744.24 遠端存取終端用途管制，限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則（https://public-inspection.federalregister.gov/2026-23529.pdf ，HTTP 200；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ，HTTP 200；https://www.milbank.com/en/news/bis-issues-new-rule-restricting-remote-access-to-advanced-chips.html ，HTTP 200）。
- 事實：新加坡 MDDI 部長楊莉明已與美國 BIS 副部長 Jeffrey Kessler 會談並同意跟進「受信任用戶」實務安排；馬來西亞亦正尋求釐清規範（https://www.channelnewsasia.com/singapore/singapore-us-semiconductor-mddi-josephine-teo-6560761 ，HTTP 200；https://www.cna.com.tw/news/afe/202611190022.aspx ，HTTP 200）。

### POL-2｜美國財政部 FinCEN 發布強化客戶盡職審查（CDD）新規提案、9 月 TIC 淨流入 2,610 億美元與 OFAC 制裁（無新進展）
- 事實：美國財政部金融犯罪執法網絡（FinCEN）發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，落實第 14406 號行政命令，60 天公眾意見徵詢），明確授權金融機構為防制風險或監管需求向法人客戶實質受益人蒐集額外資訊，並將「同一法人客戶開立新帳戶免重複驗證實質受益人」豁免規則法典化（https://home.treasury.gov/news/press-releases/sb0691 ，HTTP 200 確認）。
- 事實：美國財政部公布 9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ，HTTP 200）；OFAC 宣布「Operation Economic Outcast」制裁真主黨與伊朗聖城軍黃金及現金網路（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 重申美國優先供應鏈韌性（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）；白宮發布亞洲經濟協議事實清單（https://www.whitehouse.gov/fact-sheets/2026/11/fact-sheet-president-donald-j-trump-secures-historic-economic-deals-for-american-workers-and-strengthens-americas-leadership-in-asia/ ）；CMS CRUSH 反詐欺提案（`2026-23461`）11/19 刊登聯邦公報（https://public-inspection.federalregister.gov/2026-23461.pdf ，HTTP 200）。

---

### TW-1｜11/19 三大法人現貨賣超 461.03 億（外資 -243.12 億）、台指期淨空單擴大至 -8,883 口；金管會盤後緊急宣布 11/20 起升級 3.5% 限空令（重大更新）
- 事實（11/19 15:00 後三大法人現貨與期貨官方數據）：台股今日終場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，摜破年線）**，成交值 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190149.aspx ，HTTP 200）。證交所 `BFI82U` 與中央社公布今日三大法人合計賣超 **461.03 億元**，其中 **外資及陸資賣超 243.12 億元**（連 3 賣）、**投信買超 15.13 億元**（`1,512,543,078` 元，新聞簡寫 15.12 億，連 2 買）、**自營商合計賣超 233.03 億元**（自行部位 -18.63 億、避險部位 -214.40 億）（https://www.cna.com.tw/news/afe/202611190200.aspx ，台北時間 2026-11-19，HTTP 200 確認）。期交所（TAIFEX）公布 11/19 臺股期貨三大法人未平倉淨額合計為 **-8,883 口**（較 11/18 的 -7,322 口淨空單擴大 1,561 口），分項為：**外資淨空單 -99,219 口**（較昨日 -99,438 口微減 219 口）、**投信淨多單 +91,791 口**、**自營商淨空單 -1,455 口**。
- 事實（金管會 11/19 盤後重大宣布）：金管會於今日盤後正式發布新聞稿宣布，自 **11 月 20 日**起升級 5 項穩市措施：（1）上市櫃及 TDR 當日收盤跌幅達 **3.5%** 以上者，次一交易日不得以低於前一日收盤價進行融券及借券放空（若次日續跌達 3.5% 則持續限制；現券當沖未回補低於前收者不得改類別為融券／借券放空；造市與避險除外）；（2）每日盤中借券放空委託數量上限由前 30 日均量之 **3% 調降至 1%**；（3）鼓勵金融業進場承接績優股、自營商履行造市義務、上市櫃公司實施庫藏股（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ，台北時間 2026-11-19，HTTP 200 確認；https://www.cna.com.tw/news/afe/202611190182.aspx ，HTTP 200 確認）。
- 事實（違約交割與新台幣）：11/18 上市櫃 9 檔熱門 AI 股達標重大違約交割 **4.269 億元**（整體買賣違約約 9.64 億元），今日 20 檔千金股收跌停（https://www.chinatimes.com/realtimenews/20261119002092-260410 ，HTTP 200）。新台幣 16:00 收盤價截至 **15:42** 尚未產生，最新為 **午盤暫收 32.988 元（貶 4.1 分，早盤曾貶破 33 元見 33.04 元）**（https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200）。

### TW-2｜Anthropic 自建資料中心牽動台鏈 TPU 機櫃轉單（英業達／廣達／鴻海）；廣達納許維爾廠租約；日月光 2,489 億動土與海龍風電售台積電（無新進展）
- 事實：中央社 11/19 引述智璞產業趨勢研究所分析，Anthropic 至 2045 年算力需求換算晶圓約 **40 萬至 70 萬片**（集中於 2026–2028 年），占台積電 CoWoS 年產出 **1 至 2 成**、前段晶圓僅 **3% 至 6%**，對產能滿載的台積電屬客戶結構微調，且台積電董事會核准上限 **5 億美元**參與其同步私募；反觀 Anthropic 直接向博通租賃 **3.5 GW** Google TPU 機櫃自建資料中心，深耕 Google TPU 主機板與機櫃組裝的**英業達、廣達、鴻海**與散熱／電源台廠可望受惠訂單移轉（https://www.cna.com.tw/news/afe/202611190156.aspx ，HTTP 200）。
- 事實：**廣達（2382）**11/18 公告取得田納西州 La Vergne 廠房 **62 個月**租賃使用權資產（合約總金額約 **1,490.8 萬美元**，https://news.cnyes.com/news/id/6666244 ，HTTP 200）；**日月光投控（3711）**旗下福雷電子 11/19 在高雄仁武投資 **新台幣 2,489 億元**動土擴充 AI 高階測試（https://www.cna.com.tw/news/afe/202611190122.aspx ，HTTP 200）；**海龍離岸風電 2A 風場**改簽 CPPA 將綠電轉售予**台積電**（https://www.cna.com.tw/news/afe/202611190102.aspx ，HTTP 200）；**台積電**資深副總張曉強公開深化與輝達協作（https://www.ctee.com.tw/news/20261119700076-439901 ，HTTP 200）；**鴻海（2317）**72.4 億日圓收購 Sony 車載相機模組事業（https://www.ctee.com.tw/news/20261119700316-439901 ，HTTP 200）；**偉詮電（2436）**明年初調漲售價（https://www.cna.com.tw/news/afe/202611190036.aspx ，HTTP 200）；**元太（8069）**11/18 晚間公告資安異常（https://www.cna.com.tw/news/afe/202611180336.aspx ，HTTP 200）。
- 傳聞：外媒轉述《工商時報》稱台積電依客戶資產負債表設 AI 信用額度、超額須預付現金，尚未獲官方證實（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ）。

### TW-3｜蘋果洽談鎖定三星多年期 DRAM 長約（韓廠訂價權上升）；愛德萬新測試系統與台韓出口數據（更新韓廠動態）
- 事實（更新）：《The Korea Herald》今日報導指出，繼與 SK 海力士達成類似安排後，蘋果正進入與**三星電子**洽談多年期 DRAM 供應協議的最後階段，反映 AI 記憶體短缺令韓國記憶體廠握有更強訂價與長約主導權（https://www.koreaherald.com/article/10942672 ，台北時間 2026-11-19，HTTP 200，原文為付費訂閱摘要）。
- 事實（無新進展）：愛德萬 11 月發表 **V93000 EXA Scale QX** 測試系統；韓國 11 月前 10 天出口年增 **111.9%**（半導體年增 **331.2%**），台灣 10 月出口年增 **58.9%** 至 **967.6 億美元**（https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ；https://cyprusshippingnews.com/2026/11/13/south-koreas-exports-surge-toward-1-trillion-as-chip-shipments-more-than-quadruple/ ）。

---

### EARN-WMT｜沃爾瑪（WMT）Q3 FY27 財報（今晚美東 11/19 07:00／台北 20:00，無新進展）
- 事實：美東 **2026-11-19 07:00 財報、08:00 電話會議**（台北 **11/19 20:00／21:00**）；TradingView 彙整市場共識營收約 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（公司上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售成長 3.0%–3.75%）；選擇權隱含波動 **±5.78%～±6.4%**（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ，HTTP 200；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，HTTP 200）。

### EARN-BABA｜阿里巴巴（BABA）Q2 FY27 財報（今晚美東 11/19 盤前／台北 20:00 電話會議，無新進展）
- 事實：美東 **2026-11-19 盤前**公布（電話會議美東 07:00／台北 **20:00**，https://www.nasdaq.com/press-release/alibaba-group-will-announce-september-quarter-2026-results-november-19-2026-2026-11 ，HTTP 200 確認）；Barchart 彙整預期營收約 **404.1 億～404.8 億美元**（年增約 8.9%–16%）、調整後 EPS 約 **1.56～1.71 美元**（本站日曆列 1.56 美元）（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ，HTTP 200）。

### EARN-PDD｜拼多多（PDD）Q3 2026 財報（今晚美東 11/19 盤前／台北 20:00–21:00，無新進展）
- 事實：美東 **2026-11-19 盤前**（電話會議 07:30 ET／台北 20:30）；TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS 約人民幣 **18.72～19.02 元**（約 **2.61～2.77 美元**，本站日曆列 2.61 美元）（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ，HTTP 200）。

### EARN-INTU / ROST / GAP / WSM｜今日（11/19）美東盤前與盤後其餘財報（無新進展）
- 事實：
  - **WSM（盤前／台北 11/19 20:00）**：TradingView 彙整共識營收約 **19.8 億～20.0 億美元**、EPS **2.19 美元**（https://www.tradingview.com/news/tradingview:5796c7c550438:0-wsm-q3-26-earnings-eps-estimate-is-2-19-usd/ ，HTTP 200）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收約 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（公司原財測 2.44–2.48 美元），選擇權隱含波動約 ±8.9%–10.5%（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ，HTTP 200）。
  - **ROST（盤後／台北 11/20 05:00）**：Zacks／TradingView 彙整共識營收約 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ，HTTP 200）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收約 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（公司原財測淨銷售成長 1.5%–2.5%）（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ，HTTP 200）。

### EARN-HPE / ZM / BBY / BURL / DKS / ADI / MDT / DELL / HPQ / ADSK / WDAY / DE｜11/23–11/25 財報（補齊 ZM、ADI、MDT、BBY、HPQ、ADSK 單篇 HTTP 200 共識來源）
- 事實：
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（本站列 1.17，公司財測 1.20–1.30；選擇權波動 ±9.7%，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ，HTTP 200）；**ZM**（Q3 FY27）Zacks 共識營收 **12.8 億美元**、EPS **1.49 美元**（https://www.zacks.com/stock/news/3030700/zoom-communications-zm-falls-more-steeply-than-broader-market-what-investors-need-to-know ，HTTP 200 確認）。
  - **11/24 盤前（台北 11/24 21:00）**：**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**（https://www.tradingview.com/news/tradingview:6917007d5e261:0-burl-q3-26-earnings-revenue-estimate-is-2-97b-usd/ ，HTTP 200）；**DKS** 共識營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ，HTTP 200）；**ADI**（Q4 FY26）FactSet 共識營收 **43.2 億美元**、EPS **3.88 美元**（本站隱含波動 ±8.09%，https://www.tradingview.com/news/tradingview:4441db86105da:0-adi-q4-26-earnings-revenue-estimate-is-4-32b-usd/ ，HTTP 200 確認）；**MDT**（Q2 FY27）FactSet 共識營收 **94.8 億美元**、EPS **1.33 美元**（https://es.tradingview.com/news/tradingview:dcc2d0d8b8c99:0-mdt-q2-26-earnings-revenue-estimate-is-9-48b-usd/ ，HTTP 200 確認）；**BBY**（Q3 FY27）Zacks 共識營收 **98.8 億美元**、EPS **1.48 美元**（https://www.zacks.com/stock/news/3031155/best-buy-bby-reports-next-week-wall-street-expects-earnings-growth ，HTTP 200 確認）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億～492.5 億美元**（公司財測約 490 億）、調整後 EPS **6.41–6.60 美元**（本站列 6.41，隱含波動 ±14.85%，https://www.tradingview.com/news/tradingview:e525c4bdcb809:0-dell-q3-26-earnings-revenue-estimate-is-49-25b-usd/ ，HTTP 200）；**WDAY** 共識營收 **26.9 億美元**、EPS **2.75 美元**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ，HTTP 200）；**HPQ**（Q4 FY26）FactSet 共識營收 **154.3 億美元**、EPS **0.75 美元**（https://in.tradingview.com/news/tradingview:2627939d5b773:0-hpq-q4-26-earnings-revenue-estimate-is-15-43b-usd/ ，HTTP 200 確認）；**ADSK**（Q3 FY27）MarketBeat 彙整共識營收 **21.3 億美元**、EPS **3.07 美元**（公司自身財測 EPS 3.04–3.09 美元，https://www.marketbeat.com/instant-alerts/upcoming-autodesk-adsk-set-to-announce-quarterly-earnings-on-tuesday-2026-11-17/ ，HTTP 200 確認）。
  - **11/25 盤前（台北 11/25 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（本站隱含波動 ±7.23%，https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ，HTTP 200）。

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ，HTTP 200）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（強烈偏升息，無新進展）
- 事實：Waller 於 11/18 受訪指出聯準會可能需要「shock people」壓抑 3% 通膨預期固著，12/8–9 會議應考慮一次升息 50 基點（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ，HTTP 200）。

### FED-3｜聯準會理事 Michael S. Barr（偏升息）、紐約聯準銀行總裁 John Williams（反對一次升息 2 碼）；今晚 Goolsbee 問答與理事會閉門貼現率會議（無新進展）
- 事實：Barr 11/18 在紐約聯準銀行演說指出通膨仍過高、若經濟按預期演進適合進一步升息（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ，HTTP 200）；Williams 舞台對談明確反對 12 月一次升息 0.50%（`"I don't see a need for dramatic action right now"`，偏漸進升息，https://www.chosun.com/english/market-money-en/20261119/3ZAB4T3MGVF4HLNUXPSHRHLNCI/ ，HTTP 200）。
- 事實（今日稍後行程）：芝加哥聯準銀行總裁 Austan Goolsbee 預計 **美東 2026-11-19 12:30（台北 11/20 01:30）** 於印第安納經濟俱樂部問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ，HTTP 200）；聯準會理事會於 **美東 2026-11-19 15:00（台北 11/20 04:00）** 閉門審議貼現率（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ，HTTP 200）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼約 90%–95%、升息 2 碼約 5%–10%（無新進展）
- 事實：聯邦基金期貨幾乎完全定價 12/9 升息 1 碼（約 90%–95%），升息 2 碼約 5%–10%，暫停升息已完全被定價排除（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ，HTTP 200）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，HTTP 200 確認）。
- 事實：核心 PCE（3.1%）高於核心 CPI（2.6%）之結構主因，係 2026 年住房／房租通膨降溫拉低權重較大的 CPI，而醫療服務、金融與軟體科技服務權重在 PCE 籃子較高且價格較黏著（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。

### TASK-B2｜11/19 台股收跌 1,768.02 點收 38,426.89 點、三大法人現貨賣超 461.03 億（外資 -243.12 億）、台指期合計淨空單 -8,883 口；新台幣收盤價待 16:00 產生（重大更新）
- 事實（11/19 收盤與三大法人現貨）：集中市場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，破年線）**，成交金額 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190149.aspx ，HTTP 200）。15:00 後證交所 `BFI82U` 與中央社公布：三大法人合計賣超 **461.03 億元**，其中 **外資及陸資賣超 243.12 億元**、**投信買超 15.13 億元**、**自營商合計賣超 233.03 億元**（自行 -18.63 億、避險 -214.40 億）（https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200 確認）。
- 事實（11/19 期交所三大法人台指期未平倉）：期交所 `futContractsDate`（2026/11/19）公布 **臺股期貨三大法人合計淨空單為 -8,883 口**（外資淨空單 **-99,219 口**、投信淨多單 **+91,791 口**、自營商淨空單 **-1,455 口**）。
- 事實（新台幣與政策）：截至台北時間 **15:42** 台北匯市尚未收盤（16:00 收盤），最新為 **午盤暫收 32.988 元（貶 4.1 分，早盤曾貶破 33 元見 33.04 元）**（https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200）。另金管會盤後宣布自 **11/20 起升級限空令**（當日跌 ≥3.5% 個股次日禁平盤下放空、盤中借券上限降至 1%）（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ，HTTP 200）。

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；保留掛牌前夕關聯股收盤表現（無新進展）
- 事實：Anthropic（代號 **ANT**）已定價 **每股 83.00 美元**（發行 9.8 億股、IPO 募資 **813.1 億美元**、完全稀釋估值約 **1.5 兆美元**），將於 **美東 2026-11-19 09:30（台北 11/19 22:30）** 正式掛牌；截至台北時間 15:42 美股尚未開盤，首日開盤價、收盤價與成交量將於明早 05:00 收盤後產生（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，HTTP 200；https://w.media/anthropic-ipo-priced-at-us-83-per-share-valuation-increases-to-us-1-5-trillion/ ，HTTP 200）。
- 事實：掛牌前夕美東 11/18 收盤，**CoreWeave（CRWV）跌 4.13%、IREN 跌 3.61%、Nebius（NBIS）小漲 0.87%、Oracle（ORCL）大致持平**；同日 **NVDA 收跌約 2.9%**，**AVGO、AMD 上漲約 4%–5%**（https://247wallst.com/investing/2026/11/18/coreweave-falls-5-despite-nvidia-sticking-to-its-financing-commitments-nebius-dips-oracle-holds-steady/ ，HTTP 200）。

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字（無新進展）
- 事實：ECB 11/18《金融穩定評估》Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（基於 LSEG 10/26 共識），指多數美國超大規模雲端業者 2026 年自由現金流因 AI 資本支出大於營運現金流而轉負（表層 FCF 口徑未納入未起租的表外租賃；表外承諾逾 4 兆美元係於圖表 A 與註腳 6 依 ASC 842 單獨揭露）（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200）。
- 事實：四巨頭截至 2026-09-30 最新一季自報實際數字如下：Meta（Q3 2026）OCF $32.79B − CapEx（含融資租賃本金）$34.91B = **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）；Alphabet（Q3 2026）OCF $42.29B − 現金 PP&E $51.36B = **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）；Amazon（Q3 2026／TTM）Q3 單季 OCF $42.42B、淨現金 PP&E $75.93B（單季隱含 -$33.51B）、自報 **TTM FCF -$42.36B**（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）；Microsoft（Q1 FY27）OCF $58.02B − 現金 PP&E $39.37B = **+$18.6B（仍為正；計入新起租融資租賃總資本支出 $45.2B 後仍約 +$12.8B）**（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### TASK-B5｜WMT、BABA、PDD 今晚 20:00–21:00 才公布 11/19 財報；附上最新共識（含來源名稱）、上季指引與關稅／消費原話（無新進展）
- 事實：三家均為 **美東 11/19 盤前（台北時間今晚 11/19 20:00–21:00）** 公布，截至台北 15:42 尚未發布實際財報。
- 事實（沃爾瑪 WMT，Q3 FY27）：TradingView 彙整市場共識營收 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（公司上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）；執行長 John Furner 對關稅退稅與消費者壓力的原話為 `"Customers are feeling some pressure, so we're proud of our investments... We'll do everything we can to keep prices as low as we can for customers throughout the rest of the year."`（https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ；https://www.businessinsider.com/walmart-using-tariff-refund-price-cuts-customer-experience-sales-2026-8 ）。
- 事實（阿里巴巴 BABA，Q2 FY27）：Barchart 彙整共識營收約 **404.1 億～404.8 億美元**（年增約 8.9%–16%）、調整後 EPS **1.56～1.71 美元**，市場聚焦阿里雲 AI 資本支出與中國消費補貼戰（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ）。
- 事實（拼多多 PDD，Q3 2026）：TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS **2.61～2.77 美元**，市場聚焦跨境關稅與小額免稅新規對 Temu 利潤率的影響（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ）。

---

### CALL｜法說會重點

### CALL-PANW｜Palo Alto Networks（PANW）Q1 FY27 法說會：NGS ARR 年增 66%、斥資 45 億美元併購 Applied Compute 搶進企業混合 AI 安全（更新官方新聞稿驗證原話）
- 事實：PANW 執行長 Nikesh Arora 與財務長 Dipak Golechha 於美東 11/18 盤後公布 Q1 FY27 財報並召開電話會議，指出 AI 正重塑威脅版圖、企業須加速從分散工具走向安全 AI 採納，NGS ARR 年增 **66%** 至 **97.3 億美元**，同時宣布以 **45 億美元**全股票併購 Applied Compute（https://www.prnewswire.com/news-releases/palo-alto-networks-reports-fiscal-first-quarter-2027-financial-results-302944393.html ，HTTP 200 確認；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，HTTP 200 確認）。
- 原話（CEO Nikesh Arora）：`"As AI reshapes the threat landscape, we must continually evolve to protect our customers and enable them to adopt AI securely. To that end, we are pleased to announce our intent to acquire Applied Compute, which will allow us to deliver secure open weight models to our customers and accelerate the adoption of enterprise AI."`

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

### NEXT-1｜事件：金管會 11/20 升級 3.5% 限空令＋自營商單日大砍 233 億避險賣壓＋Anthropic 轉向自建 TPU 資料中心（更新政策傳導）
- 推理：
  - 最先受影響的資產：今日 20 檔收跌停的台股千金股與高融資 AI 硬體股、台指期／台灣 50 反 1 避險工具、以及明日平盤下受限的跌深個股流動性。
  - 傳導路徑：今日三大法人賣超中，**自營商合計賣超 233.03 億（避險部位 -214.40 億）幾乎與外資（-243.12 億）相當**，顯示權證與結構型避險賣壓在跌破年線時觸發連鎖助跌；金管會宣布 11/20 起跌 ≥3.5% 個股禁平盤下融券與借券放空、盤中借券上限降至 1%（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ），短期雖鎖住個股現貨空方，但因為**自營商造市／避險與期貨不在限制內**，法人避險需求會集中擠向**台指期（三大法人淨空單已擴至 -8,883 口）**與少數權值股。同時 Anthropic 自建 3.5 GW Google TPU 機櫃使訂單向 TPU 組裝台廠移轉（https://www.cna.com.tw/news/afe/202611190156.aspx ）：
    - 美股：**AVGO、GOOGL、CRWV、NBIS、EQIX**。
    - 台股：**廣達 (2382)、英業達 (2356)、鴻海 (2317)、台積電 (2330)、日月光投控 (3711)**。
  - 大家還沒注意到的間接受害者：**專做高價 AI 股認購／認售權證的券商自營避險部門，以及跌深股的市場流動性**——現貨借券與平盤下放空受限後，做市商只能改以期貨或相關替代品進行動態避險，會擴大期現貨逆價差與無量鎖跌停／跳空波動；此外台灣中小型券商還得面對 11/18 九檔 AI 股違約交割後的呆帳提存壓力（https://www.storm.mg/article/11182992 ）。

### NEXT-2｜事件：APEC 深圳「30 對 30 協議」＋美中俄三方峰會＋川普「Blackwell 等 2 至 3 年＆黃仁勳關聯女子遭調查」vs 荷莫茲船隻遇襲（無新進展）
- 推理：
  - 最先受影響的資產：離岸人民幣（USD/CNH）、布蘭特原油期貨與海運戰爭險費率、以及全球半導體設備／合規供應鏈股價。
  - 傳導路徑：深圳「川習會」一邊釋出 300 億美元對等降稅與確保荷莫茲通航的緩和訊號，另一邊川普同時點出 Blackwell 短期不放行且美國政府正在調查與黃仁勳有染女子是否涉及中國情報與晶片走私（https://www.cna.com.tw/news/aopl/202611193005.aspx ；https://www.cna.com.tw/news/aopl/202611193003.aspx ），代表貿易降稅不會換來先進算力鬆綁；而 ADNOC 船隻遇襲獲 UKMTO 證實、伊朗又稱 3 艘油輪觸雷，考驗中東航道保險成本（https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ）：
    - 美股：**NVDA、AMD、AVGO、FRO（Frontline）、STNG**。
    - 台股：**台積電 (2330)、聯發科 (2454)、長榮 (2603)、陽明 (2609)、台塑化 (6505)**。
  - 大家還沒注意到的間接受害者：**高度仰賴中國或東南亞中轉客戶、但缺乏「可信賴用戶」合規追蹤系統的二線 AI 伺服器與網通模組廠**——一旦美國調查延燒至實際走私節點，海關與出口稽核周期拉長將直接卡住營運資金週轉。

### NEXT-3｜事件：BOJ 總裁植田和男 11/19 鷹派談話（日圓套利風險）＋英歐通膨黏著（3.3%–3.6%）＋印度通膨 6.09% 遇強氣旋 Akvan 登陸（重大更新）
- 推理：
  - 最先受影響的資產：USD/JPY、日本 10 年期公債、印度盧比（USD/INR）與印度銀行消費股、英國 Gilts 與歐元區長債利差。
  - 傳導路徑：植田和男今日在國會重申升息決心並示警通膨恐突破 2% 上行風險（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ），疊加英國 CPI 3.6%、歐盟秋季預測 3.3% 與印度 CPI 6.09% 遇上強烈氣旋「阿克萬」逼近奧里薩邦（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ；https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ），全球央行「同步轉鷹」已從聯準會外溢到日本、英國、歐元區與原本充當資金避風港的印度：
    - 美股：**EWJ、DXJ、INDA、EWU、FDX**。
    - 台股：**華城 (1519)、中興電 (1513)、巨大 (9921)、豐泰 (9910)、中信金 (2891)**（受日圓套利資金流、歐洲／印度消費與金融外幣債券波動影響）。
  - 大家還沒注意到的間接受益者：**美元貨幣市場基金與短天期美債（SGOV / BIL）**——當原本充當避風港的印度（通膨破表＋天災）、日本（央行準備升 1.50%＋熊本地震）也同時出現緊縮與供給衝擊時，跨國資金最終只能回到無匯兌與長債利率風險的美元短端現金。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 已由 60% 降至 45%）」
- 最強反方證據：BEA 官方新聞稿已證實 9 月核心 PCE 年增確為 **3.1%**（`https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026`），The Conference Board 預估 10 月將升至 **3.3%**（`https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026`），且本站《財經日曆》卡片亦已載明 9 月為 `3.1%` 並自估 10 月為 `3.2%`。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法發布年增率，這題將成為「無法判定」；但只要有公布年增率，低於 3.0% 的空間極小。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：我維持落在 2.4%–3.0% 僅約 **30%**（比你修正後的 45% 低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露多數一線雲端商 FCF 轉負且表外承諾逾 4 兆美元，中東 UKMTO 已證實 ADNOC 船隻遇襲且伊朗稱另有 3 艘油輪觸雷（`https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/`），且台股收跌 1,768 點至 **38,426.89 點**（20 檔千金股跌停）、迫使金管會盤後緊急宣布 11/20 起升級 3.5% 限空令（`https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News`），疊加 BOJ 植田今日在國會偏鷹談話。
- 另一種同樣說得通的解釋：就算 Williams 壓低 12 月升息 2 碼機率、美國垃圾債指數因能源權重撐盤未破 4%，「投資級科技債利差走寬＋美日央行同步緊縮＋亞股千點斷頭與政府限空」就足以構成實質的「風險升級」。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：我維持「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你的 80% 低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：11/18 美國 EIA 原油庫存暴增 340 萬桶、汽油暴增 520 萬桶後，WTI 貼近 80 美元下緣，強美元亦壓抑商品；中東方面雖有 ADNOC 遇襲與伊朗觸雷宣稱（`https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/`），但深圳川習會同時釋出「美中確保荷莫茲能源通暢共識」（`https://www.cna.com.tw/news/aopl/202611193005.aspx`），使油價雙尾對撞更劇烈。
- 另一種同樣說得通的解釋：高庫存與高利率拉低基準需求（容易跌破 80 美元），而實質水雷與封鎖升級則可能瞬間衝破 100 美元——也就是油價**在 80–100 美元區間外的機率（雙尾）高於區間內**，並非單純看跌。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **未來 72 小時荷莫茲海峽通航／掃雷動態**。
- 機率估計：我維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」（無新進展）
- 最強反方證據：中央社 11/19 引述《福斯新聞》報導川普親口指出，**與黃仁勳有染的一名女子正遭美國政府調查是否為中國情報機構工作、以及是否協助走私晶片**（`https://www.cna.com.tw/news/aopl/202611193003.aspx`）；同日輝達董事長瓊斯對員工重申「黃仁勳個人行為及缺乏坦誠」是董事會接受辭呈且永不回鍋的原因（`https://www.cna.com.tw/news/aopl/202611190029.aspx`）。
- 另一種同樣說得通的解釋：最初的確是「個人行為／缺乏坦誠」引發董事會 11/11 立即切割，但因牽涉對象本身被美方列為中國情報與晶片走私調查標的，**兩件事並非互斥，而是同一人物同時觸發公司治理與國安出口調查**；且台積電副總張曉強公開為輝達新團隊「站台」、輝達採購承諾增至 3,900 億美元，顯示公司本身目前尚未被列為制裁對象。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節，11 月下旬～12 月初）**與 **美國政府對該涉案女子／走私網絡之起訴或調查公告**。
- 機率估計：維持「單純私人治理、完全無涉中國晶片調查」**25%–30%**，「個人行為與中國晶片／情報調查兩線交織」**70%–75%**（建議 `dots_read.json` 把兩種說法從對立改成因果交織）。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（無新進展）
- 事實：ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**（已超過帳上負債），且投資級科技長債利差已相對於同評級企業債走寬（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q `Commitments and Contingencies / Uncommenced Leases` 追蹤，及 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜缺少「非公開交易 BDC 限額贖回（Gating）、非銀金融槓桿（NBFI）與主權債財政－金融連動」監測（無新進展）
- 事實：金融穩定委員會（FSB）秘書長 John Schindler 在 RiskLive Asia 2026 演說與聯準會 FEDS Notes（2026-10-14）皆重點示警非銀行金融仲介（NBFI）、私募信貸不透明與避險基金槓桿（https://www.fsb.org/2026/10/innovation-and-resilience-managing-the-risks-of-a-changing-financial-system/ ，HTTP 200）。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜缺少「高集中度雲端／金融基建中斷與 SEC Item 1.05 資安事件」警報（無新進展）
- 推理：監測 SEC 8-K Item 1.05 是否涉及高集中度第三方基建（AWS、Azure、GCP、Cloudflare、DTCC），可比股價更早捕捉系統性中斷。免費資料源：CISA KEV JSON（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）＋ SEC EDGAR。

### BLIND-4｜「台股籌碼風向計」雖已顯示外資／投信／自營明細，但未自動加總「三大法人台指期合計淨口數」、15:06 更新仍停在 11/18 數據，且缺「違約交割金額」與「限空令燈號」（對照 15:06 線上版確認）
- 事實：檢視 11/19 15:06 更新的線上「台股籌碼風向計與斷頭警戒」，頁面已列 `外資台指期未平倉淨額 -99,438 口、投信 +93,573、自營 -1,457`（屬 11/18 舊資料），但並未算出並突出 **「三大法人合計淨空單（11/18 -7,322 口 → 11/19 擴大至 -8,883 口）」**，亦未呈現 15:00 後已發布的 11/19 現貨與期貨數據、證交所／櫃買每日違約交割金額統計（11/18 爆 9 檔達標 4.269 億元），以及今日盤後金管會升級 **3.5% 限空令** 狀態（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。免費資料源：期交所「三大法人區分各期貨契約交易資訊」、證交所 `BFI82U` 與「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」（無新進展）
- 推理：建議在「IPO 觀察」補上大型 IPO 納入 S&P 500、Nasdaq-100 指數時程與被動 ETF 權重排擠效應說明。

---

### SITE｜挑本站的錯（對照 15:07／15:14／15:31 線上版確認）

### SITE-1｜`forecast.json` 寫「9 月核心 PCE 數字：查無」，但本站《財經日曆》PCE 卡片其實已顯示「核心 PCE 年增 3.1%」（15:07 線上版確認仍存在）
- 本站寫了什麼：`research_feed/forecast.json` 第 130 行仍寫著 `9 月核心 PCE 數字：查無。`。
- 正確應該是什麼：本站線上《財經日曆》分頁之 `PCE 物價（聯準會最重視的通膨）` 卡片（11/19 15:07 版）已明確顯示 `核心 PCE 年增 3.1%` 與 `前值 0.3%`，完全符合 BEA 官網新聞稿（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）。請將日曆卡片的前值資料管線串接至預測腳本。

### SITE-2｜11/19 `10:33 緊急加班` 語音稿截至 15:07 仍誤把「今天（11/19）台股盤中跌幅」講成「台股昨天收盤附近少了 3.4%」（確認仍存在）
- 本站寫了什麼：線上總覽 `🚨 緊急加班（2026-11-19 10:33 台北）` 語音文字稿仍寫著：`「台股昨天收盤附近比前一天少了三點四個百分點」` 且寫開盤前能源股跳空原因「我目前沒有找到」。
- 正確應該是什麼：台股「昨天（11/18）」收盤其實是**上漲 +102.80 點（+0.26%）收在 40,194.91 點**（https://www.cna.com.tw/news/afe/202611180304.aspx ）；`-3.4%`（今日終場擴大為 `-4.40%`、收 38,426.89 點）是**今天（11/19）**的盤中跌幅，且 11/18 恰為雪佛龍（CVX）每股 1.78 美元季息除息日（https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ）。

### SITE-3｜`macro_voice.json`（`11-19 14:15 午班`，15:07 線上版仍在）將 11/18 新台幣「32.94」當成今天匯率，且尚未反映 15:00 已公布之外資賣超（更新）
- 本站寫了什麼：`research_feed/macro_voice.json` 第 6 行與線上版《每日總經情勢（最後更新 11-19 14:15）》寫道：`「新台幣只貶了一點點，三十二點九四，我沒查到外資今天買賣超的數字，只能說匯率沒有失控。」`
- 正確應該是什麼：**32.947 元**是 **11/18** 的收盤價；今日（11/19）台北匯市以 32.96 元開盤後，**盤中已貶破 33 元整數關卡至 33.04 元**、**午盤暫收 32.988 元（貶 4.1 分）**（https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200）；此外證交所已於 15:00 後公布今日外資賣超 **243.12 億元**、三大法人合計賣超 **461.03 億元**（https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200）。

### SITE-4｜本站即時題目單 `api/gemini_ask`（15:31 版）仍僅標示 `CNQ +3.2%（盤前）`，未附正規盤收跌 -4.63%（無新進展）
- 本站寫了什麼：本站即時 API `api/gemini_ask`（台北 15:31）仍寫 `### CNQ｜CNQ（Canadian Natural Resources）今天 +3.2%（盤前）`，未呈現前日正規盤隨油價重挫 `-4.63%` 的完整脈絡。
- 正確應該是什麼：應同時標示美東 11/18 正規盤收跌 **-4.63%**（因北美能源股受 EIA 庫存大增與油價走弱拖累，https://www.nationthailand.com/news/world/40073656 ，HTTP 200）。

### SITE-5｜本站 `upcoming.json`（15:14 版）之 WMT 公布時間與 HPE 共識 EPS 略低於市場實際公告與最新共識（確認仍存在）
- 本站寫了什麼：本站 `upcoming.json`（`asof: 2026-11-19 15:14`）將 `WMT` 時間列為 `2026-11-19T08:00`（台北 21:00），並將 `HPE` `eps_f` 列為 `1.17`。
- 正確應該是什麼：沃爾瑪官方公告 Q3 FY27 財報新聞稿於 **美東 07:00（台北 20:00）發布**、08:00（台北 21:00）才為電話會議（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ，HTTP 200）；而 `HPE` 目前市場共識調整後 EPS 為 **1.27–1.29 美元**（公司自身財測 1.20–1.30 美元，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ，HTTP 200）。

### SITE-6｜《未來 14 天事件》（15:07 版）仍未標明今日美債標售為「10 年期 TIPS」（確認仍存在）
- 本站寫了什麼：`新聞日曆`《未來 14 天事件》（最後更新 11-19 15:07）仍列 `11-19 美債 10 年期標售（增額） $19B`。
- 正確應該是什麼：今日 $19B 增額標售為 **10 年期 TIPS（抗通膨公債）**（可於美國財政部標售時程核對，https://www.treasurydirect.gov/auctions/announcements-data-results/ ），建議加註「TIPS」以免與名目 10 年債混淆。

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆，對照 15:07／15:14 線上版核對（無新進展）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳峰會（川習會＋美中俄三方峰會）；美東盤前（台北 20:00–21:00）**WMT、BABA、PDD、WSM** 財報；台北約 21:00（南非 15:00）**南非央行（SARB）利率決策**（https://www.sabcnews.com/sabcnews/analysts-expect-mpc-to-keep-interest-rates-unchanged/ ）；美東 09:30（台北 22:30）**Anthropic (ANT)、MapLight (MPLT)** 掛牌；美東 12:30（台北 11/20 01:30）芝加哥聯準銀行總裁 Goolsbee 問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；美東 13:00（台北 11/20 02:00）**美債 10 年期 TIPS 增額標售 $19B**；美東 15:00（台北 11/20 04:00）聯準會理事會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP** 財報（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  2. **11/20（五）**：**台股金管會 3.5% 有條件限空令與盤中借券上限 1% 正式上路**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；**台灣經濟部 10 月外銷訂單**（台北 16:00，預估 1,125–1,159 億美元，https://money.udn.com/money/story/10869/9879179 ）；**美股月選擇權到期（OPEX）**；**密大消費者信心指數終值**（美東 10:00／台北 23:00）；**SanDisk (SNDK) 1 拆 8 分割**。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM** 財報。
  5. **11/24（二）**：美東盤前（台北 21:00）**ADI、MDT、BBY、BURL、DKS**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY**。
  6. **11/25（三）**：美東盤前（台北 21:00）**DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與 10 月耐久財訂單；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**；台北 11/26 **宏于電機（台股）掛牌**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/28（六）**：**台灣 2026 九合一地方選舉投票日**。
  10. **11/29（日）**：**OPEC+ 聯合部長級監督委員會（JMMC）會議**。
  11. **11/30（一）**：**MSCI 季度調整台股收盤生效（台北 13:30）與月底資產再平衡**。
  12. **12/01（二）**：美東 10:00（台北 23:00）**ISM 製造業 PMI 與 10 月 JOLTS 職位空缺**；**CRWD、NTAP** 盤後財報（兩家官網公告頁於外部抓取分別回傳 429/403，單篇直連網址：找不到可直連網址）；**韓國 11 月出口初值**。
  13. **12/02（三）**：美東盤後（台北 12/03 05:00）**Zscaler（ZS）** Q1 FY27 財報（https://www.tradingview.com/news/tradingview:c28752bb00e6f:0-zscaler-hosts-2026-investor-day-reaffirms-q1-and-fiscal-2027-guidance/ ，HTTP 200）。
  14. **12/03（四）**：美國參議院資料中心聽證。
- 對照本站 11/19 15:07／15:14 線上版核對：
  - **正確部分**：`未來 14 天事件`（15:07）與 `upcoming.json`（15:14）已正確列出 WMT/BABA/PDD、ANT/MPLT、HPE、ADI、MDT、DELL、HPQ、DE、11/19 美債 10Y 增額 $19B、H.4.1、11/20 OPEX、11/25 GDP 與 PCE、11/30 月底再平衡、12/01 JOLTS；`休市與提早收盤` 亦正確列出 11/26 休市與 11/27 半天交易。
  - **漏掉部分**：`upcoming.json`（15:14）仍漏掉今晚盤後的 **INTU、ROST、GAP**、11/23 **ZM**、11/24 **BBY、BURL、DKS、ADSK、WDAY**；`未來 14 天事件`（15:07）仍漏掉 **11/19 南非央行、11/20 台灣 10 月外銷訂單、11/21 韓國 20 日出口、11/25 聯準會褐皮書、11/26 韓國央行、11/28 台灣九合一選舉、11/29 OPEC+ JMMC 會議**，且未併註 **11/26–27 感恩節休市與半天交易**。

---

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets）— 掛牌倒數，討論內部人首日可售股數與估值是否讓散戶接盤（更新 11/19 討論串）
- 討論內容與情緒：r/wallstreetbets 今日（11/19）熱門討論串聚焦 ANT 今晚掛牌定價 83 美元、估值 1.5 兆美元與首日內部人解禁流動性（部分網友討論高達 3.16 億股內部人額度，另一派認為機構超額認購 10 倍仍會強勢開高），多空情緒劇烈拉扯（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ，HTTP 200 確認；https://www.reddit.com/r/wallstreetbets/comments/1xtuclv/nasdaq_confirms_anthropics_shares_will_begin/ ，HTTP 200）。

### SENT-2｜NVDA 與本週財報週（r/wallstreetbets）— 財報大好卻走弱加上接班風波，週財報串熱議選擇權對賭（更新 11/19 討論串）
- 討論內容與情緒：r/wallstreetbets 今日討論串與本週財報總串持續嘲諷 NVDA「營收翻倍仍收跌」的疲軟走勢與接班人風波，同時散戶將短線高槓桿選擇權（BanBets）轉向今晚 PANW、WMT 與 ANT 掛牌（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ，HTTP 200；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ，HTTP 200）。

### SENT-3｜PANW／科技股財報（r/stocks）— 肯定資安與 AI 儲存動能但對軟體股估值審慎（無新進展）
- 討論內容與情緒：r/stocks 討論串肯定 PANW 平台化與 NGS ARR 成長，但整體對升息與 AI 高資本支出下的軟體股估值仍偏審慎（熱度自 11/18 升溫；情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-4｜UNH／管理式醫療（r/stocks）— CMS CRUSH 規則衝擊下偏悲觀觀望（無新進展）
- 討論內容與情緒：UNH 等醫療保險股受 CMS CRUSH 反詐欺規則影響連日承壓，散戶偏悲觀（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-5｜台股 11/19 跌 1,768 點破年線與盤後「限空令 2.0」（PTT 股板）— 盤中閒聊湧現恐慌與斷頭哀號，盤後熱議 3.5% 限空令效果（更新）
- 討論內容與情緒：今日台股收盤重挫 1,768.02 點、20 檔千金股收跌停、三大法人賣超 461 億且金管會盤後升級 3.5% 限空令；PTT 股板《2026/11/19 盤中閒聊》大量留言對千金股跌停與違約交割感到恐慌，盤後多空則激烈爭論 3.5% 限空令能否在明日止血或反而抽乾流動性；板內亦同步熱議大摩對台積電 3,088 元看法與輝達提前加薪留才（情緒，非事實；https://www.pttweb.cc/bbs/Stock/M.1795048218.A.865 ，HTTP 200；https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，HTTP 200；https://www.pttweb.cc/bbs/Stock/M.1795058772.A.5C2 ，HTTP 200）。

---

### CODE-1｜wsb/analytics/bottom.py：第 119–120 行與第 144–146 行使用 `cr.get("cnn_fng")` 即時值時，日期 `fg_d` 仍固定取舊檔案 `fg_s.index[-1]`，恐誤判過期或顯示空日期
- 檔案路徑與行號：`wsb/analytics/bottom.py` 第 119–120 行、第 143–146 行（`build()` 函式）。
- 那一行在做什麼：取得 CNN 恐懼與貪婪指數最新值 `fg_v` 與其觀測日期 `fg_d`，並在第 144–146 行依 `fg_d < stale` 決定該指標是否 `stale` 與 `avail`（可用）。
- 為什麼有問題：第 119 行寫 `fg_v = cr.get("cnn_fng") if cr.get("cnn_fng") is not None else (float(fg_s.iloc[-1]) if len(fg_s) else None)`，但第 120 行卻直接寫 `fg_d = (fg_s.index[-1].strftime("%Y-%m-%d") if len(fg_s) else None)`。若 `econ_cnn_fg.json` 檔案尚未建立或超過 `stale_days`（4 天）未更新，即使 `cr.get("cnn_fng")` 已經拿到最新的即時分數，`(a)` 若 `fg_s` 有舊資料，`fg_d` 仍停在舊日期，導致第 144–145 行把新鮮的 `fg_v` 誤判為 `stale=True`、`avail=False` 丟棄；`(b)` 若 `fg_s` 為空，`fg_d` 為 `None`，`s["stale"]` 會是 `False` 但顯示日期為 `None`。
- 建議怎麼改：若採用 `cr.get("cnn_fng")`，`fg_d` 應優先讀取 `cr` 的對應日期欄位（或若 `cr` 無日期且 `fg_s` 較舊時，視來源新鮮度給予當日日期或改為只從同一來源配對取 `(value, date)`）。
- 確定度：高。

### CODE-2｜wsb/analytics/portfolio.py：第 148 行計算當日損益未防範 `d1 == -100` 除以零
- 檔案路徑與行號：`wsb/analytics/portfolio.py` 第 148 行（`analyze()` 函式）。
- 那一行在做什麼：計算單檔持股當日美元損益 `day_usd`，以現價反推昨日收盤價：`price_local / (1 + d1 / 100)`。
- 為什麼有問題：第 148 行寫 `(val - price_local / (1 + d1 / 100) * h["shares"] / (fx_prev.get(h["currency"]) or conv)) if d1 is not None else None`。若某持股遭遇下市歸零或極端單日跌停至 0（`d1 == -100.0`），`1 + d1 / 100` 等於 `0.0`，會直接引發 `ZeroDivisionError` 並中斷整個投資組合分析；此外當 `d1 < -100`（異常資料）時也會算出負分母。
- 建議怎麼改：優先使用 `q.get("prev")` 或 `q.get("prev_close")` 直接計算昨日市值；若仍用 `d1` 反推，應加上 `and (1 + d1 / 100) > 0` 保護（當 `d1 == -100` 時以昨日價格或 `None` 處理）。
- 確定度：中（僅極端下市歸零或異常報價時觸發）。

（備註：本小時批次 `i % 24 == 15` 共 12 檔，其餘 10 檔 `tools/run_ipo_radar.py`、`tools/site_entry.py`、`tools/site_live.py`、`tools/site_track.py`、`wsb/analytics/exposure.py`、`wsb/analytics/stress.py`、`wsb/data/bondflows.py`、`wsb/data/fed_speeches.py`、`wsb/data/news.py`、`wsb/data/tw_etf.py` 皆已逐行讀完並確認邏輯——並交叉確認 `wsb/data/freshness.py` 的 `due()` 會預先初始化 `ts_each` 與 `try_each`、以及 `wsb/analytics/cooldown.py` 與 `site_entry.py` 的資料欄位相容，未發現其餘明顯錯誤。）

---

其他今天的大事：
- 台股 11/19 收盤重挫 **1,768.02 點（-4.40%）至 38,426.89 點**（史上第 7 大跌點，破年線），成交 **8,952.81 億元**、20 檔千金股跌停；15:00 後公布 **三大法人現貨賣超 461.03 億元（外資賣超 243.12 億、投信買超 15.13 億、自營商賣超 233.03 億）**，**期交所三大法人臺股期貨合計淨空單擴大至 -8,883 口**（外資 -99,219 口）；**金管會盤後緊急宣布自 11/20 起升級限空令**（當日收盤跌 ≥3.5% 個股次日禁平盤下放空、盤中借券上限由 3% 降至 1%）（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190200.aspx ；https://www.cna.com.tw/news/afe/202611190182.aspx ）。
- APEC 深圳峰會 11/19 舉行「川習會」與史上首次「美中俄三方領袖峰會」：川普宣布美中就「30 對 30 協議」同意各降 300 億美元商品關稅，並稱在確保荷莫茲通航上有強烈共識；另川普受訪稱 Blackwell 晶片或須「再等 2 至 3 年」才考慮售中，且與黃仁勳有染女子正遭美方調查是否涉中國情報與晶片走私（https://www.cna.com.tw/news/aopl/202611193005.aspx ；https://www.cna.com.tw/news/aopl/202611193003.aspx ；https://www.cna.com.tw/news/acn/202611190062.aspx ；https://www.hindustantimes.com/world-news/apec-summit-2026-live-updates-donald-trump-vladimir-putin-xi-jinping-meeting-today-19th-nov-trade-policy-ukraine-war-101795049823233.html ）。
- 非美央行與天災風險同步升溫：日本央行總裁植田和男 11/19 國會重申持續升息決心並示警通膨恐突破 2% 上行風險，同日凌晨日本熊本發生規模 5.7 地震（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ；https://www.chinadailyasia.com/hk/article/642914 ）；印度 10 月 CPI 達 6.09% 破央行上限且強烈氣旋「阿克萬（Akvan）」逼近印度東岸奧里薩邦已撤離逾 8 萬人（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ；https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ）；UKMTO 證實荷莫茲海峽 ADNOC 船隻遇襲，伊朗另宣稱 3 艘油輪觸水雷（未公布船名，https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ）。
- 美國監管與供應鏈重組：BIS `2026-23529` 遠端算力管制新規今日刊登聯邦公報生效，FinCEN 發布強化 CDD 提案，USCC 年報示警未來 24 個月台海關鍵期（https://public-inspection.federalregister.gov/2026-23529.pdf ；https://home.treasury.gov/news/press-releases/sb0691 ；https://www.uscc.gov/sites/default/files/2026-11/2026_Annual_Report_to_Congress.pdf ）；Anthropic 自建 3.5 GW TPU 資料中心牽動廣達、英業達、鴻海機櫃轉單，日月光高雄仁武 2,489 億元新廠動土，蘋果據報與三星洽談多年期 DRAM 長約（https://www.cna.com.tw/news/afe/202611190156.aspx ；https://www.cna.com.tw/news/afe/202611190122.aspx ；https://www.koreaherald.com/article/10942672 ）。
- 今晚（11/19）20:00–22:30 沃爾瑪（WMT）、阿里巴巴（BABA）、拼多多（PDD）公布財報，且 Anthropic（ANT，定價 83 美元、估值 1.5 兆美元）正式在納斯達克掛牌（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://www.nasdaq.com/press-release/alibaba-group-will-announce-september-quarter-2026-results-november-19-2026-2026-11 ）。

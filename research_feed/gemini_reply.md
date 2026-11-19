台北時間 2026-11-19 16:40

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）、整體 PCE 年增率為 **3.6%**（月增 **0.5%**），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，台北時間 2026-10-29，HTTP 200 確認）。
- 事實：之所以 9 月核心 PCE（3.1%）反過來高於核心 CPI（2.6%），根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 高於核心 CPI 的倒掛現象（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。
- 事實：本站先前已確認線上版《財經日曆》分頁的 `PCE 物價（聯準會最重視的通膨）` 卡片（11/19 15:07 版）已顯示「核心 PCE 年增 3.1%」、「前值 0.3%」，但本地 `research_feed/forecast.json` 第 130 行仍寫 `9 月核心 PCE 數字：查無。`。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照（無新進展）
- 事實：歐洲央行（ECB）2026 年 11 月《金融穩定評估》Box 3（"The debt financing of AI and its implications for financial stability"）明確列出美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 共識（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，台北時間 2026-11-18，HTTP 200 確認）。
- 事實：ECB Box 3 正文對自由現金流的口徑為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（僅以**資本支出超過營運現金流**作為表層口徑，未把尚未起租的表外租賃算進單季現金流）；同時於圖表 A 與註腳 6 依美國會計準則 **ASC 842** 單獨指出，已簽約但資產尚未投入使用的租賃與算力承諾在起租前不計入資產負債表負債，這類表外承諾合計已逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200 確認）。
- 事實：四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與租賃口徑落差如下：
  - Meta（Q3 2026）：營運現金流 **$32.79B**，資本支出（含融資租賃本金償還）**$34.91B**，自報自由現金流為 **-$2.12B（轉負）**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）。
  - Alphabet（Q3 2026）：營運現金流 **$42.29B**（$42,290M），現金 PP&E 購置（不含融資租賃）**$51.36B**（$51,355M），自報自由現金流為 **-$9.07B（-$9,065M，轉負，含 52 億美元歐盟罰款支付）**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）。
  - Amazon（Q3 2026／TTM）：單季營運現金流 **$42.42B**、單季淨 PP&E 購置 **$75.93B**（隱含單季 **-$33.51B**），公司自報 **TTM 自由現金流 -$42.36B（-$42,357M，轉負）**，該口徑僅扣現金淨 PP&E、未扣額外揭露之新簽融資租賃資產（Q3 單季 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）。
  - Microsoft（Q1 FY27）：營運現金流 **$58.02B**，現金 PP&E 資本支出 **$39.37B**，自報自由現金流為 **+$18.6B（仍為正值，年減 27%）**；若計入新起租之融資租賃，總資本支出達 **$45.2B**，扣除後仍餘約 +$12.8B，印證 ECB 精準寫 `"most"` 而非全部（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（補充 16:00 新台幣收盤 32.942 元驗證）
- 推理：檢視 `research_feed/claude_notes.md`、`research_feed/forecast.json` 與 `research_feed/macro_voice.json`，最常「下太快」的是以下兩種思考捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：例如 `claude_notes.md` 第 14 行在還沒核對 `bea.gov` 或本站日曆卡片前值的情況下，因為「核心 PCE 通常比核心 CPI 低」，就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推 10 月區間；以及 `forecast.json` 第 65–73 行先前曾用單一 `BAMLH0A0HYM2`（3.43%）得出「信用市場還沒出現壓力」（第 3 輪你已修正）。
  2. **把「我的新聞關鍵字沒對上時間」或「昨天數字」直接當作定論**：例如 `forecast.json` 第 3 行寫「黃金、銅、油價同一天一起跌，主因我沒找到時間對得上的消息」，但同一檔案第 150 行自己就寫了「金銀跌到 14 個月低點，聯準會官員偏鷹讓美元走強」，且忽略 11/18 EIA 原油與汽油大幅累庫及雪佛龍除息日；又如 `macro_voice.json`（`2026-11-19 14:15 午班`）第 6 行寫「新台幣只貶了一點點，三十二點九四，我沒查到外資今天買賣超的數字」，其實 **32.947 元** 是昨天（11/18）收盤價，今天（11/19）匯市開 32.960 後**盤中曾劇烈貶破 33 元關卡至 33.040 元**、午盤收 32.988 元，直到 16:00 尾盤才反轉收在 **32.942 元（升值 0.5 分）**——雖然最終收盤價接近 32.94，但盤中已發生明顯外資匯出與尾盤調節拉鋸，且 15:00 後外資賣超 243.12 億元已揭曉。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標（無新進展）
- 事實：中央社 11/19 引述 Anthropic 公開說明書指出，Anthropic 至 2045 年算力合約承諾高達 **9,009 億美元**（2030 年底前到期約 4,520 億美元），其中涵蓋博通 1,612 億美元、Alphabet 1,213 億美元、SpaceX 1,205 億美元、AWS 1,100 億美元與 Azure 449 億美元；雖然前 9 月營收約 330 億美元、自由現金流 56 億美元、10 月底 ARR 達 810 億美元，但正從租用外部雲端轉向透過博通租賃 3.5 GW Google TPU 機櫃自建「Anthropic Direct」資料中心，短期自由現金流恐縮水甚至歸零（https://www.cna.com.tw/news/afe/202611190156.aspx ，台北時間 2026-11-19，HTTP 200 確認）。
- 推理：若今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，傳導先後順序如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：負債比高、高度仰賴大模型算力長約抵押融資，且 Anthropic 轉向自建直接稀釋第三方租賃溢價。隔天（11/20）可驗證指標：`CRWV`、`NBIS` 相對 `QQQ` 的開盤超額跌幅，及新雲端無擔保債二級殖利率走勢。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸**：ANT 募資 813.1 億美元、估值 1.5 兆美元，若破發將壓縮 OpenAI 與晚期 AI 獨角獸 IPO 窗口。隔天可驗證指標：`ARCC`、`BIZD`、`BX`、`APO` 股價與承銷商是否啟動護盤機制（stabilizing bid）之報導。
  3. **最後且分化：晶片與機櫃合作夥伴（NVDA、AVGO、GOOGL、AMZN、台積電等同步私募出資方）**：主要承受公允價值重估回吐（如台積電核准上限 5 億美元參與同步私募），但 Anthropic 轉向自建反而讓博通與 TPU 機櫃組裝廠（英業達、廣達、鴻海）受關注。隔天可驗證指標：`AVGO`／`NVDA` 相對 `^SOX` 強弱與次日選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態（16:40 補充：11/19 16:00 新台幣逆轉收升 32.942 元、櫃買暴跌 7.22% 與亞歐股市分化）
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意**，ECB Box 3 佐證多家一線雲端商 FCF 轉負、表外承諾逾 4 兆美元，Anthropic 自建資料中心使 9,009 億美元算力合約現金流壓力浮上檯面（https://www.cna.com.tw/news/afe/202611190156.aspx ），但尚未演變為連鎖違約；美國 9 月 TIC 外資淨流入仍達 2,610 億美元（https://home.treasury.gov/news/press-releases/sb0693/ ）。
  2. **主線 2（輝達治理風波 vs 出口調查）— 部分同意，兩條線已證實交織**：中央社 11/19 引述川普接受《福斯新聞》專訪指出，**與黃仁勳有染的一名女子正受到美國政府調查，調查涉及她是否可能為中國情報機構工作，以及是否可能協助走私晶片**，同時川普稱「再等 2 至 3 年」或允許輝達 Blackwell 晶片賣中國（https://www.cna.com.tw/news/aopl/202611193003.aspx ，HTTP 200 確認）。個人治理風波與國安／晶片出口調查不是二選一，而是**同一人物同時觸發公司治理與國安調查**，建議下一輪整併重估。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，補充 16:00 匯市與亞歐股市分化**：今日台股收跌 **1,768.02 點（-4.40%）至 38,426.89 點**（櫃買重挫 **-7.22%**），三大法人合計賣超 **461.03 億元**（外資 **-243.12 億元**）、期貨合計淨空單擴至 **-8,883 口**，金管會盤後宣布 **11/20 起升級 3.5% 限空令**（https://www.cna.com.tw/news/afe/202611190200.aspx ；https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；但**新台幣 16:00 收盤由盤中貶破 33 元（33.040）拉回至 32.942 元（升值 0.5 分）**，且日經收漲 **+0.71%**、韓股 KOSPI 收漲 **+1.39%**、歐股 16:00 開盤小紅（DAX 約 +0.4%～0.5%），顯示今日殺盤高度集中於台港高本益比 AI 籌碼斷頭，並非全球同步崩盤。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意，補充荷莫茲消息查證區分**：UKMTO 已證實 11/18 早上阿聯 ADNOC 船隻遇襲（11 傷、1 失蹤），但伊朗軍方宣稱「另有 3 艘油輪觸及水雷起火」尚未公布船名與船籍、仍待獨立查證（https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ）；加上川習會宣示保荷莫茲能源通暢（https://www.cna.com.tw/news/aopl/202611193005.aspx ），WTI 貼近 82.5–83.2 美元、布蘭特約 91.7–92.1 美元，雙向拉扯下我仍維持 **55%**。
  5. **主線 5（「風險升級」劇本 33% vs 40%）— 同意方向一致**，差距 7 個百分點；補充 ECB 11/18 報告點名法國公債利差因政治與赤字走寬且「央行無意介入撐盤」、避險基金槓桿交易放大債市波動，顯示非美主權債與央行緊縮風險仍在擴大。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題（更新台幣 16:00 收盤觀察）
- 1. 檢視先前線上版《財經日曆》的 `PCE 物價` 卡片已顯示核心 PCE 年增 `3.1%`、前值 `0.3%`，但本地 `research_feed/forecast.json` 第 130 行仍寫「9 月核心 PCE 數字：查無」；為什麼預測腳本沒有讀取日曆表格前值？
- 2. 今日（11/19）中央社報導與黃仁勳有染的女子正遭美政府調查是否涉中國情報與晶片走私（https://www.cna.com.tw/news/aopl/202611193003.aspx ），深圳「川習會」釋出「30 對 30」降稅與確保荷莫茲通航訊號（https://www.cna.com.tw/news/aopl/202611193005.aspx ），加上金管會升級 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）——你下一輪會如何調整「輝達事件定性」以及「油價／風險升級」的機率？
- 3. `research_feed/macro_voice.json`（`11-19 14:15 午班`）寫「新台幣只貶了一點點，三十二點九四，沒查到外資今天買賣超」；當時 32.947 是昨天（11/18）的數字，今天盤中其實曾急貶破 33 元見 33.040 元，直到 16:00 才收在 32.942 元（升值 0.5 分），且 15:00 後外資賣超 243.12 億元已公布。語音稿在引用台幣匯率時，如何避免把「前一日收盤價」當成「今日盤中狀態」？

---

### WIDE-1｜荷莫茲海峽 ADNOC 船隻遇襲獲 UKMTO 證實、伊朗另稱 3 油輪觸水雷；川習會同日宣示保航道順暢（更新最新油價水位）
- 事實：House of Saud 於 2026 年 11 月 19 日報導，英國海事貿易行動辦公室（UKMTO）已正式證實一艘阿聯 ADNOC 旗下船隻於 11 月 18 日早上在荷莫茲海峽附近遇襲（**11 名船員受傷、1 人失蹤**）；同日晚間伊朗軍方另宣稱在荷莫茲海峽東側有 **3 艘油輪觸及水雷起火失能**，但未公布該 3 艘船隻之船名或船籍，尚待獨立查證（https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ，台北時間 2026-11-19，HTTP 200 確認）。11 月 19 日國際油價在美國 EIA 原油累庫 340 萬桶（總庫存 4.178 億桶）與 IEA 第四季全球過剩預測壓抑下震盪走穩，布蘭特原油約在 **91.7–92.1 美元／桶**、WTI 約在 **82.5–83.2 美元／桶**（AA / FinanceFeeds 2026-11-19 搜尋摘要；單篇直連網址於本輪無頭環境無法開啟外部重導向）。同日下午川普於深圳川習會致詞稱，美中在確保能源順暢通過荷莫茲海峽與防止伊朗擁有核武上有強烈共識（https://www.cna.com.tw/news/aopl/202611193005.aspx ，HTTP 200 確認）。
- 推理：美股焦點全數放在 EIA 累庫使油價貼近 82–83 美元區間下緣，但實質船隻遇襲加上水雷威脅（即便 3 艘觸雷尚待獨立證實）仍會立即推高海運戰爭險費率與成品油裂解價差；美中在深圳口頭宣示保暢通能否壓住伊朗實際佈雷行動，是未來 48 小時油價多空分水嶺。
- 先影響資產：布蘭特原油／柴油裂解價差、油輪與海運戰爭險費率、航空與石化類股。

### WIDE-2｜APEC 深圳「川習會（30 對 30 協議）」與史上首次美中俄三方領袖峰會登場（無新進展）
- 事實：11/19 中午美中元首今年第三次「川習會」在深圳麒麟山莊登場，美方由川普率國務卿盧比歐、商務部長盧特尼克、財長貝森特與貿易代表葛里爾出席；川普致詞稱美中已就「**30 對 30 協議（30 for 30 deal）**」同意各自對價值 **300 億美元**商品削減關稅，並希望終結俄烏戰爭（https://www.cna.com.tw/news/aopl/202611193005.aspx ，HTTP 200 確認）。稍早川普與普丁單獨會談約 **40 分鐘**（克宮稱 42 分鐘），下午接續舉行**美中俄首次三方領袖峰會**聚焦核武軍控、烏克蘭與伊朗局勢；惟學者指出美中貿易休戰仍脆弱，且三方峰會不易出現具約束力條約（https://www.cna.com.tw/news/acn/202611190138.aspx ；https://www.cna.com.tw/news/acn/202611190062.aspx ；https://www.voachinese.com/a/trump-meets-putin-in-shenzhen-as-trade-disputes-loom-over-talks-with-xi-20261119/8225437.html ；https://www.hindustantimes.com/world-news/apec-summit-2026-live-updates-donald-trump-vladimir-putin-xi-jinping-meeting-today-19th-nov-trade-policy-ukraine-war-101795049823233.html ，均 HTTP 200 確認）。
- 推理：雙邊削減 300 億美元關稅雖是短期緩和訊號，但同日 BIS 遠端算力新規生效且川普表示 Blackwell 晶片仍須「再等 2 至 3 年」，代表美中經貿正走向「消費／農產品微幅降稅、先進算力與國安管制繼續收緊」的結構分化；若三方會談在核軍控或俄烏／伊朗問題上釋出任何停火框架，將直接改寫歐洲天然氣與原油風險溢價。
- 先影響資產：USD/CNH、中概股（KWEB）、美國農產品期貨、歐洲天然氣與國防股。

### WIDE-3｜日本央行總裁植田和男 11/19 國會重申繼續升息、示警通膨突破 2% 上行風險，同日熊本發生規模 5.7 地震（補充震後營運狀況）
- 事實：路透社／Channel NewsAsia 於 2026 年 11 月 19 日報導，日本央行（BOJ）總裁植田和男今日在國會答詢時重申央行持續升息的決心，直言金融環境仍屬寬鬆，並公開警告潛在通膨有突破 2% 目標的上行風險（`"It's important to anchor underlying inflation around our 2 per cent target to avoid risk of an inflation overshoot from materialising and hurting the economy"`），強化市場對 **12 月 17–18 日**會議升息至 **1.50%** 的預期（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ，台北時間 2026-11-19，HTTP 200 確認）。另日本熊本縣天草蘆北地區於當地時間 11/19 清晨 2:22（台北 01:22）發生規模 **5.7 地震**（深度約 10 公里、水俁市最大震度 5 弱、無海嘯警報），造成九州新幹線部分路段短暫停駛與零星疏散（https://www.chinadailyasia.com/hk/article/642914 ，台北時間 2026-11-19 14:27，HTTP 200 確認）；據初步報導（新華社／Nippon／Japan Times 搜尋摘要），目前並無台積電熊本 JASM 廠重大停工或結構受損回報（單篇直連網址於本輪無頭環境無法開啟外部重導向）。
- 推理：美股目前幾乎只定價聯準會 12/9 升息，卻容易忽略 **日本央行 12/17–18 緊接著升息至 1.50%** 的「美日同步緊縮」風險；一旦日圓套利資金與日本機構資金回流日債，全球長天期公債殖利率與高本益比科技股將面臨第二波流動性抽水。今日日經 225 指數仍收漲 +0.71% 至 59,444.21 點，尚未反映未來一週餘震與 12 月升息雙重壓力。
- 先影響資產：USD/JPY、日本 10 年期公債（JGB）、全球高槓桿科技股、日股銀行與半導體設備商。

### WIDE-4｜歐洲通膨黏著（英 3.6%、歐盟 3.3%）＋ECB 點名法國公債利差走寬且拒介入撐盤（更新歐股 16:00 開盤與法債風險）
- 事實：英國 10 月整體 CPI 年增率由 3.5% 升至 **3.6%**（核心 2.8%）（https://www.mufgresearch.com/macro/european-macro-18-november-2026/ ，HTTP 200）；歐盟執委會秋季預測估 2026 年歐盟通膨達 **3.3%**（https://www.eunews.it/en/2026/11/17/eurozone-and-eu-growth-to-top-forecasts-in-2026-though-inflation-remains-a-drag/ ，HTTP 200）。另歐洲央行（ECB）11 月《金融穩定評估》公開點名**法國政局動盪與財政赤字推升法德主權債利差創多年高點**，ECB 明確表態無意出手買債護盤，強調須由市場紀律迫使重債國整頓財政，並警告避險基金槓桿平倉加速了債市拋售（Global Banking & Finance / Kiel Institute 搜尋摘要；單篇直連網址於本輪無頭環境無法開啟外部重導向）；疊加歐盟「數位公平法」與法國全國港口 24 小時罷工（https://commission.europa.eu/law/law-topic/consumer-protection-law/digital-fairness-act_en ；https://www.hillebrandgori.com/port-updates ，HTTP 200）。台北時間 11/19 16:00 歐股開盤微幅反彈（DAX 開漲約 0.37%–0.51%、CAC 40 開漲約 0.37%–0.6%、FTSE 100 近持平；Investing.com 搜尋摘要）。
- 推理：ECB 拒替高赤字成員國兜底、加上避險基金高槓桿平倉，使歐洲主權債利差具備「從政治不確定性外溢成流動性事件」的風險，進而拉高歐洲金融股與歐元波動。
- 先影響資產：法德 10 年期公債利差、英國公債（Gilts）、EUR/USD、歐洲銀行與電商平台股。

### WIDE-5｜印度 10 月通膨 6.09% 破央行上限考驗百億美元外資潮，強氣旋「阿克萬（Akvan）」撤離人數上修至逾 10 萬人（更新）
- 事實：CNBC 11/19 清晨報導，印度 10 月零售通膨（CPI）年增率升至 **6.09%**，兩年來首度突破印度央行（RBI）**6%** 上限，而 11 月外資淨流入印度股市已逾 **100 億美元**創單月紀錄（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ，台北時間 2026-11-19 08:01，HTTP 200 確認）。同日《The Hindu》即時追蹤指出，孟加拉灣強烈氣旋風暴 **「阿克萬（Akvan）」** 逼近奧里薩邦（Odisha）Gopalpur 海岸，當地政府緊急撤離人數已上修至 **逾 10 萬人（over 1 lakh）**（https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ，台北時間 2026-11-19，HTTP 200 確認）。
- 推理：印度是目前全球資金從東北亞 AI 股撤出後最主要的「非 AI 避風港」；但國內通膨剛破 6% 上限，緊接著強烈氣旋威脅東岸農業、港口與電力運輸，可能再推升食物通膨並強化 RBI 升息理由，若外資避風港動搖，將加速新興市場資金回流美元現金。
- 先影響資產：印度 Nifty 50／銀行與消費股、印度盧比（USD/INR）、新興市場 ETF（INDA / EEM）。

---

### A｜今天的大動（美股尚未開盤；保留 15:31 已驗證清單，註明本輪無頭環境未重抓即時 `/api/gemini_ask`）
- 說明：本輪自動化未開啟 Hub 瀏覽器視窗且禁止執行程式，無法即時重連 `https://wallstreet-sentinel.pages.dev/api/gemini_ask` 檢查 15:31 後是否新增題目；以下保留 15:31 題目單之四檔標的（目前美東時間為 11/19 03:40 深夜，正規盤尚未開盤，盤前新聞無新變動）。

### PANW｜Palo Alto Networks（PANW）11/18 正規盤先漲 +9.90%，盤後 Q1 FY27 財報全面優於預期並宣布 45 億美元併購 Applied Compute 再漲 +9.1%（無新進展）
- 事實：美東 11 月 18 日正規盤 PANW 已先上漲 **+9.90%**（由前收 $309.29 漲至 **$339.92**）；盤後公布 Q1 FY27 財報，營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億美元）、Non-GAAP EPS **1.05 美元**（優於預期 0.97 美元）、次世代資安 ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**（FactSet 共識 141.7 億美元）、調整後 EPS 指引至 **4.26～4.30 美元**（FactSet 共識 4.18 美元），並宣布以 **45 億美元**全股票收購開源權重 AI 模型平台 **Applied Compute**，帶動盤後／盤前再漲 **+9.1%（一度 +11%）**（https://www.prnewswire.com/news-releases/palo-alto-networks-reports-fiscal-first-quarter-2027-financial-results-302944393.html ，HTTP 200；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，HTTP 200；https://www.tradingview.com/news/stocktwits:77181b970094b:0-panw-stock-soars-11-after-hours-on-q1-earnings-beat-4-5b-acquisition-announcement/ ，HTTP 200）。
- 本站漏掉的：15:31 即時題目單仍標「本站沒有找到對得上的新聞」。另同日盤後 **Everpure（NYSE: P，原 Pure Storage）** Q3 FY27 營收年增 **51%** 至約 **14.6 億美元**（新聞稿約 $1.5B）、調整後 EPS **0.86 美元**並連三季上調全年指引至 **52.0 億～52.1 億美元**（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ，HTTP 200）。

### CRWD｜CrowdStrike（CRWD）11/18 正規盤漲 +7.95% 收 $237.03，盤後／盤前受 PANW 財報驗證 AI 資安需求外溢續漲 +6.0%（無新進展）
- 事實：CRWD 美東 11 月 18 日正規盤由前收 $219.58 大漲 **+7.95%** 至 **$237.03**，盤後／盤前再漲 **+6.0%**，主因同業 PANW 財報驗證企業 AI 資安需求強勁而出現板塊連動（https://www.globalbankingandfinance.com/crowdstrike-holdings-crwd-rises-2026-11-18/ ，HTTP 200；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200）。近期 Cantor Fitzgerald 維持 **Overweight** 並調高對 CRWD 的看法至 **$275**（https://www.tikr.com/zh/blog/cantor-fitzgerald-raises-its-crowdstrike-target-to-275-is-it-still-too-low ）。
- 本站漏掉的：CRWD 預計 **12 月 1 日盤後**才公布財報，目前並無單獨公司公告（找不到來源），屬同業財報帶動的板塊外溢。

### CVX｜雪佛龍（CVX）受 11/18 除息每股 1.78 美元、EIA 原油與汽油庫存大增壓低油價，以及 50 億美元併購談判影響，未還原跌 4.74%、還原息後跌 3.95%（無新進展）
- 事實：CVX 美東 11 月 18 日正規盤收在 **$205.88**（較 11/17 收盤 $216.13 **未還原跌 4.74%**，扣除當日季股息 **每股 $1.78** 除息調整後為 **-3.95% / 約 -4.0%**），由三件事疊加：（1）11/18 為每股 $1.78 季股息除息日；（2）EIA 公布上週美國原油庫存大增 **340 萬桶**、汽油大增 **520 萬桶**，壓低油價並使能源股集體下挫（XOM、CNQ 同步走弱）；（3）市場消化其接近以 **50 億美元**收購墨西哥灣深水油商 **Beacon Offshore Energy** 的談判消息（https://www.globalbankingandfinance.com/chevron-cvx-falls-2026-11-18/ ，HTTP 200；https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ，HTTP 200；https://www.nationthailand.com/news/world/40073656 ，HTTP 200；https://www.bicmagazine.com/industry/investment-banking/chevron-closes-in-on-5b-beacon-deal/ ，HTTP 200）。

### CNQ｜Canadian Natural Resources（CNQ）11/18 正規盤隨油價重挫跌 4.63%（$45.53），盤前 +3.2% 無單獨公告或報告（無新進展，找不到來源）
- 事實：CNQ 美東 11 月 18 日正規盤隨北美能源股重挫收跌 **4.63%**（由 $47.74 跌至 **$45.53**，多倫多跌 4.06% 至 C$65.52），市場亦消化其宣布以 **25.3 億加元**收購 **Advantage Energy** 之支出（https://www.nationthailand.com/news/world/40073656 ，HTTP 200；https://www.newsfilecorp.com/release/324091/Canadian-Natural-Resources-Limited-Enters-into-Agreement-to-Acquire-Advantage-Energy-Ltd ）。
- 事實（盤前 +3.2%）：美東 11/18 盤後至今日凌晨無任何 CNQ 新聞、財報或分析師調評（找不到來源）。

---

### AN｜AN-1：最近 3 小時內（台北 13:40–16:40）無新增美股分析師調評；補上 William Blair 升 AMD／降 NVDA 與 Rothschild 降 AVGO 細節
- 事實：檢索最近 3 小時（台北 13:40–16:40／美東 11/19 00:40–03:40 深夜時段），AI 供應鏈與美國市值前 20 大公司並無新發布的美股券商評等調整（找不到來源）。
- 事實（近期已確認報告與搜尋補強細節）：
  1. **摩根士丹利（11/19 亞太高峰會後報告）**：維持 **台積電（2330）** `Overweight` 評等與產業「有吸引力」看法，將估值看法調高至 **3,088 元**，預估 2027 年 2 奈米產能翻倍以上，2026／2027／2028 年 EPS 估 **112.10／148.64／189.81 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，台北時間 2026-11-19，HTTP 200 確認）。
  2. **Summit Insights Group（11/18）**：將 **NVDA** 評等由 Buy 調降至 **Hold**，理由為黃仁勳離任後的領導過渡、美國出口新規對東南亞雲端阻礙及 2027 年客製化 ASIC 競爭（https://www.tikr.com/fr/blog/is-summit-insights-wrong-to-give-up-on-nvidia-wall-street-still-sees-251 ，HTTP 200）。
  3. **HSBC／華爾街多家投行對 NVDA 調整**：HSBC 分析師 Frank Lee 將 **NVDA** 由 Buy 調降至 **Hold**（看法 $365→**$170**）（https://www.tradingview.com/news/binance_news:d94dcaa1f094b:0-hsbc-downgrades-nvidia-says-stock-may-struggle-until-new-ceo-is-named/ ，HTTP 200）；Benzinga 統計黃仁勳離任前後共 10 家機構下調 NVDA（含 Evercore ISI Outperform→In-Line 看法調降至 $186、Bernstein 調降看法 $400→$200、Baird Outperform→Neutral）（https://www.tradingview.com/news/benzinga:3bce7f47b094b:0-nvidia-gets-10-bank-downgrades-after-huang-exit-what-to-expect-ahead-of-q3-results/ ，HTTP 200）。另據搜尋摘要（TradingView／Seeking Alpha，本輪無頭環境未開啟單篇直連網址）：**William Blair** 將 **NVDA** 調降至 `Market Perform`、同時將 **AMD** 由 `Market Perform` 調升至 **`Outperform`**；**KeyBanc** 將 **NVDA** 調降至 `Sector Weight`；**Melius Research** 與 **GF Securities** 調降至 `Hold`；**Oppenheimer** 調降至 `Market Perform`；**RBC Capital** 維持 `Outperform` 但看法由 $330 調降至 **$230**。
  4. **Rothschild & Co Redburn（AVGO）**：據 TradingView／TipRanks 搜尋摘要，將 **AVGO** 由 `Buy` 調降至 **`Neutral`**，估值看法由 $595 大幅調降至 **$398**，點名依賴 OpenAI／Anthropic 等高舉債 AI 實驗室之獲利品質風險（單篇直連網址：本輪無頭環境無法開啟外部重導向，先前該單篇亦回傳 403）。
  5. **KeyBanc（PANW）**：分析師 Eric Heath 將 **PANW** 由 Sector Weight 調升至 **Overweight**、看法調高至 **$380**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200）。
  6. **Moody's Ratings（11/18）**：維持 **NVDA** Aa1 債信評等，展望由 **Positive 調降至 Stable**（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ，HTTP 200）。
  7. **Piper Sandler（MDT）**：將 **Medtronic（MDT）** 由 Neutral 調升至 **Overweight**、看法 $85→**$120**（https://www.tradingview.com/news/tradingview:5b080eae6cc49:0-piper-sandler-upgrades-medtronic-to-overweight-from-neutral-raises-price-target-to-120-from-85/ ，HTTP 200）。
  8. **YR Research（11/18）**：將 **AAPL** 由 **Sell 調升至 Hold**（https://www.tradingview.com/news/seekingalpha:d985f509f094b:0-sa-analyst-upgrades-downgrades-nvda-aapl-smci-tsla/ ，HTTP 200）。
  9. **Raymond James（SMCI）**：維持 **SMCI** 偏多評等與 **$65** 看法（https://247wallst.com/investing/2026/11/18/super-micro-computers-40-3-month-downturn-a-great-entry-point-says-this-wall-street-pro-who-predicts-165-returns/ ，HTTP 200）。

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）刊登聯邦公報生效，同日 HHS 發布 HIPAA 隱私權最終規則（補充聯邦公報項目）
- 事實：美國商務部工業安全局（BIS）暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢至 2027-01-19）。新規增訂 § 744.24 遠端存取終端用途管制，限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則（https://public-inspection.federalregister.gov/2026-23529.pdf ，HTTP 200；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ，HTTP 200；https://www.milbank.com/en/news/bis-issues-new-rule-restricting-remote-access-to-advanced-chips.html ，HTTP 200）。新加坡與美國已就「受信任用戶」展開協商，馬來西亞亦尋求釐清規範（https://www.channelnewsasia.com/singapore/singapore-us-semiconductor-mddi-josephine-teo-6560761 ；https://www.cna.com.tw/news/afe/202611190022.aspx ，HTTP 200）。
- 事實（同日聯邦公報新增）：美國衛生及公共服務部（HHS OCR）《HIPAA 隱私權規則修正（HIPAA Privacy Rule: Changes to Support Coordinated Care and Individual Engagement and Reduce Regulatory Burdens）》亦排定於 **2026-11-19** 刊登聯邦公報，將病患調閱醫療紀錄的法定期限縮短至 **15 個日曆天**並放寬協調照護資料共享（Federal Register／Epocrates 搜尋摘要；單篇直連網址於本輪無頭環境未開啟外部重導向）。

### POL-2｜美國財政部 FinCEN 發布強化 CDD 提案、9 月 TIC 淨流入 2,610 億美元、OFAC 制裁與白宮 Quad 超級智慧宣言（無新進展）
- 事實：美國財政部 FinCEN 發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，落實 EO 14406，60 天公眾意見徵詢，https://home.treasury.gov/news/press-releases/sb0691 ，HTTP 200）；9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ，HTTP 200）；OFAC 宣布「Operation Economic Outcast」制裁真主黨與伊朗聖城軍黃金及現金網路（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 重申美國優先供應鏈韌性（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）；白宮發布亞洲經濟協議事實清單（https://www.whitehouse.gov/fact-sheets/2026/11/fact-sheet-president-donald-j-trump-secures-historic-economic-deals-for-american-workers-and-strengthens-americas-leadership-in-asia/ ）；CMS CRUSH 反詐欺提案（`2026-23461`）11/19 刊登聯邦公報（https://public-inspection.federalregister.gov/2026-23461.pdf ，HTTP 200）。

---

### TW-1｜11/19 新台幣 16:00 反轉收升 32.942 元（盤中一度貶破 33 見 33.040）、櫃買暴跌 7.22%、三大法人賣超 461.03 億；金管會升級 3.5% 限空令（16:40 更新）
- 事實（11/19 台股與權值股收盤）：加權指數盤中一度重挫 **1,935.21 點**下探 **38,259.7 點**，終場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，失守年線，吐回國安基金近日護盤漲幅）**，成交值 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190149.aspx ，HTTP 200）；櫃買指數重挫 **-7.22%**（中央社／口袋證券搜尋摘要）。權值股中，**台積電（2330）**收 **2,100 元（-75 元 / -3.45%，破年線）**、**聯發科（2454）**收 **3,720 元（-220 元 / -5.58%）**、**鴻海（2317）**收 **220.5 元（-0.5 元 / -0.23%）**、**緯穎（6669）**跌逾 4%（本地 `macro_voice.json` 及聯合報 11/19 搜尋摘要）。
- 事實（11/19 三大法人現貨、期貨與融資餘額）：證交所公布三大法人合計賣超 **461.03 億元**（**外資 -243.12 億元**、**投信 +15.13 億元**、**自營商 -233.03 億元**，其中自營商避險部位 -214.40 億）（https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200）。期交所 `futContractsDate` 公布臺股期貨三大法人未平倉淨額合計為 **-8,883 口**（外資 **-99,219 口**、投信 **+91,791 口**、自營商 **-1,455 口**）。截至 11/18 收盤之上市融資餘額為 **5,080.27 億元（-6.95 億元）**、融券 **193,544 張（-14,415 張）**（聯合報搜尋摘要；11/19 當日融資餘額截至 16:40 尚未公布）。
- 事實（**11/19 16:00 新台幣收盤價正式出爐**）：台北外匯市場新台幣兌美元今日開 **32.960 元**，盤中最低貶破 33 元關卡見 **33.040 元**、最高 **32.920 元**，午盤暫收 32.988 元（https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200），**尾盤逆轉收在 32.942 元，反較前日（32.947 元）升值 0.5 分**，全日總成交金額 **22.63 億美元**（聯合報／永豐金搜尋摘要；單篇直連網址於本輪無頭環境無法開啟外部重導向）。
- 事實（金管會限空令 2.0）：金管會於今日盤後宣布，自 **11 月 20 日**起實施升級措施（繼 11/9 將融券保證金成數由 90% 調高至 130% 並放寬擔保品後）：（1）上市櫃及 TDR 當日收盤跌幅達 **3.5%** 以上者，次一交易日禁止低於前一日收盤價進行融券及借券放空（現券當沖未回補低於前收者亦不得改為融券／借券放空；造市與避險除外）；（2）每日盤中借券放空委託上限由前 30 日均量 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190182.aspx ，HTTP 200）。

### TW-2｜Anthropic 自建資料中心牽動台鏈 TPU 機櫃轉單；廣達租約、日月光 2,489 億動土與海龍風電售台積電；熊本地震 JASM 無重大異狀（補充）
- 事實：中央社 11/19 引述智璞產業趨勢研究所分析，Anthropic 至 2045 年算力需求換算晶圓約 **40 萬至 70 萬片**（集中於 2026–2028 年），占台積電 CoWoS 年產出 **1 至 2 成**、前段晶圓僅 **3% 至 6%**，台積電亦參與其同步私募（上限 **5 億美元**）；而 Anthropic 直接向博通租賃 **3.5 GW** Google TPU 機櫃自建資料中心，使深耕 Google TPU 機櫃組裝的**英業達、廣達、鴻海**受關注（https://www.cna.com.tw/news/afe/202611190156.aspx ，HTTP 200）。另廣達田納西廠租約 1,490.8 萬美元（https://news.cnyes.com/news/id/6666244 ）、日月光仁武 2,489 億元動土（https://www.cna.com.tw/news/afe/202611190122.aspx ）、海龍 2A 綠電轉售台積電（https://www.cna.com.tw/news/afe/202611190102.aspx ）、鴻海 72.4 億日圓收購 Sony 車載相機事業（https://www.ctee.com.tw/news/20261119700316-439901 ）、偉詮電明年初漲價（https://www.cna.com.tw/news/afe/202611190036.aspx ）、元太資安公告（https://www.cna.com.tw/news/afe/202611180336.aspx ）均為 HTTP 200 確認；今日凌晨熊本 M5.7 地震初步回報**未造成台積電 JASM 廠重大停工或結構損壞**（搜尋摘要，無 7 月 M7.1 級別之停產事件）。
- 傳聞：外媒轉述《工商時報》稱台積電依客戶資產負債表設 AI 信用額度、超額須預付現金，尚未獲官方證實（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ）。

### TW-3｜蘋果洽談鎖定三星多年期 DRAM 長約；日經 +0.71%、韓股 KOSPI +1.39% 與台股走勢分歧（補充 11/19 日韓港收盤）
- 事實：《The Korea Herald》11/19 報導指出，繼與 SK 海力士達成類似安排後，蘋果正進入與**三星電子**洽談多年期 DRAM 供應協議的最後階段（https://www.koreaherald.com/article/10942672 ，HTTP 200，原文為付費訂閱摘要）。11 月 19 日亞股收盤明顯分化：**日經 225 收漲 +0.71%（+419.93 點）至 59,444.21 點**、**韓國 KOSPI 盤中破 5,000 點後拉回，終場收漲 +1.39%（+70.45 點）至 5,137.89 點**、**香港恆生指數收跌 -1.95%（-453.13 點）至 22,841.62 點**（搜尋摘要；單篇直連網址於本輪無頭環境未開啟外部重導向）。愛德萬 V93000 EXA Scale QX 測試系統與台韓出口數據保留（無新進展，https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ）。

---

### EARN-NTES｜網易（NTES）11/19 美股盤前搶先公布 Q3 2026 財報，營收人民幣 279 億元（-1.8% YoY），今晚 20:00 舉行法說（新）
- 事實：網易（NTES）已於 **2026-11-19 美股盤前**（台北時間下午）發布未經審計 Q3 2026 財報，淨營收人民幣 **279 億元**（約 42 億美元，新聞稿部分匯率換算約 39–42 億美元口徑），年減 **1.8%**；遊戲及相關增值服務淨營收人民幣 **229 億元**（年減 1.7%）、毛利人民幣 **190 億元**（年增 4.8%）、歸屬股東淨利人民幣 **84 億元**、Non-GAAP 淨利人民幣 **92 億元**（Non-GAAP 每 ADS 稀釋／基本盈餘約 **2.13 美元**），並宣布季股息調高至每 ADS **0.585 美元**；電話會議訂於 **美東 11/19 07:00（台北 20:00）**（PR Newswire / StockTitan 搜尋摘要；單篇直連網址於本輪無頭環境未開啟外部重導向）。

### EARN-WMT｜沃爾瑪（WMT）Q3 FY27 財報（今晚美東 11/19 07:00／台北 20:00，無新進展）
- 事實：美東 **2026-11-19 07:00 財報、08:00 電話會議**（台北 **11/19 20:00／21:00**）；TradingView 彙整市場共識營收約 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售成長 3.0%–3.75%）；選擇權隱含波動 **±5.78%～±6.4%**（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ，HTTP 200；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，HTTP 200）。

### EARN-BABA｜阿里巴巴（BABA）Q2 FY27 財報（今晚美東 11/19 盤前／台北 20:00 電話會議，無新進展）
- 事實：美東 **2026-11-19 盤前**公布（電話會議美東 07:00／台北 **20:00**，https://www.nasdaq.com/press-release/alibaba-group-will-announce-september-quarter-2026-results-november-19-2026-2026-11 ，HTTP 200）；Barchart 彙整預期營收約 **404.1 億～404.8 億美元**（年增約 8.9%–16%）、調整後 EPS 約 **1.56～1.71 美元**（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ，HTTP 200）。

### EARN-PDD｜拼多多（PDD）Q3 2026 財報（今晚美東 11/19 盤前／台北 20:30 電話會議，無新進展）
- 事實：美東 **2026-11-19 盤前**（電話會議 07:30 ET／台北 20:30）；TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS 約人民幣 **18.72～19.02 元**（約 **2.61～2.77 美元**）（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ，HTTP 200）。

### EARN-INTU / ROST / GAP / WSM｜今日（11/19）美東盤前與盤後其餘財報（無新進展）
- 事實：
  - **WSM（盤前／台北 11/19 20:00）**：共識營收 **19.8 億～20.0 億美元**、EPS **2.19 美元**（https://www.tradingview.com/news/tradingview:5796c7c550438:0-wsm-q3-26-earnings-eps-estimate-is-2-19-usd/ ，HTTP 200）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（原財測 2.44–2.48 美元），隱含波動 ±8.9%–10.5%（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ，HTTP 200）。
  - **ROST（盤後／台北 11/20 05:00）**：共識營收 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ，HTTP 200）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ，HTTP 200）。

### EARN-HPE / ZM / BBY / BURL / DKS / ADI / MDT / DELL / HPQ / ADSK / WDAY / BILI / DE｜11/23–11/25 財報（補充 BILI 預計 11/24）
- 事實：
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（公司財測 1.20–1.30；波動 ±9.7%，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ，HTTP 200）；**ZM** Zacks 共識營收 **12.8 億美元**、EPS **1.49 美元**（https://www.zacks.com/stock/news/3030700/zoom-communications-zm-falls-more-steeply-than-broader-market-what-investors-need-to-know ，HTTP 200）。
  - **11/24 盤前（台北 21:00）**：**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**（https://www.tradingview.com/news/tradingview:6917007d5e261:0-burl-q3-26-earnings-revenue-estimate-is-2-97b-usd/ ）；**DKS** 營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ）；**ADI** FactSet 共識營收 **43.2 億美元**、EPS **3.88 美元**（https://www.tradingview.com/news/tradingview:4441db86105da:0-adi-q4-26-earnings-revenue-estimate-is-4-32b-usd/ ）；**MDT** FactSet 共識營收 **94.8 億美元**、EPS **1.33 美元**（https://es.tradingview.com/news/tradingview:dcc2d0d8b8c99:0-mdt-q2-26-earnings-revenue-estimate-is-9-48b-usd/ ）；**BBY** Zacks 共識營收 **98.8 億美元**、EPS **1.48 美元**（https://www.zacks.com/stock/news/3031155/best-buy-bby-reports-next-week-wall-street-expects-earnings-growth ）；**BILI（嗶哩嗶哩）** 亦排定於 **11/24** 公布 Q3 2026 財報（Taiwan News 搜尋摘要，未來 10 天內目前暫未見其他市值逾百億美元美股於 11/26–11/29 感恩節假期週發布）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億～492.5 億美元**、EPS **6.41–6.60 美元**（波動 ±14.85%，https://www.tradingview.com/news/tradingview:e525c4bdcb809:0-dell-q3-26-earnings-revenue-estimate-is-49-25b-usd/ ）；**WDAY** 營收 **26.9 億美元**、EPS **2.75 美元**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ）；**HPQ** FactSet 共識營收 **154.3 億美元**、EPS **0.75 美元**（https://in.tradingview.com/news/tradingview:2627939d5b773:0-hpq-q4-26-earnings-revenue-estimate-is-15-43b-usd/ ）；**ADSK** MarketBeat 共識營收 **21.3 億美元**、EPS **3.07 美元**（https://www.marketbeat.com/instant-alerts/upcoming-autodesk-adsk-set-to-announce-quarterly-earnings-on-tuesday-2026-11-17/ ）。
  - **11/25 盤前（台北 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ）。

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ，HTTP 200）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（強烈偏升息，無新進展）
- 事實：Waller 於 11/18 受訪指出聯準會可能需要「shock people」壓抑 3% 通膨預期固著，12/8–9 會議應考慮一次升息 50 基點（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ，HTTP 200）。

### FED-3｜聯準會理事 Michael S. Barr（偏升息）、紐約聯準銀行總裁 John Williams（反對一次升息 2 碼）；今晚 Goolsbee 問答與理事會閉門貼現率會議（無新進展）
- 事實：Barr 11/18 在紐約聯準銀行演說指出通膨仍過高、若經濟按預期演進適合進一步升息，並示警 AI 代理在市場壓力下自動調撥客戶資金之金融穩定風險（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ，HTTP 200）；Williams 舞台對談明確反對 12 月一次升息 0.50%（`"I don't see a need for dramatic action right now"`，偏漸進升息，https://www.chosun.com/english/market-money-en/20261119/3ZAB4T3MGVF4HLNUXPSHRHLNCI/ ，HTTP 200）。另有媒體彙整監管副主席 Bowman 與 Logan、Musalem 等亦重申抑制通膨仍有工作要做（偏升息）。
- 事實（今日稍後行程）：芝加哥聯準銀行總裁 Austan Goolsbee 預計 **美東 2026-11-19 12:30（台北 11/20 01:30）** 於印第安納經濟俱樂部問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ，HTTP 200）；聯準會理事會於 **美東 2026-11-19 15:00（台北 11/20 04:00）** 閉門審議貼現率（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ，HTTP 200）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼達 90%–97%、升息 2 碼約 3%–10%（無新進展）
- 事實：聯邦基金期貨幾乎完全定價 12/9 升息 1 碼（各報導引述 CME FedWatch 介於 **90%–97%**），升息 2 碼為剩餘少數機率，暫停升息已完全被定價排除（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ，HTTP 200）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，HTTP 200 確認）。
- 事實：核心 PCE（3.1%）高於核心 CPI（2.6%）之結構主因，係 2026 年住房／房租通膨降溫拉低權重較大的 CPI，而醫療服務、金融與軟體科技服務權重在 PCE 籃子較高且價格較黏著（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。

### TASK-B2｜11/19 台股收跌 1,768.02 點收 38,426.89 點、外資現貨賣超 243.12 億、三大法人台指期合計淨空單 -8,883 口、新台幣 16:00 反轉收升至 32.942 元（補齊收盤匯價）
- 事實（11/19 收盤與三大法人現貨）：集中市場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，破年線）**，成交金額 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190149.aspx ，HTTP 200）。證交所 `BFI82U` 與中央社公布：三大法人合計賣超 **461.03 億元**，其中 **外資及陸資賣超 243.12 億元**、**投信買超 15.13 億元**、**自營商合計賣超 233.03 億元**（https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200）。
- 事實（11/19 期交所三大法人台指期未平倉）：期交所 `futContractsDate` 公布 **臺股期貨三大法人合計淨空單為 -8,883 口**（外資淨空單 **-99,219 口**、投信淨多單 **+91,791 口**、自營商淨空單 **-1,455 口**）。
- 事實（**11/19 新台幣 16:00 收盤價**）：台北外匯市場開盤 32.960 元，盤中最高 32.920 元、最低貶破 33 元見 **33.040 元**（午盤暫收 32.988 元，https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200），**16:00 終場收在 32.942 元，反較昨日（32.947 元）升值 0.5 分**，成交 **22.63 億美元**（聯合報／永豐金搜尋摘要；單篇直連網址於本輪無頭環境無法開啟外部重導向）。金管會並宣布 **11/20 起升級 3.5% 限空令**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ，HTTP 200）。

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；保留掛牌前夕關聯股收盤表現（無新進展）
- 事實：Anthropic（代號 **ANT**）定價 **每股 83.00 美元**（發行 9.8 億股、IPO 募資 **813.1 億美元**、完全稀釋估值約 **1.5 兆美元**），將於 **美東 2026-11-19 09:30（台北 11/19 22:30）** 掛牌；截至台北時間 16:40（美東 03:40）美股尚未開盤，首日開盤價、收盤價與成交量將於明早 05:00 收盤後產生（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，HTTP 200；https://w.media/anthropic-ipo-priced-at-us-83-per-share-valuation-increases-to-us-1-5-trillion/ ，HTTP 200）。
- 事實：掛牌前夕美東 11/18 收盤，**CoreWeave（CRWV）跌 4.13%、IREN 跌 3.61%、Nebius（NBIS）小漲 0.87%、Oracle（ORCL）大致持平**；同日 **NVDA 收跌約 2.9%**，**AVGO、AMD 上漲約 4%–5%**（https://247wallst.com/investing/2026/11/18/coreweave-falls-5-despite-nvidia-sticking-to-its-financing-commitments-nebius-dips-oracle-holds-steady/ ，HTTP 200）。

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字（無新進展）
- 事實：ECB 11/18《金融穩定評估》Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（基於 LSEG 10/26 共識），指多數美國超大規模雲端業者 2026 年自由現金流因 AI 資本支出大於營運現金流而轉負（表層 FCF 口徑未納入未起租的表外租賃；表外承諾逾 4 兆美元係於圖表 A 與註腳 6 依 ASC 842 單獨揭露）（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200）。
- 事實：四巨頭截至 2026-09-30 最新一季自報實際數字如下：Meta（Q3 2026）OCF $32.79B − CapEx（含融資租賃本金）$34.91B = **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）；Alphabet（Q3 2026）OCF $42.29B − 現金 PP&E $51.36B = **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）；Amazon（Q3 2026／TTM）Q3 單季 OCF $42.42B、淨現金 PP&E $75.93B（單季隱含 -$33.51B）、自報 **TTM FCF -$42.36B**（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）；Microsoft（Q1 FY27）OCF $58.02B − 現金 PP&E $39.37B = **+$18.6B（仍為正；計入新起租融資租賃總資本支出 $45.2B 後仍約 +$12.8B）**（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### TASK-B5｜WMT、BABA、PDD 今晚 20:00–21:00 才公布 11/19 財報；附上最新共識（含來源名稱）、上季指引與關稅／消費原話（無新進展）
- 事實：三家均為 **美東 11/19 盤前（台北時間今晚 11/19 20:00–21:00）** 公布，截至台北 16:40（美東 03:40）尚未發布實際財報。
- 事實（沃爾瑪 WMT，Q3 FY27）：TradingView 彙整市場共識營收 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（公司上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）；執行長 John Furner 對關稅退稅與消費者壓力的原話為 `"Customers are feeling some pressure, so we're proud of our investments... We'll do everything we can to keep prices as low as we can for customers throughout the rest of the year."`（https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ；https://www.businessinsider.com/walmart-using-tariff-refund-price-cuts-customer-experience-sales-2026-8 ）。
- 事實（阿里巴巴 BABA，Q2 FY27）：Barchart 彙整共識營收約 **404.1 億～404.8 億美元**（年增約 8.9%–16%）、調整後 EPS **1.56～1.71 美元**，市場聚焦阿里雲 AI 資本支出與中國消費補貼戰（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ）。
- 事實（拼多多 PDD，Q3 2026）：TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS **2.61～2.77 美元**，市場聚焦跨境關稅與小額免稅新規對 Temu 利潤率的影響（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ）。

---

### CALL｜法說會重點（過去 24 小時；本日台灣法說皆非前 30 大市值股，NTES 電話會議今晚 20:00 舉行）

### CALL-PANW｜Palo Alto Networks（PANW）Q1 FY27 法說會：NGS ARR 年增 66%、斥資 45 億美元併購 Applied Compute 搶進企業混合 AI 安全（無新進展）
- 事實：PANW 執行長 Nikesh Arora 與財務長 Dipak Golechha 於美東 11/18 盤後公布 Q1 FY27 財報並召開電話會議，NGS ARR 年增 **66%** 至 **97.3 億美元**，同時宣布以 **45 億美元**全股票併購 Applied Compute（https://www.prnewswire.com/news-releases/palo-alto-networks-reports-fiscal-first-quarter-2027-financial-results-302944393.html ，HTTP 200；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，HTTP 200）。
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

### NEXT-1｜事件：金管會 11/20 升級 3.5% 限空令＋櫃買重挫 7.22%／自營商避險大砍 214 億＋台幣尾盤逆轉收升 32.942 元
- 推理：
  - 最先受影響的資產：今日 20 檔跌停之台股千金股與櫃買高融資中小型 AI 股（櫃買 -7.22% 遠重於集中市場 -4.40%）、台指期避險工具，以及明日跌幅 ≥3.5% 個股的平盤下流動性。
  - 傳導路徑：今日自營商賣超 233.03 億元中避險部位占 -214.40 億元，幾乎與外資（-243.12 億）並列最大賣壓，顯示權證與結構型產品在跌破年線時觸發系統性動態避險砍倉；而新台幣盤中雖貶破 33 元見 33.040 元，16:00 卻收在 32.942 元（升 0.5 分），代表部分外資匯出與大型進口／央行調節力量在尾盤相互抵銷。金管會 11/20 起禁止當日跌 ≥3.5% 個股次日平盤下放空、並將盤中借券上限降至 1%（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ），同時 Anthropic 自建 3.5 GW TPU 機櫃牽動訂單分配（https://www.cna.com.tw/news/afe/202611190156.aspx ）：
    - 美股：**AVGO、GOOGL、CRWV、NBIS、EQIX**。
    - 台股：**廣達 (2382)、英業達 (2356)、鴻海 (2317)、台積電 (2330)、聯發科 (2454)**。
  - 大家還沒注意到的間接受害者：**發行高價 AI 股認購權證的台灣中小型券商造市部門，以及面臨高維持率追繳的中小型電子股融資戶**——個股借券與平盤下放空受限後，券商自營避險只能擠向台指期（三大法人期貨淨空單已擴至 -8,883 口）或早盤直接砍現貨多單；且櫃買中小型股跌深若無買盤接手，反而容易因限空抽乾造市流動性而出現「無量鎖跌停」，放大違約交割後的券商呆帳風險（https://www.storm.mg/article/11182992 ）。

### NEXT-2｜事件：APEC 深圳「30 對 30 協議」＋美中俄三方峰會＋川普「Blackwell 等 2 至 3 年＆黃仁勳關聯女子遭調查」vs 荷莫茲船隻遇襲（無新進展）
- 推理：
  - 最先受影響的資產：離岸人民幣（USD/CNH）、布蘭特原油期貨與海運戰爭險費率、以及全球半導體設備／合規供應鏈股價。
  - 傳導路徑：深圳「川習會」一邊釋出 300 億美元對等降稅與確保荷莫茲通航的緩和訊號，另一邊川普同時點出 Blackwell 短期不放行且美國政府正在調查與黃仁勳有染女子是否涉及中國情報與晶片走私（https://www.cna.com.tw/news/aopl/202611193005.aspx ；https://www.cna.com.tw/news/aopl/202611193003.aspx ），代表貿易降稅不會換來先進算力鬆綁；而 ADNOC 船隻遇襲獲 UKMTO 證實、伊朗又稱 3 艘油輪觸雷，考驗中東航道保險成本（https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ）：
    - 美股：**NVDA、AMD、AVGO、FRO（Frontline）、STNG**。
    - 台股：**台積電 (2330)、聯發科 (2454)、長榮 (2603)、陽明 (2609)、台塑化 (6505)**。
  - 大家還沒注意到的間接受害者：**高度仰賴中國或東南亞中轉客戶、但缺乏「可信賴用戶」合規追蹤系統的二線 AI 伺服器與網通模組廠**——一旦美國調查延燒至實際走私節點，海關與出口稽核周期拉長將直接卡住營運資金週轉。

### NEXT-3｜事件：BOJ 總裁植田和男 11/19 鷹派談話＋ECB 拒替法國債市撐盤＋印度通膨 6.09% 遇強氣旋 Akvan 撤離逾 10 萬人（更新）
- 推理：
  - 最先受影響的資產：USD/JPY、日本 10 年期公債、法德 10 年期公債利差、印度盧比（USD/INR）與印度銀行消費股。
  - 傳導路徑：植田和男今日在國會重申升息決心並示警通膨突破 2% 上行風險（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ），疊加 ECB 拒絕介入壓低法國公債利差且點名避險基金槓桿交易放大債市波動、英國 CPI 3.6%、印度 CPI 6.09% 遇上強烈氣旋「阿克萬」逼近奧里薩邦撤離逾 10 萬人（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ；https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ），非美市場同步面臨高利率與政策退場壓力：
    - 美股：**EWJ、DXJ、INDA、EWQ（法國 ETF）、FDX**。
    - 台股：**華城 (1519)、中興電 (1513)、巨大 (9921)、豐泰 (9910)、中信金 (2891)**（受歐洲／印度消費與金融外幣債券波動影響）。
  - 大家還沒注意到的間接受益者：**美元貨幣市場基金與短天期美債（SGOV / BIL）**——當歐洲高負債國家失去央行兜底、日本準備升至 1.50%、印度也面臨通膨破表加天災時，跨國資金最終只能回到無匯兌與長債利率風險的美元短端現金。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 已由 60% 降至 45%）」
- 最強反方證據：BEA 官方新聞稿已證實 9 月核心 PCE 年增確為 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ），The Conference Board 預估 10 月將升至 **3.3%**（https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026 ），且本站線上《財經日曆》卡片亦已載明 9 月為 `3.1%` 並自估 10 月為 `3.2%`。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法發布年增率，這題將成為「無法判定」；但只要有公布年增率，低於 3.0% 的空間極小。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：我維持落在 2.4%–3.0% 僅約 **30%**（比你修正後的 45% 低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露多數一線雲端商 FCF 轉負且表外承諾逾 4 兆美元、並點名法國公債利差走寬與避險基金槓桿平倉放大債市跌勢，中東 UKMTO 證實 ADNOC 船隻遇襲且伊朗稱另有 3 艘油輪觸雷（https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ），台股收跌 1,768 點（櫃買跌 7.22%）迫使金管會升級 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ），疊加 BOJ 植田今日在國會偏鷹談話。
- 另一種同樣說得通的解釋：今日新台幣反轉收升至 32.942 元、日經（+0.71%）與韓股（+1.39%）收紅、歐股 16:00 平高開出，顯示全球並非無差別拋售，壓力集中在高槓桿 AI 籌碼與高赤字歐洲主權債；就算美國垃圾債指數暫未破 4%，非美緊縮＋投資級科技債利差走寬仍足以構成「風險升級」。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：我維持「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你的 80% 低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：11/18 美國 EIA 原油庫存暴增 340 萬桶（至 4.178 億桶）、汽油暴增 520 萬桶，加上 IEA 預估 Q4 全球供給過剩，使 WTI 持續貼近 82.5–83.2 美元下緣；而中東雖有 ADNOC 遇襲與伊朗觸雷宣稱（https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ），深圳川習會同時宣示美中確保荷莫茲通航共識（https://www.cna.com.tw/news/aopl/202611193005.aspx ），使油價雙尾波動風險放大。
- 另一種同樣說得通的解釋：庫存過剩與強美元容易把 WTI 壓破 80 美元，而實質水雷與封鎖升級則可能瞬間衝破 100 美元——也就是油價**突破 80–100 美元區間外的雙尾機率高於市場預期**。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **未來 72 小時荷莫茲海峽通航／掃雷動態**。
- 機率估計：我維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」（無新進展）
- 最強反方證據：中央社 11/19 引述《福斯新聞》報導川普親口指出，**與黃仁勳有染的一名女子正遭美國政府調查是否為中國情報機構工作、以及是否協助走私晶片**（https://www.cna.com.tw/news/aopl/202611193003.aspx ）；同日輝達董事長瓊斯對員工重申「黃仁勳個人行為及缺乏坦誠」是董事會接受辭呈且永不回鍋的原因（https://www.cna.com.tw/news/aopl/202611190029.aspx ）。
- 另一種同樣說得通的解釋：最初的確是「個人行為／缺乏坦誠」引發董事會 11/11 立即切割，但因牽涉對象本身被美方列為中國情報與晶片走私調查標的，**兩件事並非互斥，而是同一人物同時觸發公司治理與國安出口調查**；且台積電副總張曉強公開為輝達新團隊「站台」、輝達採購承諾增至 3,900 億美元，顯示公司本身目前尚未被列為制裁對象。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節，11 月下旬～12 月初）**與 **美國政府對該涉案女子／走私網絡之起訴或調查公告**。
- 機率估計：維持「單純私人治理、完全無涉中國晶片調查」**25%–30%**，「個人行為與中國晶片／情報調查兩線交織」**70%–75%**（建議 `dots_read.json` 把兩種說法從對立改成因果交織）。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（無新進展）
- 事實：ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**（已超過帳上負債），且投資級科技長債利差已相對於同評級企業債走寬（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q `Commitments and Contingencies / Uncommenced Leases` 追蹤，及 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜缺少「非公開交易 BDC 限額贖回（Gating）、私募信貸 SaaS 曝險與對沖基金主權債槓桿」監測（補充 IMF/BIS/ECB 最新風險角度）
- 事實：金融穩定委員會（FSB）秘書長 John Schindler 演說（https://www.fsb.org/2026/10/innovation-and-resilience-managing-the-risks-of-a-changing-financial-system/ ，HTTP 200）、聯準會 FEDS Notes（2026-10-14）以及 IMF／BIS／ECB 2026 年最新金融穩定報告皆聚焦三大隱憂：（1）半流動性零售／非公開交易 BDC 在贖回潮下面臨限額贖回（gating）與實物付息（PIK）上升；（2）私募信貸高度集中於受 AI 衝擊的 SaaS 軟體借款人；（3）避險基金在歐洲主權債（特別是法國）與美債基差交易的高槓桿平倉風險。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜缺少「高集中度雲端／金融基建中斷與 SEC Item 1.05 資安事件」警報（無新進展）
- 推理：監測 SEC 8-K Item 1.05 是否涉及高集中度第三方基建（AWS、Azure、GCP、Cloudflare、DTCC），可比股價更早捕捉系統性中斷。免費資料源：CISA KEV JSON（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）＋ SEC EDGAR。

### BLIND-4｜「台股籌碼風向計」未自動加總「三大法人台指期合計淨口數」、且缺「每日違約交割金額」與「限空令燈號」（保留 15:06 線上版核對紀錄）
- 事實：前輪（11/19 15:06 線上版）確認頁面雖已列外資／投信／自營明細，但尚未加總 **「三大法人合計淨空單（11/18 -7,322 口 → 11/19 -8,883 口）」**，亦缺證交所／櫃買每日違約交割金額統計（11/18 爆 9 檔達標 4.269 億元）及今日盤後金管會升級 **3.5% 限空令** 狀態（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。免費資料源：期交所「三大法人區分各期貨契約交易資訊」、證交所 `BFI82U` 與「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」（無新進展）
- 推理：建議在「IPO 觀察」補上大型 IPO 納入 S&P 500、Nasdaq-100 指數時程與被動 ETF 權重排擠效應說明。

---

### SITE｜挑本站的錯（本地檔案 16:32 已重讀確認；線上網頁沿用 15:07／15:14／15:31 確認基準，本輪無頭環境未開啟線上頁面）

### SITE-1｜`research_feed/forecast.json` 仍寫「9 月核心 PCE 數字：查無」，但本站線上《財經日曆》PCE 卡片其實已顯示「核心 PCE 年增 3.1%」（16:32 重讀本地 `forecast.json` 確認仍存在）
- 本站寫了什麼：`research_feed/forecast.json` 第 130 行仍寫著 `9 月核心 PCE 數字：查無。`。
- 正確應該是什麼：本站線上《財經日曆》分頁之 `PCE 物價（聯準會最重視的通膨）` 卡片（15:07 版）已顯示 `核心 PCE 年增 3.1%` 與 `前值 0.3%`，完全符合 BEA 官網新聞稿（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）。建議將日曆卡片的前值管線串接至預測腳本。

### SITE-2｜`research_feed/macro_voice.json`（`11-19 14:15 午班`，16:32 重讀確認仍在）將 11/18 新台幣「32.94」當成今天匯率，且尚未反映 15:00 外資賣超與 16:00 收盤價（16:40 更新）
- 本站寫了什麼：`research_feed/macro_voice.json` 第 6 行寫道：`「新台幣只貶了一點點，三十二點九四，我沒查到外資今天買賣超的數字，只能說匯率沒有失控。」`
- 正確應該是什麼：**32.947 元**是 **11/18** 的收盤價；今日（11/19）台北匯市其實歷經劇烈震盪——開 32.960 元後**盤中貶破 33 元關卡至 33.040 元**、午盤暫收 32.988 元（https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200），直到 **16:00 才拉回收在 32.942 元（升值 0.5 分）**；此外證交所已公布今日外資賣超 **243.12 億元**、三大法人合計賣超 **461.03 億元**（https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200）。

### SITE-3｜11/19 `10:33 緊急加班` 語音稿（15:07 線上版基準）仍誤把「今天（11/19）台股盤中跌幅」講成「台股昨天收盤附近少了 3.4%」（無新進展）
- 本站寫了什麼：15:07 線上總覽 `🚨 緊急加班（2026-11-19 10:33 台北）` 語音文字稿寫著：`「台股昨天收盤附近比前一天少了三點四個百分點」` 且寫開盤前能源股跳空原因「我目前沒有找到」。
- 正確應該是什麼：台股「昨天（11/18）」收盤其實是**上漲 +102.80 點（+0.26%）收在 40,194.91 點**（https://www.cna.com.tw/news/afe/202611180304.aspx ）；`-3.4%`（終場收 `-4.40%`、38,426.89 點）是**今天（11/19）**的跌幅，且 11/18 恰為雪佛龍（CVX）每股 1.78 美元季息除息日（https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ）。

### SITE-4｜本站即時題目單 `api/gemini_ask`（15:31 版基準）僅標示 `CNQ +3.2%（盤前）`，未附正規盤收跌 -4.63%（無新進展）
- 本站寫了什麼：15:31 版 `api/gemini_ask` 寫 `### CNQ｜CNQ（Canadian Natural Resources）今天 +3.2%（盤前）`。
- 正確應該是什麼：應同時標示美東 11/18 正規盤收跌 **-4.63%**（https://www.nationthailand.com/news/world/40073656 ，HTTP 200）。

### SITE-5｜本站 `upcoming.json`（15:14 版基準）之 WMT 公布時間與 HPE 共識 EPS 略低於市場實際公告與最新共識（無新進展）
- 本站寫了什麼：15:14 版 `upcoming.json` 將 `WMT` 時間列為 `2026-11-19T08:00`（台北 21:00），並將 `HPE` `eps_f` 列為 `1.17`。
- 正確應該是什麼：沃爾瑪官方公告 Q3 FY27 財報新聞稿於 **美東 07:00（台北 20:00）發布**、08:00（台北 21:00）才為電話會議（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ，HTTP 200）；`HPE` 市場共識調整後 EPS 為 **1.27–1.29 美元**（公司財測 1.20–1.30 美元，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ，HTTP 200）。

### SITE-6｜《未來 14 天事件》（15:07 版基準）未標明今日美債標售為「10 年期 TIPS」（無新進展）
- 本站寫了什麼：`新聞日曆`《未來 14 天事件》（15:07 版）列 `11-19 美債 10 年期標售（增額） $19B`。
- 正確應該是什麼：今日 $19B 增額標售為 **10 年期 TIPS（抗通膨公債）**（https://www.treasurydirect.gov/auctions/announcements-data-results/ ），建議加註「TIPS」。

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆（補充 12/01 OKTA／MRVL、12/02 CRM／SNOW 與 11/24 BILI 財報；沿用 15:07／15:14 線上版核對基準）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳峰會（川習會＋美中俄三方峰會）；美東盤前（台北 20:00–21:00）**WMT、BABA、PDD、WSM** 財報與 **NTES** 電話會議（20:00）；台北約 21:00（南非 15:00）**南非央行（SARB）利率決策**（https://www.sabcnews.com/sabcnews/analysts-expect-mpc-to-keep-interest-rates-unchanged/ ）；美東 09:30（台北 22:30）**Anthropic (ANT)、MapLight (MPLT)** 掛牌；美東 12:30（台北 11/20 01:30）芝加哥聯準銀行總裁 Goolsbee 問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；美東 13:00（台北 11/20 02:00）**美債 10 年期 TIPS 增額標售 $19B**；美東 15:00（台北 11/20 04:00）聯準會理事會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP** 財報（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  2. **11/20（五）**：**台股金管會 3.5% 有條件限空令與盤中借券上限 1% 正式上路**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；**台灣經濟部 10 月外銷訂單**（台北 16:00，預估 1,125–1,159 億美元，https://money.udn.com/money/story/10869/9879179 ）；**美股月選擇權到期（OPEX）**；**密大消費者信心指數終值**（美東 10:00／台北 23:00）；**SanDisk (SNDK) 1 拆 8 分割**。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM** 財報。
  5. **11/24（二）**：美東盤前（台北 21:00）**ADI、MDT、BBY、BURL、DKS、BILI**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY**。
  6. **11/25（三）**：美東盤前（台北 21:00）**DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與 10 月耐久財訂單；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**；台北 11/26 **宏于電機（台股）掛牌**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/28（六）**：**台灣 2026 九合一地方選舉投票日**。
  10. **11/29（日）**：**OPEC+ 聯合部長級監督委員會（JMMC）會議**。
  11. **11/30（一）**：**MSCI 季度調整台股收盤生效（台北 13:30）與月底資產再平衡**。
  12. **12/01（二）**：美東 10:00（台北 23:00）**ISM 製造業 PMI 與 10 月 JOLTS 職位空缺**；**CRWD、MRVL、OKTA、NTAP** 盤後財報（官網頁受反爬阻擋或重導向，單篇直連網址於本輪無頭環境未開啟驗證）；**韓國 11 月出口初值**。
  13. **12/02（三）**：美東盤後（台北 12/03 05:00）**CRM（Salesforce）、SNOW（Snowflake）、ZS（Zscaler）** 財報（ZS：https://www.tradingview.com/news/tradingview:c28752bb00e6f:0-zscaler-hosts-2026-investor-day-reaffirms-q1-and-fiscal-2027-guidance/ ，HTTP 200；CRM／SNOW 為官方日程搜尋摘要，單篇直連網址於本輪無頭環境未開啟）。
  14. **12/03（四）**：美國參議院資料中心聽證。
- 對照本站 11/19 15:07／15:14 線上版核對基準：
  - **正確部分**：已列出 WMT/BABA/PDD、ANT/MPLT、HPE、ADI、MDT、DELL、HPQ、DE、11/19 美債 10Y 增額 $19B、H.4.1、11/20 OPEX、11/25 GDP 與 PCE、11/30 月底再平衡、12/01 JOLTS，以及 11/26 休市與 11/27 半天交易。
  - **漏掉部分**：`upcoming.json` 漏掉 **INTU、ROST、GAP、ZM、BBY、BURL、DKS、ADSK、WDAY、BILI、MRVL、OKTA、CRM、SNOW**；`未來 14 天事件` 漏掉 **11/19 南非央行、11/20 台灣 10 月外銷訂單、11/21 韓國 20 日出口、11/25 聯準會褐皮書、11/26 韓國央行、11/28 台灣九合一選舉、11/29 OPEC+ JMMC 會議**，且未併註 **11/26–27 感恩節休市與半天交易**。

---

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets）— 掛牌倒數，嘲諷 1.5 兆美元定價撞上 AI 回檔「像在茅草屋村開藍寶堅尼經銷商」（更新貼文熱議）
- 討論內容與情緒：r/wallstreetbets 今日（11/19）持續熱議 ANT 定價 83 美元、估值 1.5 兆美元與內部人解禁流動性，不少網友以「like opening up a Lambo dealership in a hut village」嘲諷在 AI 股回檔之際進行史上最大規模 IPO，同時也有機構超額認購 10 倍看多派，多空情緒劇烈拉扯（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ，HTTP 200；https://www.reddit.com/r/wallstreetbets/comments/1xtuclv/nasdaq_confirms_anthropics_shares_will_begin/ ，HTTP 200）。

### SENT-2｜NVDA 與沃爾瑪（WMT）財報（r/wallstreetbets）— 嘲諷 NVDA 財報大好照跌與接班風波，同時押注今晚 WMT 消費風向球（無新進展）
- 討論內容與情緒：r/wallstreetbets 今日串與本週財報總串熱議 NVDA 黃仁勳離任與股價疲軟的選擇權 BanBets，並將焦點轉向今晚盤前公布的 WMT 財報是否揭示美國底層消費真實健康度（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ，HTTP 200）。

### SENT-3｜PANW／科技股財報（r/stocks）— 肯定資安與 AI 儲存動能但對軟體股估值審慎（無新進展）
- 討論內容與情緒：r/stocks 討論串肯定 PANW 平台化與 NGS ARR 成長，但整體對升息與 AI 高資本支出下的軟體股估值仍偏審慎（熱度自 11/18 升溫；情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-4｜UNH／管理式醫療（r/stocks）— CMS CRUSH 規則衝擊下偏悲觀觀望（無新進展）
- 討論內容與情緒：UNH 等醫療保險股受 CMS CRUSH 反詐欺規則影響連日承壓，散戶偏悲觀（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-5｜台股 11/19 跌 1,768 點破年線與盤後「限空令 2.0」（PTT 股板）— 熱議國安基金護盤漲幅全數吐回與 3.5% 限空令能否止血（更新）
- 討論內容與情緒：今日台股收跌 1,768.02 點（櫃買跌 7.22%）、吐回近期國安基金護盤漲幅且 20 檔千金股跌停，盤後金管會緊急宣布 11/20 起實施「當日跌 ≥3.5% 次日禁平盤下放空、盤中借券降至 1%」；PTT 股板盤中對斷頭與違約交割恐慌，盤後則兩極爭論限空令 2.0 是止跌訊號還是反而抽乾中小型股流動性，同步討論大摩對台積電 3,088 元看法與台幣尾盤竟由貶破 33 逆轉收升 32.942 元（情緒，非事實；https://www.pttweb.cc/bbs/Stock/M.1795048218.A.865 ，HTTP 200；https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，HTTP 200；https://www.pttweb.cc/bbs/Stock/M.1795058772.A.5C2 ，HTTP 200）。

---

### CODE-1｜wsb/data/calendar.py：第 71–72 行 `isinstance(datetime, date)` 成立導致 `date <= datetime` 拋出 `TypeError`，持股財報日曆可能整批被靜默略過
- 檔案路徑與行號：`wsb/data/calendar.py` 第 70–75 行（`_earnings()` 函式）。
- 那一行在做什麼：從 `yfinance.Ticker(t).calendar` 取出 `Earnings Date`，轉成 `date` 型別後與 `us_today()` 比對是否在未來 60 天內。
- 為什麼有問題：第 71 行寫 `d = d if isinstance(d, date) else datetime.fromisoformat(str(d)).date()`。在 Python 中 `datetime` 是 `date` 的子類別（`isinstance(datetime(...), date)` 永遠為 `True`）。只要 `yfinance` 回傳的是 `datetime.datetime` 或 `pandas.Timestamp` 物件，第 71 行就會保留原物件而不呼叫 `.date()`；緊接著第 72 行執行 `if us_today() <= d <= us_today() + timedelta(days=60):` 時，`date <= datetime` 會直接觸發 `TypeError: can't compare datetime.datetime to datetime.date`，並被第 74 行 `except Exception: continue` 靜默吃掉，使該持股的財報日期從行事曆消失。
- 建議怎麼改：將第 71 行改為先判斷 `isinstance(d, datetime)`（呼叫 `d.date()`），例如：`d = d.date() if isinstance(d, datetime) else (d if isinstance(d, date) else datetime.fromisoformat(str(d)).date())`。
- 確定度：高。

### CODE-2｜wsb/data/fedwatch.py：第 104 行使用台北本機 `date.today()` 而非 `us_today()`，每月 1 日上午（台北 00:00–13:00）抓聯邦基金期貨會漏掉美國當月合約
- 檔案路徑與行號：`wsb/data/fedwatch.py` 第 104 行（`FedWatch.refresh()` 函式），對照第 179–180 行（`view()`）。
- 那一行在做什麼：計算接下來 10 個月的 CBOT 30 天聯邦基金期貨代碼（`ZQ...CBT`），下載最新報價並覆寫 `self.quotes`。
- 為什麼有問題：第 180 行 `view()` 已註明 `today = us_today().isoformat()`，但第 104 行卻寫 `months_ahead(date.today())`（以台北主機日期為準）。在每月 1 日台北時間清晨至美東午夜過後（約 12–13 小時，此時美東仍屬上個月最後一天），`date.today()` 已經跨入下個月，導致 `refresh()` 不抓美國當月 `ZQ` 合約並直接覆寫 `self.quotes`，使該月若剛好有期末會議或需要當月報價時缺失一整欄資料（這不是往回抓好幾天的起始日，而是往前滾動月份造成當月合約被覆蓋消失）。
- 建議怎麼改：改用 `from .econcal import us_today`，將第 104 行 `date.today()` 改為 `us_today()`（第 137 行清理兩年前快照的 `cutoff` 亦建議一致改用 `us_today()`）。
- 確定度：高。

### CODE-3｜wsb/data/fedwatch.py：第 54–60 行若「月末最後 7 天開會」且「次月也有會議」時會落入除以 1～7 天的雜訊分支
- 檔案路徑與行號：`wsb/data/fedwatch.py` 第 54–60 行（`implied()` 函式）。
- 那一行在做什麼：依 CME FedWatch 規則推算每次 FOMC 會後隱含利率；當會議落在該月最後 7 天（`N - x.day < 8`）時，第 57 行註解明確寫明應避免用本月合約除以 `(N - d)` 以免放大報價雜訊。
- 為什麼有問題：第 54 行限制 `nxt not in mdays` 才跳轉次月，第 56 行又只檢查 `nxt not in fut`。如果未來某次排程出現「月末 7 天內開會、且次月剛好也有 FOMC 會議（`nxt in mdays` 且 `nxt in fut`）」的情況，前兩個條件都不成立，程式會落入第 58 行 `elif ym in fut and N - x.day > 0:`，直接執行第 59 行除以 1～7 天剩餘天數的運算——與第 57 行想防止的雜訊放大相違背。
- 建議怎麼改：將第 56 行改為 `elif N - x.day < 8:`（只要在月末最後 7 天且無法用無會議的次月合約推算，就一律設 `r_a = None` 停止外推，不落入短天數除法）。
- 確定度：中（實務上 FOMC 較少連兩個月於月末相鄰開會，但屬於條件缺口）。

（備註：本小時批次 `i % 24 == 16` 共 12 檔，其餘 9 檔 `tools/sec_push.py`、`tools/site_estrev.py`、`tools/site_longhist.py`、`tools/site_transmission.py`、`wsb/analytics/breadth.py`、`wsb/analytics/factors.py`、`wsb/analytics/premarket.py`、`wsb/analytics/techearn.py`、`wsb/data/news_digest.py`、`wsb/data/tw_fuel.py`（連同前述 3 個問題以外段落）皆已逐行讀完；其中 `wsb/data/tw_fuel.py` 第 57 行的 `d["try_each"]` 已交叉確認由 `wsb/data/freshness.py` 的 `due()` 預先初始化，無 `KeyError` 風險；其餘小細節如 `sec_push.py` 第 557 行 `market_now` 未防 `chg == -100`、第 652 行 `yen_jump` 以 UTC 日期作去重鍵則屬極端或無害，不予濫報。）

---

其他今天的大事：
- 台股 11/19 收盤重挫 **1,768.02 點（-4.40%）至 38,426.89 點**（盤中一度跌 1,935.21 點下探 38,259.7 點，櫃買指數跌 **-7.22%**），台積電收 2,100 元（-3.45%）、聯發科收 3,720 元（-5.58%）、鴻海收 220.5 元（-0.23%）；三大法人現貨賣超 **461.03 億元（外資 -243.12 億、自營商 -233.03 億、投信 +15.13 億）**，期貨合計淨空單擴大至 **-8,883 口**；金管會盤後緊急宣布自 **11/20 起升級 3.5% 限空令**；新台幣 16:00 則由盤中貶破 33 元（33.040）逆轉收在 **32.942 元（升值 0.5 分）**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190200.aspx ；https://www.cna.com.tw/news/afe/202611190149.aspx ；新台幣收盤與櫃買指數來源見聯合報搜尋摘要）。
- 亞歐股市 11/19 表現分歧：日經 225 收漲 **+0.71%**（59,444.21 點）、韓股 KOSPI 收漲 **+1.39%**（5,137.89 點）、港股恆生收跌 **-1.95%**（22,841.62 點）；歐股 16:00 開盤小幅反彈（DAX 約 +0.4%～0.5%、CAC 40 約 +0.4%～0.6%），但 ECB 金融穩定報告警告法國主權債利差擴大且拒出手護盤（搜尋摘要）。
- 網易（NTES）11/19 盤前搶先公布 Q3 2026 財報，淨營收人民幣 279 億元（年減 1.8%）、Non-GAAP 淨利人民幣 92 億元並調高季股息至每 ADS 0.585 美元；今晚（11/19）20:00–22:30 沃爾瑪（WMT）、阿里巴巴（BABA）、拼多多（PDD）將陸續公布財報，且 Anthropic（ANT，定價 83 美元、估值 1.5 兆美元）正式在納斯達克掛牌（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://www.nasdaq.com/press-release/alibaba-group-will-announce-september-quarter-2026-results-november-19-2026-2026-11 ）。
- 深圳 APEC 峰會 11/19 舉行「川習會（30 對 30 協議）」與首次「美中俄三方峰會」（https://www.cna.com.tw/news/aopl/202611193005.aspx ；https://www.cna.com.tw/news/acn/202611190062.aspx ）；川普受訪稱與黃仁勳有染女子正遭美政府調查是否涉中國情報與晶片走私（https://www.cna.com.tw/news/aopl/202611193003.aspx ）；BIS `2026-23529` 遠端算力規則與 HHS HIPAA 最終規則同日刊登聯邦公報（https://public-inspection.federalregister.gov/2026-23529.pdf ）。
- 日本央行總裁植田和男 11/19 國會重申升息決心，同日凌晨熊本 M5.7 地震初步未傳出台積電 JASM 廠重大停工（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ；https://www.chinadailyasia.com/hk/article/642914 ）；印度強氣旋「阿克萬」撤離人數升至逾 10 萬人（https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ）。

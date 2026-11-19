台北時間 2026-11-19 13:45

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）、整體 PCE 年增率為 **3.6%**（月增 **0.5%**），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，台北時間 2026-10-29，HTTP 200 確認）。
- 事實：之所以 9 月核心 PCE（3.1%）反過來高於核心 CPI（2.6%），根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 高於核心 CPI 的倒掛現象（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。
- 事實：檢視本站即時網頁《財經日曆》分頁的 `PCE 物價（聯準會最重視的通膨）` 卡片（11/19 13:27 線上版確認仍在），其實已明確寫出「核心 PCE 月增 前值 `0.3%`、核心 PCE 年增 前值 `3.1%`、PCE 月增 前值 `0.5%`、PCE 年增 前值 `3.6%`」，而總覽的估算卡片亦估 10 月核心 PCE 月增約 `+0.26%`、年增約 `+3.2%`，顯示 9 月基準值已在站內日曆卡片上，只是沒有串接到 `forecast.json`。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照（無新進展）
- 事實：歐洲央行（ECB）2026 年 11 月《金融穩定評估》Box 3（"The debt financing of AI and its implications for financial stability"）明確列出美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 共識（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，台北時間 2026-11-18，HTTP 200 確認）。
- 事實：ECB Box 3 正文對自由現金流的口徑為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（僅以**資本支出超過營運現金流**作為表層口徑，未把尚未起租的表外租賃算進單季現金流）；同時於圖表 A 與註腳 6 依美國會計準則 **ASC 842** 單獨指出，已簽約但資產尚未投入使用的租賃與算力承諾在起租前不計入資產負債表負債，這類表外承諾合計已逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200 確認）。
- 事實：四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與租賃口徑落差如下：
  - Meta（Q3 2026）：營運現金流 **$32.79B**，資本支出（含融資租賃本金償還）**$34.91B**，自報自由現金流為 **-$2.12B（轉負）**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）。
  - Alphabet（Q3 2026）：營運現金流 **$42.29B**（$42,290M），現金 PP&E 購置（不含融資租賃）**$51.36B**（$51,355M），自報自由現金流為 **-$9.07B（-$9,065M，轉負，含 52 億美元歐盟罰款支付）**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）。
  - Amazon（Q3 2026／TTM）：單季營運現金流 **$42.42B**、單季淨 PP&E 購置 **$75.93B**（隱含單季 **-$33.51B**），公司自報 **TTM 自由現金流 -$42.36B（-$42,357M，轉負）**，該口徑僅扣現金淨 PP&E、未扣額外揭露之新簽融資租賃資產（Q3 單季 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）。
  - Microsoft（Q1 FY27）：營運現金流 **$58.02B**，現金 PP&E 資本支出 **$39.37B**，自報自由現金流為 **+$18.6B（仍為正值，年減 27%）**；若計入新起租之融資租賃，總資本支出達 **$45.2B**，扣除後仍餘約 +$12.8B，印證 ECB 精準寫 `"most"` 而非全部（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（附 claude_notes.md 與 forecast.json 實例）
- 推理：檢視 `claude_notes.md` 與 `forecast.json`，最常「下太快」的是以下兩種思考捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：例如 `claude_notes.md` 第 14 行在還沒核對 `bea.gov` 或本站日曆卡片前值的情況下，因為「核心 PCE 通常比核心 CPI 低」，就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推 10 月區間；以及 `forecast.json` 第 65–73 行先前曾用單一 `BAMLH0A0HYM2`（3.43%）得出「信用市場還沒出現壓力」（本輪你已修正）。
  2. **把「我的新聞關鍵字沒對上時間」直接寫成「原因不明／沒有消息」**：例如 `forecast.json` 第 3 行寫「黃金、銅、油價同一天一起跌，主因我沒找到時間對得上的消息」，但同一檔案第 150 行自己就寫了「金銀跌到 14 個月低點，聯準會官員偏鷹讓美元走強」，且忽略 11/18 EIA 原油與汽油大幅累庫及雪佛龍除息日；11/19 10:33 緊急加班語音稿截至 13:27 仍保留「開盤前到底是什麼事（能源股跳空），我目前沒有找到」，建議把除息行事曆（如 CVX 11/18 除息）與產經日曆串進新聞原因比對流程。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標（無新進展）
- 推理：若今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，傳導先後順序如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：負債比高、高度仰賴把大模型算力長約拿去抵押融資。隔天（11/20）可驗證指標：`CRWV`、`NBIS` 相對 `QQQ` 的開盤超額跌幅，及新雲端無擔保債二級殖利率走勢。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸**：ANT 募資 813.1 億美元、估值 1.5 兆美元，若破發將壓縮 OpenAI 與晚期 AI 獨角獸 IPO 窗口。隔天可驗證指標：`ARCC`、`BIZD`、`BX`、`APO` 股價與承銷商是否啟動護盤機制（stabilizing bid）之報導。
  3. **最後且幅度較小：出資的晶片商與雲端股東（NVDA、AMD、GOOGL、AMZN）**：主要承受公允價值重估回吐，但只要 RPO 與資料中心交貨未取消，本業現金流不致立即受損。隔天可驗證指標：`NVDA`、`AVGO`、`AMD` 相對 `^SOX` 強弱與 `GOOGL`／`AMZN` 次日盤中選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態（13:45 補充台股收盤與最新外部資訊）
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意**，ECB Box 3 佐證多家一線雲端商 FCF 轉負、表外承諾逾 4 兆美元，但尚未演變為連鎖違約；另美國財政部 11/18 公布 9 月 TIC 外資淨流入仍達 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ）。惟同時留意新加坡與馬來西亞就美國 BIS `2026-23529` 遠端算力管制展開緊急釐清（https://www.channelnewsasia.com/singapore/singapore-us-semiconductor-mddi-josephine-teo-6560761 ），東南亞資料中心融資與租賃審查已成為新的外部變數。
  2. **主線 2（輝達治理風波 vs 出口調查）— 同意雙方收斂**（45%–50% vs 55%–60%）。今日中央社再報導輝達新任董事長瓊斯（Harvey Jones）在員工大會重申董事會因黃仁勳個人行為及「缺乏坦誠」接受辭呈、**不會讓其回任**，而代理執行長克瑞斯（Colette Kress）預告提前於 12 月加薪與增發股票獎勵穩住人才，且台積電副總張曉強公開表態深化合作（https://www.cna.com.tw/news/aopl/202611190029.aspx ；https://money.udn.com/money/story/123398/9888693 ；https://www.ctee.com.tw/news/20261119700076-439901 ，HTTP 200 確認）。這更傾向公司治理切割後的內部穩盤，後續仍看 10-Q Legal Proceedings 章節。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，補充 11/19 台股收盤破底與證交所發聲**：今日台股 13:30 收盤大跌 **1,768.02 點（-4.40%）** 至 **38,426.89 點**（盤中最低 38,259.70 點，櫃買 13:29 重挫 7.32% 至 285.03 點），本週累計跌幅逾 10%，台灣證交所已公開表態若出現非理性賣壓或異常波動將採必要措施維持秩序（https://news.cnyes.com/news/id/6667459 ，HTTP 200）；同時紐約聯準銀行總裁 John Williams 反對 12 月一次升息 0.50%（https://www.chosun.com/english/market-money-en/20261119/3ZAB4T3MGVF4HLNUXPSHRHLNCI/ ）。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意**，11/19 伊朗軍方證實荷莫茲海峽東側 3 艘油輪觸及水雷起火失能、且 ADNOC 船隻遇襲 11 傷 1 失蹤（https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906 ），支持你對封鎖升級尾部風險的重視；但我仍因 EIA 庫存大增與強美元維持 **55%**。
  5. **主線 5（「風險升級」劇本 33% vs 40%）— 同意方向一致**，差距僅 7 個百分點。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題（新增第 3 題補足深圳川習會變數）
- 1. 檢視今天（11/19 13:27）線上版《財經日曆》的 `PCE 物價（聯準會最重視的通膨）` 卡片，其實**已經明確顯示核心 PCE 年增前值 `3.1%`、核心 PCE 月增前值 `0.3%`**；為什麼 `forecast.json` 卻仍寫「9 月核心 PCE 數字：查無」？是預測腳本沒有讀取該表格，還是產出順序有落差？
- 2. 今日（11/19）紐約聯準銀行總裁 John Williams 公開表態不認為 12 月需要一次升息 0.50%，正好與理事 Waller 的 2 碼說法對撞；再加上荷莫茲海峽 3 艘油輪觸水雷與台股今日收跌 1,768 點至 38,426.89 點、逾 200 檔跌停，你下一輪會如何調整「聯準會升息幅度」與「風險升級」的機率？
- 3. 今日中午 13:24 深圳「川習會」正式登場（盧比歐、貝森特、盧特尼克、葛里爾全數出席）且緊接舉行美中俄三方峰會，今晚（20:00–22:30）又同時碰上 WMT／BABA／PDD 財報與 Anthropic 掛牌，若明早美股與跨資產劇烈震盪，你打算怎麼在站上拆解「川習／美中俄外交訊號」、「ANT 掛牌帶動的 AI 資金輪動」與「利率／地緣事件」？

---

### WIDE-1｜荷莫茲海峽 11/19 驚傳 3 艘油輪觸及水雷起火失能，且 ADNOC 船隻遇襲 11 傷 1 失蹤（無新進展）
- 事實：土耳其國營安納杜魯新聞社（AA）與 CBS News 於台北時間 2026 年 11 月 19 日報導，伊朗軍方證實 **3 艘油輪在荷莫茲海峽東側觸及水雷並起火失能（disabled）**，伊朗稱該等船隻關閉導航系統並駛入禁航區；稍早阿聯阿布達比國家石油公司（ADNOC）亦證實一艘旗下船隻在海峽航行時遇襲，造成 **11 名船員受傷、1 人失蹤**，同時美伊在海峽周邊（包含美軍空襲葛希姆島與科威特、巴林攔截飛彈無人機）互襲升溫（https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906 ，台北時間 2026-11-19 10:34，HTTP 200 確認；https://www.cbsnews.com/live-updates/iran-war-us-gulf-retaliation-strikes-strait-of-hormuz/ ，HTTP 200 確認）。
- 推理：美股昨晚（11/18）全數聚焦美國 EIA 原油與汽油累庫，使油價大跌；但今日清晨出現**實質水雷致油輪起火失能**，性質已從「口頭封鎖／攔檢」升級為「航道物理毀損與水雷威脅」，若海運保險業全面停保或延後通航，短線原油與成品油裂解價差極易劇烈反彈並重新點燃二次通膨定價。
- 先影響資產：布蘭特原油／柴油裂解價差、油輪與海運戰爭險費率、航空與石化類股。

### WIDE-2｜APEC 深圳峰會 11/19 下午「川習會」正式登場、美方經貿國安團隊全員出席，緊接美中俄三方峰會（重大更新）
- 事實：中央社於台北時間 2026 年 11 月 19 日 13:24–13:30 報導，中美元首今年第三次「川習會」在深圳麒麟山莊正式登場，美方代表除川普總統外，國務卿盧比歐（Marco Rubio）、商務部長盧特尼克（Howard Lutnick）、財長貝森特（Scott Bessent）與貿易代表葛里爾（Jamieson Greer）均在席；稍早川普亦在 APEC 場邊與俄國總統普丁簡短會談，稱期待促成「好的開始」，會後將接續舉行美中俄三國元首峰會（https://www.cna.com.tw/news/acn/202611190138.aspx ，台北時間 2026-11-19 13:30，HTTP 200 確認；https://www.cna.com.tw/news/aopl/202611190121.aspx ，台北時間 2026-11-19 12:50，HTTP 200 確認）。
- 推理：商務部長（主管 BIS 出口管制）、財長（主管制裁與 TIC 資本）與貿易代表（主管 301 關稅）同時坐在川習會桌前，代表這不只是禮貌性會晤，而是直接涵蓋**關稅休兵、AI 晶片／遠端算力管制與俄烏停火框架**的實質談判；在美股開盤前若釋出公報或談判訊號，跨資產定價可能出現劇烈跳空。
- 先影響資產：USD/CNH、中概股（KWEB）、歐洲天然氣與國防股、全球半導體設備股。

### WIDE-3｜歐盟 11/18 達成「歐洲電網包裹」加速許可臨時協議，同時歐元區定價 ECB 升息 3 次且拒救法國債務（更新）
- 事實：歐盟理事會與歐洲議會於 2026 年 11 月 18 日清晨就「歐洲電網包裹（European Grids Package）」許可指令達成臨時政治協議，規定太陽能與併設儲能審批上限 **3 個月**、獨立儲能與電動車充電樁 **6 個月**、電網併網 **3 個月**（正當理由可延至 6 個月），並將強制與地方社區分享利益的再生能源門檻由 10 MW 降至 **7 MW**，各成員國須於 18 個月內完成國內立法（https://www.anews.com.tr/european-union/2026/11/18/eu-reaches-provisional-deal-to-fast-track-permits-for-renewable-energy-projects-electricity-grids ，台北時間 2026-11-18，HTTP 200 確認；https://euperspectives.eu/2026/11/eu-faster-permits-solar-grids-ev-chargers/ ，HTTP 200 確認）。
- 事實（債市無新進展）：受中東戰事推升能源成本影響，歐元區短期利率市場已完全定價 ECB 自今年 12 月起至 2027 年底前升息 3 次；ECB 在 11/18 金融穩定評估警告法國須靠財政改革與「市場紀律」約束，不應期待央行救市（https://www.globalbankingandfinance.com/euro-zone-yields-rise-traders-bet-three-ecb-hikes-late-2027/ ；https://www.globalbankingandfinance.com/markets-help-discipline-france-over-high-debt-ecb/ ）。
- 推理：歐洲一邊強推電網與儲能快速審批擺脫化石燃料進口脆弱度，一邊卻面臨能源通膨迫使 ECB 重啟升息並拒替法國公債兜底，歐洲工業用電轉型與主權信用利差正同時進入高波動期。
- 先影響資產：歐洲電網設備／變壓器廠、荷蘭 TTF 天然氣期貨、法德 10 年期公債利差、EUR/USD。

### WIDE-4｜歐盟反壟斷擬否決 Anglo American 巴西鎳鐵出售予中資 MMG，警告將直接關礦威脅歐洲供應鏈（新）
- 事實：路透社（經 Euronext Financial News 刊載）於 2026 年 11 月中旬報導，歐盟執委會反壟斷官員傾向否決英美資源集團（Anglo American）以 **5 億美元**將巴西鎳鐵業務（Barro Alto 與 Codemin 礦場）出售予中國五礦資源（MMG）的交易；Anglo American 執行長 Duncan Wanblad 致函 Acerinox、Aperam、Outokumpu 等歐洲主要不鏽鋼客戶警告，一旦遭否決公司不會重新談判，而是將兩座礦場轉入維護封存並以永久關閉為目標（https://live.euronext.com/en/financial-news/anglo-american-warns-customers-possible-ferronickel-supply-disruption-if-deal ，HTTP 200 確認）。
- 推理：美股尚未注意此案，但歐盟為防止中資掌握關鍵礦產而行使併購否決權，反過來可能觸發礦商直接退場關礦，引發歐洲不鏽鋼與特種合金原料實質斷鏈，同時加深巴西與歐盟的資源監管摩擦。
- 先影響資產：倫敦金屬交易所（LME）鎳價、歐洲不鏽鋼廠（Aperam、Outokumpu、Acerinox）、巴西股匯（EWZ / BRL）。

### WIDE-5｜美國會 USCC 11/19 年報示警未來 24 個月台海關鍵期；新加坡與美啟動 BIS 晶片轉運實務協商（更新）
- 事實：美國「美中經濟暨安全檢討委員會（USCC）」2026 年度國會報告台灣章節指出，**未來 24 個月**將形塑長期兩岸關係，若北京透過 11 月底台灣地方選舉與 2028 年大選評估政治脅迫效果不如預期，對台海採取隔離或封鎖的風險將提高（https://www.uscc.gov/sites/default/files/2026-11/2026_Annual_Report_to_Congress.pdf ，HTTP 200 確認；https://www.rti.org.tw/en/news?uid=3&pid=1052391 ，HTTP 200 確認）；同日新加坡數位發展及新聞部（MDDI）部長楊莉明（Josephine Teo）與美國 BIS 副部長 Jeffrey Kessler 會談後宣布，雙方同意針對受信任的新加坡用戶持續取得美國先進晶片技術展開實務安排跟進（https://www.channelnewsasia.com/singapore/singapore-us-semiconductor-mddi-josephine-teo-6560761 ，HTTP 200 確認）；另加拿大總理卡尼在深圳稱盼近期簽署加台貿易協議（https://www.cna.com.tw/news/aipl/202611190019.aspx ）。
- 推理：新加坡迅速與美方建立「可信賴用戶」豁免與追蹤機制，馬來西亞與泰國資料中心若跟進慢半拍，東南亞 AI 算力建設訂單可能重新向新加坡合規樞紐集中。
- 先影響資產：台股半導體權值股（2330 / TSM）、東南亞資料中心 REITs、新台幣（USD/TWD）、新加坡海峽時報指數。

---

### A｜今天的大動（對照 `/api/gemini_ask` 13:31 即時清單）

### PANW｜同意本站，Palo Alto Networks（PANW）Q1 FY27 財報全面優於預期、宣布 45 億美元併購 Applied Compute，且同日 Everpure（P）財報強勁共振（補充）
- 事實：同意本站。PANW 於美東 11 月 18 日盤後公布 Q1 FY27 財報，營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億美元），GAAP 淨利 **4.82 億美元**（每股 0.57 美元），次世代資安年經常性營收（NGS ARR）年增 **66%** 至 **97.3 億美元**；上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**（成長 26%–27%）、調整後 EPS 至 **4.26～4.30 美元**，並宣布以 **45 億美元**全股票收購開源權重 AI 模型後訓練／推論平台 **Applied Compute**（預計 FY27 Q3 完成交割，Applied Compute 共同創辦人兼 CEO Yash Patil 將出任 PANW 共同 AI 長），盤前／盤後漲 **+9.1%**（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19，HTTP 200 確認；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，台北時間 2026-11-19，HTTP 200 確認）。
- 本站漏掉的：本站引用 Yahoo 標題提及的 **Everpure（NYSE: P，原 Pure Storage）** 同於 11/18 盤後公布 Q3 FY27 財報大好——營收年增 **51%** 至約 **14.6 億美元**（新聞稿約 $1.5B）、調整後 EPS **0.86 美元**（優於預期 0.77 美元）並連三季上調全年指引至 **52.0 億～52.1 億美元**，顯示企業級 AI 資料儲存與資安同步獲得預算驗證；另有 KeyBanc 分析師 Eric Heath 近日將 PANW 評等由 Sector Weight 調升至 **Overweight**（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ，HTTP 200；https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200）。

### CRWD｜CrowdStrike（CRWD）受 PANW 財報驗證 AI 資安需求外溢帶動，疊加近期 Cantor Fitzgerald 調高看法（無新進展）
- 事實：CRWD 於美東 11 月 18 日盤後／盤前大漲 **+6.0%**，系同業 PANW 財報驗證企業 AI 資安需求強勁而出現板塊連動；近期 Cantor Fitzgerald 分析師 Jonathan Ruykhaver 維持 **Overweight** 並調高對 CRWD 的看法至 **$275**（原 $250）（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ；https://www.tikr.com/zh/blog/cantor-fitzgerald-raises-its-crowdstrike-target-to-275-is-it-still-too-low ）。
- 推理：CRWD 本身預計 12 月初才公布財報，11/18 盤後未有單獨公司公告（找不到來源），屬同業財報驗證後的資金外溢。

### CVX｜雪佛龍（CVX）受 11/18 除息每股 1.78 美元、EIA 原油與汽油庫存大增壓低油價，以及 50 億美元併購談判影響下跌 4.0%（無新進展）
- 事實：CVX 美東 11 月 18 日正規盤收跌約 **-4.0%**（$205.88，-3.95%），由三件事疊加：（1）11/18 為季股息 **每股 $1.78** 除息日（約佔跌幅 0.8 個百分點）；（2）EIA 公布上週美國原油庫存大增 **340 萬桶**（遠超預期）、汽油大增 **520 萬桶**，壓低 WTI 原油跌至 83.26 美元，能源板塊集體下挫；（3）傳接近以 **50 億美元**收購墨西哥灣深水油商 **Beacon Offshore Energy**（https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ；https://www.nationthailand.com/news/world/40073656 ；https://www.bicmagazine.com/industry/investment-banking/chevron-closes-in-on-5b-beacon-deal/ ）。
- 本站漏掉的：除技術性除息外，當天能源板塊（XLE、XOM、CNQ）同步重挫，屬宏觀庫存與油價事件驅動，而非雪佛龍單一公司利空。

### CNQ｜Canadian Natural Resources（CNQ）正規盤隨油價重挫跌 4.63%（$45.53），盤後／盤前 +3.2% 無新公告或報告（無新進展，找不到來源）
- 事實：CNQ 美東 11 月 18 日正規盤隨北美能源股重挫收跌 **4.63%**（$45.53，多倫多跌 4.06% 至 C$65.52），市場亦在消化其 11/16 宣布以 **25.3 億加元**收購 **Advantage Energy** 之現金支出（https://www.nationthailand.com/news/world/40073656 ；https://www.newsfilecorp.com/release/324091/Canadian-Natural-Resources-Limited-Enters-into-Agreement-to-Acquire-Advantage-Energy-Ltd ）。
- 事實（盤後／盤前 +3.2%）：經查公司公告、交易所與主流媒體，美東 11/18 盤後至今日美東深夜 **沒有任何 CNQ 新聞、財報或分析師調評**（找不到來源）。
- 推理：正規盤急跌近 5% 後盤前低流動性搓合出現 +3.2% 跳動，應屬美加掛牌價差或薄量回補，非基本面突發事件。

---

### AN｜AN-1：最近 3 小時內（台北 10:45–13:45）無新增美股分析師調評；保留本週已公開可查證報告（補充 SMCI）
- 事實：檢索最近 3 小時（台北 10:45–13:45／美東 11/18 21:45–11/19 00:45 深夜時段），AI 供應鏈與美國市值前 20 大公司並無新發布的券商評等調整（找不到來源）。
- 事實：本週已公開可查證之重要評等與信用展望調整包括：
  1. **Moody's Ratings（11/18）**：維持 **NVDA** Aa1 債信評等，但將展望由 **Positive 調降至 Stable**，點名黃仁勳驟然離職後的接班真空與美國政府調查風險（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ，台北時間 2026-11-19，HTTP 200）。
  2. **KeyBanc**：分析師 Eric Heath 將 **PANW** 由 Sector Weight 調升至 **Overweight**、價格看法調高至 **$380**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200）。
  3. **YR Research（11/18）**：將 **AAPL** 由 **Sell 調升至 Hold**（https://www.tradingview.com/news/seekingalpha:d985f509f094b:0-sa-analyst-upgrades-downgrades-nvda-aapl-smci-tsla/ ，台北時間 2026-11-19，HTTP 200）。
  4. **Raymond James（11/18 報導引述）**：維持對 **SMCI** 偏多評等並給予 **$65** 估值看法（對照 Susquehanna 維持 Negative 評等、看法 $18），多空極度分歧（https://247wallst.com/investing/2026/11/18/super-micro-computers-40-3-month-downturn-a-great-entry-point-says-this-wall-street-pro-who-predicts-165-returns/ ，HTTP 200）。
  - 另據多篇外媒彙整，Summit Insights 調降 NVDA（Buy → Hold）、Rothschild & Co Redburn 調降 AVGO（Buy → Neutral）、Bernstein（11/18）對 ORCL 壓力測試評論與 RBC（11/18）維持 MU Outperform，但相關單篇直連網址（Benzinga／Seeking Alpha／Investing）對外部自動抓取設 403 阻擋（單篇直連網址：找不到來源）。

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）正式刊登聯邦公報生效，新加坡與馬來西亞尋求釐清安排（更新）
- 事實：美國商務部工業安全局（BIS）暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢至 2027-01-19）。新規增訂 § 744.24 遠端存取終端用途管制，限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則（https://public-inspection.federalregister.gov/2026-23529.pdf ，HTTP 200；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ，HTTP 200；https://www.milbank.com/en/news/bis-issues-new-rule-restricting-remote-access-to-advanced-chips.html ，HTTP 200）。
- 事實（更新）：新加坡數位發展及新聞部（MDDI）部長楊莉明已與美國 BIS 副部長 Jeffrey Kessler 會談並同意跟進「受信任用戶」實務安排；馬來西亞亦正尋求釐清規範；專家指出東協中唯二未入列名單的越南與菲律賓短期難直接享轉單紅利，合規稽核仍為關鍵（https://www.channelnewsasia.com/singapore/singapore-us-semiconductor-mddi-josephine-teo-6560761 ，HTTP 200；https://www.cna.com.tw/news/afe/202611190022.aspx ，台北時間 2026-11-19 07:46，HTTP 200）。

### POL-2｜美國財政部公布 9 月 TIC 資本淨流入 2,610 億美元、OFAC 制裁伊朗網路與 CMS CRUSH 規則（無新進展）
- 事實：美國財政部於美東 11 月 18 日公布 2026 年 9 月國際資本流動報告（TIC），9 月外資淨流入美國金融市場合計達 **2,610 億美元**（其中私人外資淨流入 **2,670 億美元**、外國官方機構淨流出 **60 億美元**；外資淨買入美國長期證券 **1,867 億美元**、短期國庫券增加 **35 億美元**）（https://home.treasury.gov/news/press-releases/sb0693/ ，HTTP 200）。
- 事實：同日美國財政部 OFAC 宣布 **「Operation Economic Outcast」** 制裁真主黨與伊朗聖城軍黃金及現金網路（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 代表重申美國優先供應鏈韌性（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）；白宮發布亞洲經濟協議事實清單（https://www.whitehouse.gov/fact-sheets/2026/11/fact-sheet-president-donald-j-trump-secures-historic-economic-deals-for-american-workers-and-strengthens-americas-leadership-in-asia/ ）；CMS CRUSH 反詐欺提案（`2026-23461`）今日刊登聯邦公報進入 60 天意見徵詢（https://public-inspection.federalregister.gov/2026-23461.pdf ，HTTP 200）。

---

### TW-1｜台股 11/19 收盤大跌 1,768 點收 38,426.89 點、證交所表態必要時採穩定措施；11/18 違約交割 9 檔今日盤中全鎖跌停（重大更新）
- 事實：台股今日（11/19）早盤開在 40,145.73 點、衝高至 **40,315.53 點**後反轉急殺，高低震盪逾 **2,055 點**，盤中最低下探 **38,259.70 點**（上市櫃逾 200 檔亮燈跌停，一度多達 21 檔千金股觸及跌停），終場（13:30）加權指數收在 **38,426.89 點（較昨收 40,194.91 點大跌 1,768.02 點 / -4.40%）**；權值股**台積電（2330）**早盤最高 2,190 元、盤中低見 2,085 元，終場收在 **2,100.00 元（跌 75 元 / -3.45%）**；櫃買市場 13:29 亦重挫 **-7.32%（-22.52 點）至 285.03 點**。由於本週累計跌幅已超過 **10%**，台灣證交所今日公開表示，若市場出現非理性賣壓或異常波動，將採取必要措施維持交易秩序（https://news.cnyes.com/news/id/6667459 ，台北時間 2026-11-19 13:30，HTTP 200；https://news.cnyes.com/news/id/6667450 ，13:28，HTTP 200；https://news.cnyes.com/news/id/6667452 ，13:29，HTTP 200；https://money.udn.com/money/story/5607/9888592 ，HTTP 200；另證交所盤後官方統計總表 `MI_INDEX`、三大法人現貨買賣超及期交所台指期未平倉須待 15:00 後公布）。
- 事實：11 月 18 日（對應 11/16 台股大跌 2,635 點的 T+2 交割日）證交所及櫃買中心公告上市櫃共 **9 檔熱門 AI 股**達標重大違約交割（創意 9,453 萬元、華通 9,360.35 萬元、雙鴻 6,465.6 萬元、欣興 5,204 萬元、精材 4,001 萬元、穩懋 3,406 萬元、金像電 2,616 萬元、精測 1,186 萬元、金山電 1,001 萬元），合計 **4 億 2,694 萬 6,248 元**（整體上市櫃買賣合計違約總金額約 **9.64 億元**），而該 9 檔違約股今日盤中全數一度亮燈跌停鎖死（https://www.chinatimes.com/realtimenews/20261119002092-260410 ，台北時間 2026-11-19，HTTP 200；https://www.storm.mg/article/11182992 ，HTTP 200）。
- 事實：台北匯市新台幣兌美元今日以 **32.96 元**開盤、盤中低見 **33.04 元**，**午盤暫收 32.988 元（貶 4.1 分），成交金額 11.55 億美元**（央行 16:00 官方收盤價尚未產生）（https://www.cna.com.tw/news/afe/202611190098.aspx ，台北時間 2026-11-19 12:06，HTTP 200）。

### TW-2｜日月光今日宣布投資 2,489 億元建高雄仁武新廠；海龍離岸風電 2A 轉售綠電予台積電；台積電張曉強為輝達新團隊「站台」（重大更新）
- 事實（今日新訊）：**日月光投控（3711）**旗下日月光半導體今日（11/19）宣布，台灣福雷電子在高雄仁武產業園區舉行新廠動土典禮，規劃投資 **新台幣 2,489 億元**擴充 AI 高階測試產能，預計 **2028 至 2029 年分期完成**，未來 K 與 J 兩基地合計預估創造年營收約 1,173 億元與 3,300 個就業機會（https://www.cna.com.tw/news/afe/202611190122.aspx ，台北時間 2026-11-19 12:47，HTTP 200 確認）。另旗下**矽品**已於 11/18 與輝達簽署數十億美元多年期合作協議，目標 2029 年年中前將輝達專用先進封裝產能擴增至目前 3 倍（https://money.udn.com/money/story/5612/9885611 ，HTTP 200）。
- 事實（今日新訊）：**台積電（2330）**資深副總經理暨副共同營運長張曉強公開表態深化與輝達協作、為輝達新管理團隊「站台」；輝達 11/17 Q3 採購承諾已增至 **3,900 億美元**，點名**台積電、欣興、景碩、矽品、鴻海、Amkor 與三星電機**擴充晶圓、ABF 載板、先進封裝與系統製造產能，代理執行長克瑞斯亦於 11/18 員工大會預告提前於 12 月加薪與增發股票獎勵留才（https://www.ctee.com.tw/news/20261119700076-439901 ，台北時間 2026-11-19，HTTP 200；https://money.udn.com/money/story/123398/9888693 ，HTTP 200）。同日能源署證實**海龍離岸風電 2A 風場**終止台電躉購契約，改簽企業購售電合約（CPPA）將綠電轉售予**台積電**（https://www.cna.com.tw/news/afe/202611190102.aspx ，台北時間 2026-11-19 12:19，HTTP 200）。
- 事實（今日新訊）：**鴻海（2317）**斥資 **72.4 億日圓**（約新台幣 14.5 億元）全資收購日本 Sony 半導體車載相機模組事業，預計 2027 年 4 月底前完成（https://www.ctee.com.tw/news/20261119700316-439901 ，HTTP 200）；**偉詮電（2436）**因晶圓代工漲價確定明年初調漲產品售價，今年前 3 季 EPS 4.49 元（https://www.cna.com.tw/news/afe/202611190036.aspx ，HTTP 200）；**元太（8069）**11/18 晚間重訊公告資安異常（https://www.cna.com.tw/news/afe/202611180336.aspx ）。
- 傳聞（無新進展）：外媒轉述《工商時報》稱台積電依客戶資產負債表設 AI 信用額度、超額須預付現金，尚未獲公司官方證實（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ）。

### TW-3｜愛德萬 V93000 EXA Scale QX 與台韓出口數據（無新進展）
- 事實：愛德萬（Advantest）11 月發表 36 槽四卡籠架構 **V93000 EXA Scale QX** 測試系統鎖定高功耗 AI 晶片；韓國 11 月前 10 天出口年增 **111.9%**（半導體年增 **331.2%**），台灣 10 月出口年增 **58.9%** 至 **967.6 億美元**（https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ；https://cyprusshippingnews.com/2026/11/13/south-koreas-exports-surge-toward-1-trillion-as-chip-shipments-more-than-quadruple/ ）。

---

### EARN-WMT｜沃爾瑪（WMT）Q3 FY27 財報（今晚美東 11/19 07:00／台北 20:00，更新隱含波動）
- 事實：美東 **2026-11-19 07:00 財報、08:00 電話會議**（台北 **11/19 20:00／21:00**）；TradingView 彙整市場共識營收約 **1,872.5 億～1,873.8 億美元**（年增約 4.3%–5.4%）、調整後 EPS **0.64 美元**（公司上季財測為 EPS 0.62–0.64 美元、常數匯率淨銷售成長 3.0%–3.75%）；選擇權隱含波動 **±5.78%～±5.89%**（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ，HTTP 200；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，HTTP 200）。

### EARN-BABA｜阿里巴巴（BABA）Q2 FY27 財報（今晚美東 11/19 盤前／台北 20:00–21:00，無新進展）
- 事實：美東 **2026-11-19 盤前**（台北 **11/19 20:00–21:00**）；Barchart 彙整預期截至 9/30 季度營收約 **404.1 億～404.8 億美元**（年增約 8.9%–16%）、調整後 EPS 約 **1.56～1.71 美元**（本站日曆列 1.56 美元）（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ，HTTP 200）。

### EARN-PDD｜拼多多（PDD）Q3 2026 財報（今晚美東 11/19 盤前／台北 20:00–21:00，無新進展）
- 事實：美東 **2026-11-19 盤前**（台北 **11/19 20:00–21:00**，電話會議 07:30 ET）；TradingView 彙整市場共識預期營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS 約人民幣 **18.72～19.02 元**（約 **2.61～2.77 美元**，本站日曆列 2.61 美元）（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ，HTTP 200）。

### EARN-INTU / ROST / GAP / WSM｜今日（11/19）美東盤前與盤後其餘財報（無新進展）
- 事實：
  - **WSM（盤前／台北 11/19 20:00）**：TradingView 彙整共識營收約 **19.8 億～20.0 億美元**、EPS **2.19 美元**（https://www.tradingview.com/news/tradingview:5796c7c550438:0-wsm-q3-26-earnings-eps-estimate-is-2-19-usd/ ，HTTP 200）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收約 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（公司原財測 2.44–2.48 美元），選擇權隱含波動約 ±8.9%–10.5%（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ，HTTP 200）。
  - **ROST（盤後／台北 11/20 05:00）**：Zacks／TradingView 彙整共識營收約 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ，HTTP 200）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收約 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（公司原財測淨銷售成長 1.5%–2.5%）（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ，HTTP 200）。

### EARN-HPE / ZM / BBY / BURL / DKS / ADI / MDT / DELL / HPQ / ADSK / WDAY / ZS / DE｜11/23–11/25 財報（補齊 HPE、DELL、WDAY TradingView 單篇連結）
- 事實：
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（本站日曆列 1.17，公司財測 1.20–1.30；選擇權波動 ±9.7%，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ，HTTP 200 確認；https://247wallst.com/investing/2026/11/09/dell-and-hpe-were-ai-winners-until-the-selloff-can-earnings-put-them-back-on-track/ ）；**ZM** 市場預期 11/23 盤後公布，共識營收 **12.8 億美元**、EPS **1.49 美元**（單篇新聞直連網址：找不到來源）。
  - **11/24 盤前（台北 11/24 21:00）**：**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**（https://www.tradingview.com/news/tradingview:6917007d5e261:0-burl-q3-26-earnings-revenue-estimate-is-2-97b-usd/ ，HTTP 200）；**DKS** 共識營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ，HTTP 200）；**ADI** 共識營收 **43.2 億美元**、EPS **3.89–3.92 美元**（本站隱含波動 ±8.09%）；**MDT** 共識營收 **94.6 億～94.8 億美元**、EPS **1.33–1.34 美元**；**BBY** 共識營收 **98.8 億～98.9 億美元**、EPS **1.49 美元**（ADI／MDT／BBY 單篇直連新聞網址：找不到來源）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億～492.5 億美元**（公司財測約 490 億）、調整後 EPS **6.41–6.60 美元**（本站列 6.41，隱含波動 ±14.85%，https://www.tradingview.com/news/tradingview:e525c4bdcb809:0-dell-q3-26-earnings-revenue-estimate-is-49-25b-usd/ ，HTTP 200 確認）；**WDAY** 共識營收 **26.9 億美元**、EPS **2.75 美元**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ，HTTP 200 確認）；**HPQ** 共識營收 **153.0 億～155.8 億美元**、EPS **0.72–0.76 美元**；**ADSK** 共識營收 **21.3 億美元**、EPS **2.91–3.07 美元**；**ZS** 共識營收 **9.35 億～9.39 億美元**（公司財測）、EPS **1.00 美元**（HPQ／ADSK／ZS 單篇直連新聞網址：找不到來源）。
  - **11/25 盤前（台北 11/25 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（本站隱含波動 ±7.23%，https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ，HTTP 200）。

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ，HTTP 200）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（強烈偏升息，無新進展）
- 事實：Waller 於 11/18 受訪指出聯準會可能需要「shock people」壓抑 3% 通膨預期固著，12/8–9 會議應考慮一次升息 50 基點（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ，HTTP 200）。

### FED-3｜聯準會理事 Michael S. Barr（偏升息）與紐約聯準銀行總裁 John Williams（明確反對一次升息 2 碼，無新進展）
- 事實：聯準會理事 Barr 11/18 在紐約聯準銀行演說指出，通膨仍過高，若經濟按預期演進適合進一步升息（偏升息）（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ，HTTP 200）。
- 事實：紐約聯準銀行總裁 John Williams 在 Axios BFD Summit 舞台對談（朝鮮日報英文版 11/19 報導）明確反對 12 月一次升息 0.50% 的大幅動作，表示 `"I don't see a need for dramatic action right now"`，強調雖然通膨仍高於 2% 需要維持緊縮立場，但就業市場穩健且過去數月政策正在奏效（偏漸進升息、反對 2 碼）（https://www.chosun.com/english/market-money-en/2026/11/19/3ZAB4T3MGVF4HLNUXPSHRHLNCI/ ，台北時間 2026-11-19，HTTP 200）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼約 90%–95%、升息 2 碼約 5%–10%（無新進展）
- 事實：聯邦基金期貨幾乎完全定價 12/9 升息 1 碼（約 90%–95%），升息 2 碼約 5%–10%，暫停升息已完全被定價排除（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ，HTTP 200）。

---

### CALL-PANW｜Palo Alto Networks（PANW）Q1 FY27 法說會：NGS ARR 年增 66%、斥資 45 億美元併購 Applied Compute 搶進企業混合 AI 安全（補充官方原話）
- 事實：PANW 執行長 Nikesh Arora、財務長 Dipak Golechha 與技術長 Lee Klarich 於美東 11/18 盤後召開 Q1 FY27 電話會議，強調企業正轉向「開源與閉源混合 AI」且安全防護正延伸至「token flow」，旗下 Prisma AIRS ARR 已近 **1.7 億美元**（逾 1,000 家客戶），本季新增約 170 筆平台化大單並宣布以 **45 億美元**全股票併購 Applied Compute（https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，HTTP 200 確認）。
- 原話（CEO Nikesh Arora）：`"Every enterprise is going to run a mix of open and closed models, and every one of those models needs to be secured. Applied Compute has built the best post-training and inference platform we've seen, and its research team is exceptional."`

### CALL-P｜Everpure（NYSE: P，原 Pure Storage）Q3 FY27 法說會：營收年增 51%、連三季上調全年財測（無新進展）
- 事實：Everpure（NYSE: P）於美東 11 月 18 日盤後公布 Q3 FY27 財報並召開電話會議，營收年增 **51%** 至約 **14.6 億美元**（新聞稿約 $1.5B）、Non-GAAP 營業利益年增 **76%** 至 **3.45 億美元**、調整後 EPS **0.86 美元**，並連三季上調 FY27 全年營收財測至 **52.0 億～52.1 億美元**（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ，HTTP 200）。
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

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets / r/stocks）— 今晚掛牌在即，懷疑「退出流動性」與討論 Claude 定價影響交錯（更新）
- 討論內容與情緒：r/wallstreetbets（`What Are Your Moves Tomorrow, November 19, 2026` 主討論串熱度自 11/18–19 急升）與 r/stocks 對定價 83 美元、募資 813 億美元的 ANT IPO 兩極分化，一面熱議史上最大掛牌是否引爆賭盤，一面普遍警覺龐大算力承諾恐讓散戶成為早期創投與避險基金的「退出流動性」，並擔憂上市後對產品定價與使用額度的影響（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xtuclv/nasdaq_confirms_anthropics_shares_will_begin/ ）。

### SENT-2｜NVDA（r/wallstreetbets）— 財報大好卻走弱，社群嘲諷「沒有驚喜就是利空」與接班風波（無新進展）
- 討論內容與情緒：11/18 財報達標但股價回跌，r/wallstreetbets 討論串混雜對科技股連月回檔的疲勞感與「nothing burger」嘲諷，並熱議輝達 100 億美元參與 Anthropic 股份與管理層風波（熱度自 11/17–18 升溫；情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xyw3ym/what_are_your_moves_tomorrow_november_18_2026/ ）。

### SENT-3｜PANW／科技股財報（r/stocks）— 肯定資安與 AI 儲存動能但對軟體股估值審慎（無新進展）
- 討論內容與情緒：r/stocks 討論串肯定 PANW 平台化與 NGS ARR 成長，但整體對升息與 AI 高資本支出下的軟體股估值仍偏審慎（熱度自 11/18 升溫；情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-4｜UNH／管理式醫療（r/stocks）— CMS CRUSH 規則衝擊下偏悲觀觀望（無新進展）
- 討論內容與情緒：UNH 等醫療保險股受 CMS CRUSH 反詐欺規則影響連日承壓，散戶偏悲觀（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-5｜台股 11/19 收盤大跌 1,768 點至 38,426.89 點與千金跌停潮（PTT 股板）— 「輝達接班＋Fed 鷹派＋AI 監管」三空恐慌擴散（重大更新）
- 討論內容與情緒：今日（11/19）台股盤中最低殺至 38,259.70 點、上市櫃逾 200 檔跌停（包含昨日爆出 4.269 億元違約交割的 9 檔 AI 概念股盤中全數一度亮燈跌停），PTT 股板 11/19 湧現大量恐慌討論與「公園客滿／違約交割潮」情緒，同步熱議「三大法人與大摩維持台積電（2330）看法」（熱度自 11/18–19 急升；情緒，非事實；https://www.pttweb.cc/bbs/Stock/M.1795058772.A.5C2 ，HTTP 200 確認；https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，HTTP 200 確認；https://www.pttweb.cc/bbs/Stock/M.1794981623.A.7D5 ）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，HTTP 200 確認）。
- 事實：核心 PCE（3.1%）高於核心 CPI（2.6%）之結構主因，係 2026 年住房／房租通膨降溫拉低權重較大的 CPI，而醫療服務、金融與軟體科技服務權重在 PCE 籃子較高且價格較黏著（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。

### TASK-B2｜11/19 台股收盤大跌 1,768.02 點收在 38,426.89 點、台積電收 2,100 元；三大法人現貨／期貨與央行新台幣收盤價待 15:00／16:00 後公布（更新）
- 事實（11/19 13:30 台股收盤與時間說明）：今日集中市場開在 40,145.73 點、高見 40,315.53 點、低探 38,259.70 點，**終場收在 38,426.89 點（大跌 1,768.02 點 / -4.40%）**，權值股台積電（2330）收 **2,100.00 元（-3.45%）**；證交所與新聞中心速報顯示 13:28 指數為 38,347.67 點（-4.6%）、櫃買 13:29 為 285.03 點（-7.32%），證交所並於 13:30 聲明本週累計跌幅逾 10%、必要時將採穩定措施（https://news.cnyes.com/news/id/6667459 ，HTTP 200；https://news.cnyes.com/news/id/6667450 ，HTTP 200；https://news.cnyes.com/news/id/6667452 ，HTTP 200）。
- 事實（未公布時段與最新可得）：截至 **台北時間 2026-11-19 13:45**，證交所 11/19 `MI_INDEX` 總表、三大法人現貨買賣超及期交所三大法人台指期未平倉須待 **今日 15:00 後**公布，台北匯市尚未收盤（16:00 收盤），目前最新為 **午盤暫收 32.988 元（貶 4.1 分，成交 11.55 億美元）**（https://www.cna.com.tw/news/afe/202611190098.aspx ，12:06，HTTP 200）。
- 事實（11/18 官方收盤對照）：加權指數收 **40,194.91 點（+102.80 點 / +0.26%）**；外資現貨賣超 **765.64 億元**；期交所三大法人台指期淨部位合計 **-7,322 口**（外資 -99,438 口、投信 +93,573 口、自營商 -1,457 口）；新台幣 11/18 收 **32.947 元**（https://www.cna.com.tw/news/afe/202611180304.aspx ，HTTP 200）。

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；保留掛牌前夕關聯股收盤表現（無新進展）
- 事實：Anthropic（代號 **ANT**）已定價 **每股 83.00 美元**（發行 9.8 億股、IPO 募資 **813.1 億美元**、完全稀釋估值約 **1.5 兆美元**），將於 **美東 2026-11-19 09:30（台北 11/19 22:30）** 正式掛牌；截至台北時間 13:45 美股尚未開盤，首日開盤價、收盤價與成交量將於明早 05:00 收盤後產生（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，HTTP 200；https://w.media/anthropic-ipo-priced-at-us-83-per-share-valuation-increases-to-us-1-5-trillion/ ，HTTP 200）。
- 事實：掛牌前夕美東 11/18 收盤，**CoreWeave（CRWV）跌 4.13%、IREN 跌 3.61%、Nebius（NBIS）小漲 0.87%、Oracle（ORCL）大致持平**；同日 **NVDA 收跌約 2.9%**，**AVGO、AMD 上漲約 4%–5%**（https://247wallst.com/investing/2026/11/18/coreweave-falls-5-despite-nvidia-sticking-to-its-financing-commitments-nebius-dips-oracle-holds-steady/ ，HTTP 200）。

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字（無新進展）
- 事實：ECB 11/18《金融穩定評估》Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（基於 LSEG 10/26 共識），指多數美國超大規模雲端業者 2026 年自由現金流因 AI 資本支出大於營運現金流而轉負（表層 FCF 口徑未納入未起租的表外租賃；表外承諾逾 4 兆美元係於圖表 A 與註腳 6 依 ASC 842 單獨揭露）（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200）。
- 事實：四巨頭截至 2026-09-30 最新一季自報實際數字如下：Meta（Q3 2026）OCF $32.79B − CapEx（含融資租賃本金）$34.91B = **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）；Alphabet（Q3 2026）OCF $42.29B − 現金 PP&E $51.36B = **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）；Amazon（Q3 2026／TTM）Q3 單季 OCF $42.42B、淨現金 PP&E $75.93B（單季隱含 -$33.51B）、自報 **TTM FCF -$42.36B**（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）；Microsoft（Q1 FY27）OCF $58.02B − 現金 PP&E $39.37B = **+$18.6B（仍為正；計入新起租融資租賃總資本支出 $45.2B 後仍約 +$12.8B）**（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### TASK-B5｜WMT、BABA、PDD 今晚 20:00–21:00 才公布 11/19 財報；附上最新共識（含來源名稱）、上季指引與關稅／消費原話（無新進展）
- 事實：三家均為 **美東 11/19 盤前（台北時間今晚 11/19 20:00–21:00）** 公布，截至台北 13:45 尚未發布實際財報。
- 事實（沃爾瑪 WMT，Q3 FY27）：TradingView 彙整市場共識營收 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（公司上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）；執行長 John Furner 對關稅退稅與消費者壓力的原話為 `"Customers are feeling some pressure, so we're proud of our investments... We'll do everything we can to keep prices as low as we can for customers throughout the rest of the year."`（https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ；https://www.businessinsider.com/walmart-using-tariff-refund-price-cuts-customer-experience-sales-2026-8 ）。
- 事實（阿里巴巴 BABA，Q2 FY27）：Barchart 彙整共識營收約 **404.1 億～404.8 億美元**（年增約 8.9%–16%）、調整後 EPS **1.56～1.71 美元**，市場聚焦阿里雲 AI 資本支出與中國消費補貼戰（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ）。
- 事實（拼多多 PDD，Q3 2026）：TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS **2.61～2.77 美元**，市場聚焦跨境關稅與小額免稅新規對 Temu 利潤率的影響（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ）。

---

### NEXT-1｜事件：11/19 台股收跌 1,768 點（9 檔違約 AI 股盤中全鎖跌停）＋日月光 2,489 億高雄擴廠＋BIS 新規生效（更新）
- 推理：
  - 最先受影響的資產：台灣高融資中小型電子股（櫃買跌逾 7%）、USD/TWD（午盤 32.988、盤中見 33.04）、以及東南亞（新加坡、馬來西亞、泰國、印尼）資料中心租賃與算力合約。
  - 傳導路徑：一方面，台股週跌幅逾 10% 疊加 11/18 爆出 9 檔 AI 股達標違約交割 4.269 億元，引發今日斷頭連鎖賣壓從 PCB／散熱／ASIC 外溢至權值股與塑化龍頭（南亞一度跌停）；另一方面，BIS `2026-23529` 今日生效且新加坡率先與美方展開「可信賴用戶」實務安排，跨國算力客戶與高階測試訂單將更向具備合規能力與本地封測聚落（如日月光今日投入 2,489 億元建高雄仁武 AI 測試新廠）集中：
    - 美股：**NVDA、ORCL、CRWV、SMCI、EQIX**（東南亞機房合規成本與算力租賃審核拉長）。
    - 台股：**台積電 (2330)、日月光投控 (3711)、創意 (3443)、雙鴻 (3324)、華通 (2313)**（短期斷頭洗籌碼 vs 長期高階封測在台集中度上升）。
  - 大家還沒注意到的間接受害者：**台灣中小型券商的融資斷頭追繳與自營權證避險損益**——連續兩波高價 AI 股跌停鎖死導致融資戶賣不掉、且當沖大戶違約交割（單日合計近 10 億買賣總額），若下週未能快速止跌，下季台灣獨立／中小型券商財報將面臨顯著呆帳提存與避險滑價虧損（可從今日報導之整體違約金額攀升佐證：https://www.storm.mg/article/11182992 ）。

### NEXT-2｜事件：APEC 深圳「川習會」經貿國安團隊全員登場＋美中俄三方峰會 vs 荷莫茲海峽 3 油輪觸水雷（更新）
- 推理：
  - 最先受影響的資產：離岸人民幣（USD/CNH）、布蘭特原油期貨與柴油裂解價差、歐洲 TTF 天然氣與德國公債殖利率。
  - 傳導路徑：川習會美方由商務部長盧特尼克、財長貝森特、貿易代表葛里爾與國務卿盧比歐陪同出席（https://www.cna.com.tw/news/acn/202611190138.aspx ），若美中俄會晤在能源制裁、俄烏停火或部分關稅豁免釋出緩和訊號，將會與「荷莫茲水雷實質毀損油輪＋歐洲定價 ECB 升息 3 次」形成劇烈拉扯；一旦外交無實質協議，油輪停保與戰爭險費率暴衝將直接墊高全球製造與運輸成本：
    - 美股：**FRO（Frontline）、STNG（Scorpio Tankers）、LNG（Cheniere）、DAL、UAL**。
    - 台股：**陽明 (2609)、長榮 (2603)、長榮航 (2618)、華航 (2610)、台塑化 (6505)**。
  - 大家還沒注意到的間接受害者：**南非、印度等高度依賴波斯灣原油且正處升／降息邊緣的新興市場央行與本幣債**——荷莫茲航運受阻推高進口燃料通膨，會迫使這類國家放棄寬鬆並擴大外匯干預，加劇新興市場匯率波動。

### NEXT-3｜事件：歐盟加速電網與儲能許可（Grids Package）vs 歐盟擬否決 Anglo American 鎳鐵交易致關礦斷鏈風險（新）
- 推理：
  - 最先受影響的資產：LME 鎳期貨價格、歐洲電力與儲能設備訂單、歐洲不鏽鋼廠（Aperam、Outokumpu、Acerinox）毛利率與股價。
  - 傳導路徑：歐盟一邊大幅縮短再生能源與儲能審批至 3–6 個月（https://www.anews.com.tr/european-union/2026/11/18/eu-reaches-provisional-deal-to-fast-track-permits-for-renewable-energy-projects-electricity-grids ），但另一邊反壟斷部門因擔心中資 MMG 掌握供應而擬否決 Anglo American 巴西鎳鐵礦出售案，反促使賣方警告「若被否決就直接關礦」（https://live.euronext.com/en/financial-news/anglo-american-warns-customers-possible-ferronickel-supply-disruption-if-deal ）。歐洲能源轉型與工業原料「去中國化」正造成短期供給硬缺口：
    - 美股：**STLD、NUE（美國不鏽／特鋼替代）、TSLA（儲能 Megapack 受惠歐洲儲能 3–6 個月快速許可）、FLNC、VALE**。
    - 台股：**華城 (1519)、中興電 (1513)（歐洲電網加速擴建帶動變壓器／重電需求外溢）、華新 (1605)、燁興 (2007)、大成鋼 (2027)**。
  - 大家還沒注意到的間接受益者：**北美電網級儲能與美國本土不鏽鋼廠**——歐洲電網許可大鬆綁拉升儲能交貨能見度，而歐洲不鏽鋼廠若因巴西鎳鐵關礦失去低價原料，訂單與報價將轉向自有供應鏈較完整的北美廠商。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 已由 60% 降至 45%）」
- 最強反方證據：BEA 官方新聞稿已證實 9 月核心 PCE 年增確為 **3.1%**（`https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026`），The Conference Board 預估 10 月將升至 **3.3%**（`https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026`），且本站《財經日曆》卡片亦已載明 9 月前值 `3.1%` 並自估 10 月為 `3.2%`。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法發布年增率，這題將成為「無法判定」；但只要有公布年增率，低於 3.0% 的空間極小。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：我維持落在 2.4%–3.0% 僅約 **30%**（比你修正後的 45% 低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露多數一線雲端商 FCF 轉負且表外承諾逾 4 兆美元，今日（11/19）荷莫茲海峽再爆 3 艘油輪觸水雷起火（`https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906`），且台股今日收跌 1,768 點至 **38,426.89 點**、本週跌逾 10% 迫使證交所出面喊話穩定秩序（`https://news.cnyes.com/news/id/6667459`）。
- 另一種同樣說得通的解釋：就算 Williams 壓低 12 月升息 2 碼機率、美國垃圾債指數因能源權重撐盤未破 4%，「投資級科技債利差走寬＋中東油輪水雷＋亞股千點斷頭」就足以構成實質的「風險升級」。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：我維持「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你的 80% 低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：11/18 美國 EIA 原油庫存暴增 340 萬桶、汽油暴增 520 萬桶後，WTI 跌至 83 美元附近、貼近 80 美元下緣，強美元亦壓抑商品；但今日（11/19）荷莫茲海峽 3 艘油輪觸水雷起火，讓油價上下雙尾風險同時放大（`https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906`）。
- 另一種同樣說得通的解釋：高庫存與高利率拉低基準需求（容易跌破 80 美元），而實質水雷與封鎖升級則可能瞬間衝破 100 美元——也就是油價**在 80–100 美元區間外的機率（雙尾）高於區間內**，並非單純看跌。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **未來 72 小時荷莫茲海峽通航／掃雷動態**。
- 機率估計：我維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」
- 最強反方證據：財報與法說會未見執法處分揭露，今日中央社再報導輝達董事長瓊斯對員工重申「黃仁勳個人行為及缺乏坦誠」是董事會接受辭呈且永不回鍋的原因（`https://www.cna.com.tw/news/aopl/202611190029.aspx`），而台積電副總張曉強亦公開為輝達新團隊「站台」、輝達採購承諾增至 3,900 億美元（`https://www.ctee.com.tw/news/20261119700076-439901`），若屬重大出口犯罪處分前夕，核心供應商通常會趨於保留。
- 另一種同樣說得通的解釋：個人治理／行為失當先觸發董事會立即切割，隨後才引發美國國會與監管機構對過往對中／新加坡銷售的連帶審查。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節，11 月下旬～12 月初）**與 **國會公開聽證會證詞**。
- 機率估計：我估「直接因中國出口調查」**40%–45%**，「個人治理觸發＋連帶國會／監管審查」**55%–60%**（與你目前 45%–50% 接近）。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（無新進展）
- 事實：ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**（已超過帳上負債），且投資級科技長債利差已相對於同評級企業債走寬（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q `Commitments and Contingencies / Uncommenced Leases` 追蹤，及 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜缺少「非公開交易 BDC 限額贖回（Gating）、非銀金融槓桿（NBFI）與主權債財政－金融連動」監測（補充 FSB 官方來源）
- 事實：金融穩定委員會（FSB）秘書長 John Schindler 在 RiskLive Asia 2026 演說與聯準會 FEDS Notes（2026-10-14）皆重點示警非銀行金融仲介（NBFI）、私募信貸不透明與避險基金槓桿（https://www.fsb.org/2026/10/innovation-and-resilience-managing-the-risks-of-a-changing-financial-system/ ，HTTP 200 確認）。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜缺少「高集中度雲端／金融基建中斷與 SEC Item 1.05 資安事件」警報（無新進展）
- 推理：監測 SEC 8-K Item 1.05 是否涉及高集中度第三方基建（AWS、Azure、GCP、Cloudflare、DTCC），可比股價更早捕捉系統性中斷。免費資料源：CISA KEV JSON（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）＋ SEC EDGAR。

### BLIND-4｜「台股籌碼風向計」尚未合計三大法人台指期淨口數，亦未統計證交所單日違約交割金額（對照 13:06 更新線上版確認）
- 事實：檢視 11/19 線上「台股籌碼風向計與斷頭警戒」（最後更新 11-19 13:06），目前仍僅對 `外資台指期未平倉 -99,438 口` 亮紅燈，尚未加總投信與自營商為 **「三大法人合計淨空單 -7,322 口」**，亦未納入證交所／櫃買每日違約交割金額統計（11/18 爆 9 檔達標 4.269 億元、整體買賣總額約 9.64 億元）。免費資料源：期交所「三大法人區分各期貨契約交易資訊」與證交所「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」（無新進展）
- 推理：建議在「IPO 觀察」補上大型 IPO 納入 S&P 500、Nasdaq-100 指數時程與被動 ETF 權重排擠效應說明。

---

### SITE-1｜`forecast.json` 寫「9 月核心 PCE 數字：查無」，但本站《財經日曆》PCE 卡片其實已顯示「前值 3.1%」（13:27 線上版確認仍存在）
- 本站寫了什麼：`research_feed/forecast.json` 第 130 行寫著 `9 月核心 PCE 數字：查無。`。
- 正確應該是什麼：本站線上《財經日曆》分頁之 `PCE 物價（聯準會最重視的通膨）` 卡片（11/19 13:27 版）已明確顯示 **`核心 PCE 月增 前值 0.3%`、`核心 PCE 年增 前值 3.1%`、`PCE 月增 前值 0.5%`、`PCE 年增 前值 3.6%`**，完全符合 BEA 官網新聞稿（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）。請將日曆卡片的前值資料管線串接至預測腳本。

### SITE-2｜11/19 `10:33 緊急加班` 語音稿截至 13:27 仍誤把「今天（11/19）台股盤中跌幅」講成「台股昨天收盤附近少了 3.4%」（確認仍存在）
- 本站寫了什麼：線上總覽 `🚨 緊急加班（最後更新 11-19 10:33 台北）` 語音文字稿仍寫著：`「台股昨天收盤附近比前一天少了三點四個百分點」` 且寫開盤前能源股跳空原因「我目前沒有找到」。
- 正確應該是什麼：台股「昨天（11/18）」收盤其實是**上漲 +102.80 點（+0.26%）收在 40,194.91 點**（https://www.cna.com.tw/news/afe/202611180304.aspx ）；`-3.4%`（今天最終收盤擴大為 `-4.40%`、收 38,426.89 點）是**今天（11/19）**的跌幅，且 11/18 恰為雪佛龍（CVX）每股 1.78 美元季息除息日（https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ）。

### SITE-3｜`api/gemini_ask`（13:31 即時版）仍僅標示 `CNQ +3.2%（盤前）`，未附正規盤收跌 -4.63%（無新進展）
- 本站寫了什麼：`https://wallstreet-sentinel.pages.dev/api/gemini_ask`（台北 13:31）仍寫 `### CNQ｜CNQ（Canadian Natural Resources）今天 +3.2%（盤前）`，未呈現正規盤重挫 -4.63% 的完整脈絡（https://www.nationthailand.com/news/world/40073656 ）。

### SITE-4｜`upcoming.json`（13:14 版）之 WMT 公布時間與 HPE 共識 EPS 略低於市場實際公告與最新共識（新增）
- 本站寫了什麼：`https://wallstreet-sentinel.pages.dev/upcoming.json`（`asof: 2026-11-19 13:14`）將 `WMT` 時間列為 `2026-11-19T08:00`（台北 21:00），並將 `HPE` `eps_f` 列為 `1.17`。
- 正確應該是什麼：沃爾瑪官方公告 Q3 FY27 財報新聞稿於 **美東 07:00（台北 20:00）發布**、08:00（台北 21:00）才為電話會議（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ）；而 `HPE` 目前市場共識調整後 EPS 為 **1.27–1.29 美元**（公司自身財測 1.20–1.30 美元，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ）。

### SITE-5｜總覽《每日總經情勢》台股加權定格在 13:27 建置的盤中數字，且《未來 14 天事件》未標明「10 年期 TIPS」（更新）
- 本站寫了什麼：13:27 建置的總覽 `台股加權` 顯示 `38,490（-4.24%）`，`未來 14 天事件` 列 `11-19 美債 10 年期標售（增額）$19B`。
- 正確應該是什麼：台股 13:30 實際收在 **38,426.89 點（-4.40%）**（待下次定時重建更新）；另今日 $19B 增額標售為 **10 年期 TIPS（抗通膨公債）**，建議加註「TIPS」以免與名目 10 年債混淆。

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆，對照 13:14／13:27 線上版核對
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳峰會；美東盤前（台北 20:00–21:00）**WMT、BABA、PDD、WSM** 財報；台北約 21:00（南非 15:00）**南非央行（SARB）利率決策**（https://www.sabcnews.com/sabcnews/analysts-expect-mpc-to-keep-interest-rates-unchanged/ ）；美東 09:30（台北 22:30）**Anthropic (ANT)、MapLight (MPLT)** 掛牌；美東 13:00（台北 11/20 02:00）**美債 10 年期 TIPS 增額標售 $19B**；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP** 財報（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
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
- 對照本站 11/19 13:14／13:27 線上版核對：
  - **正確部分**：`未來 14 天事件`（13:27）與 `upcoming.json`（13:14）已正確列出 WMT/BABA/PDD、ANT/MPLT、HPE、ADI、MDT、DELL、HPQ、DE、11/19 美債 10Y 增額 $19B、H.4.1、11/20 OPEX、11/25 GDP 與 PCE、11/30 月底再平衡、12/01 JOLTS；`休市與提早收盤` 亦正確列出 11/26 休市與 11/27 半天交易。
  - **漏掉部分**：`upcoming.json`（13:14）仍漏掉今晚盤後的 **INTU、ROST、GAP**（市值皆逾百億美元）、11/23 **ZM**、11/24 **BBY、BURL、DKS、ADSK、WDAY、ZS**；`未來 14 天事件`（13:27）仍漏掉 **11/19 南非央行、11/20 台灣 10 月外銷訂單、11/21 韓國 20 日出口、11/25 聯準會褐皮書（僅列在《美國經濟日曆》內未上總覽清單）、11/26 韓國央行、11/28 台灣九合一選舉、11/29 OPEC+ JMMC 會議**，且未在該清單內併註 **11/26–27 感恩節休市與半天交易**。

---

### CODE-1｜tools/dots.py：第 85 行 `or f.get("priced")` 在 IPO 定價後立即把公司與同步私募出資者從 17 天事件時間軸抹除
- 檔案路徑與行號：`tools/dots.py` 第 82–96 行（特別是第 85 行）。
- 那一行在做什麼：`events()` 依規定應該整理「過去 10 天到未來 7 天」的 SEC 申報、財報、政策與 IPO／同步私募（`pp`）交集；但第 85 行寫 `if not (cv.get("pp") or f.get("a12")) or not (lo <= late <= hi) or f.get("priced"): continue`。
- 為什麼有問題：一旦某家焦點公司剛定價準備隔天掛牌（例如 Anthropic 在 11/18 晚間定價 83 美元、`f.get("priced")` 轉為 True，準備 11/19 上市），`dots.py` 在它**還沒正式開盤交易之前**，就把該公司的 `ipo` 與同業出資者的 `pp`（例如輝達出資 Anthropic 100 億美元）從整個 17 天時間軸移除，導致仍在過去 10 天窗口內的關鍵交集（如 NVDA 8-K + BIS + 財報 + ANT 同步私募）突然消失。
- 建議怎麼改：移除 `or f.get("priced")`，改依 `lo <= late <= hi` 判斷是否仍在過去 10 天到未來 7 天的視窗內（若須區分狀態，可在文字標註「已定價」或「已掛牌」）。
- 確定度：高。

### CODE-2｜wsb/analytics/stock_shock.py：第 96–102 行遇到美股平日國定假日隔天會提早 `break`，漏掉前一交易日盤後財報
- 檔案路徑與行號：`wsb/analytics/stock_shock.py` 第 96–103 行（`earnings_note`）。
- 那一行在做什麼：往回找上一個交易日，檢查該公司是否於前一交易日盤後公布財報，註解寫明 `(skip a weekend / holiday)`；若沒找到財報且 `p.weekday() < 5` 就執行第 101–102 行的 `break`。
- 為什麼有問題：在美股平日國定假日隔天的第一個交易日（例如下週五 `2026-11-27` 為感恩節隔天、週四 `11/26` 休市；或總統日／陣亡將士紀念日等週一假日隔天的週二），`back=1` 查到週四 `11/26`（或週一假日）沒有財報，因 `p.weekday() < 5` 為真就直接 `break` 跳出迴圈，不會再往回查 `back=2`（`11/25` 週三盤後或週五盤後）的財報，導致假日隔天的財報大動被誤寫為「找不到對得上的新聞，原因還不清楚」。
- 建議怎麼改：不要只用 `p.weekday() < 5` 認定是交易日，改為跳過 `wsb.data.exchange_cal` 的美股休市日（或僅在有交易日資料時才 `break`）。
- 確定度：高。

### CODE-3｜wsb/analytics/event_clock.py：第 63–65、73–74 行四巫日未依規則「遇假日提前」，2026 年 6 月四巫日直接指向休市的六月節假日
- 檔案路徑與行號：`wsb/analytics/event_clock.py` 第 5、63–65、73–74 行。
- 那一行在做什麼：`quad_witching(y0, y1)` 用 `third_friday(y, m)` 產生 1995 至明年的所有四巫日；第 5 行 docstring 寫明「四巫日＝3、6、9、12 月第三個星期五（遇假日提前）」。
- 為什麼有問題：程式完全沒有檢查該星期五是否為美股國定假日（例如 **2026 年 6 月 19 日**恰好是星期五且為美股休市日 Juneteenth，實際四巫日提前至 **2026-06-18**；部分年份 3 月第三個星期五也會撞到 Good Friday）。結果是：(1) 倒數時鐘在該季會指到休市日；(2) `move_stats()` 用 `r.reindex(idx).dropna()` 統計歷史震幅時會漏掉所有撞到假日的四巫日樣本。
- 建議怎麼改：檢查算出的 `third_friday` 是否為 Good Friday 或 Juneteenth（或比對實際 S&P 500 交易日索引），若遇休市則前移一個交易日。
- 確定度：高。

### CODE-4｜wsb/data/migration_polls.py：第 142–146、154–158 行用固定筆數位置 `iloc[-13]`／`shift(12)` 算年增率，遇到缺失月份會錯抓基期
- 檔案路徑與行號：`wsb/data/migration_polls.py` 第 142–146、154–158 行。
- 那一行在做什麼：`_yoy()` 以 `(s.iloc[-1] / s.iloc[-13] - 1) * 100` 計算行業時薪年增率；`migration()` 以 `fb - fb.shift(12)` 與 `fb.iloc[-13]` 計算外國出生勞動力 12 個月增減與一年前占比。
- 為什麼有問題：外國出生勞動力（`LNU01073395`）與本國出生勞動力（`LNU01073413`）屬於 BLS 家戶調查（CPS）。一旦遇到聯邦政府停擺造成單月調查缺期（如 2025 年 10 月停擺曾導致多項家戶資料中斷），`dropna()` 後的固定位置 `iloc[-13]` 與 `shift(12)` 就會往前錯位變成「13 個月前」而非「去年同月」，使 12 個月變動與年增率失真。
- 建議怎麼改：改用時間索引 `target = s.index[-1] - pd.DateOffset(months=12)` 精確比對去年同月數值，缺該月時回傳 `None` 而非往前滑移補位。
- 確定度：高。

### CODE-5｜tools/site_econ.py：第 164 行未防衛空 `probs` 字典，且第 335、506 行依賴固定 6 字元前綴切出台北時間
- 檔案路徑與行號：`tools/site_econ.py` 第 163–164、335、506 行。
- 那一行在做什麼：`_fw_block()` 第 164 行直接寫 `likely = items[0][0]`；第 335、506 行寫 `(e.get("tpe") or "")[6:]` 擷取台北時分。
- 為什麼有問題：若期貨模組某次未產出 `nx["probs"]` 鍵值（`items` 為空）第 164 行會引發 `IndexError`；另外 `[6:]` 隱含假設上游 `_fmt_times()` 永遠回傳 `"MM/DD HH:MM"`（6 字元日期前綴），若格式改為 `"YYYY-MM-DD HH:MM"` 就會被截斷出錯。
- 建議怎麼改：第 164 行改為 `if not items: return ""`；第 335、506 行改用 `split(" ", 1)[-1]` 取得時間字串。
- 確定度：低（屬防禦性修正，目前上游格式相符）。

（備註：本小時批次 `i % 24 == 13` 共 12 檔，其餘 7 檔 `tools/site_learn.py`、`tools/site_stamp.py`、`wsb/analytics/bankruptcy.py`、`wsb/analytics/physics.py`、`wsb/data/__init__.py`、`wsb/data/fed_register.py`、`wsb/data/treasury.py` 皆已逐行檢查完畢，未發現上述錯誤。）

---

其他今天的大事：
- 台股 11/19 盤中高低震盪逾 2,055 點（低見 38,259.70 點），終場收跌 **1,768.02 點（-4.40%）至 38,426.89 點**、台積電收 **2,100 元（-3.45%）**、櫃買 13:29 重挫 7.32%；本週累跌逾 10% 使證交所公開表態必要時採穩定措施；昨日爆出 4.269 億元違約交割的 9 檔 AI 股今日盤中全數一度亮燈跌停；新台幣午盤暫收 **32.988 元**（https://news.cnyes.com/news/id/6667459 ；https://news.cnyes.com/news/id/6667450 ；https://www.chinatimes.com/realtimenews/20261119002092-260410 ；https://www.cna.com.tw/news/afe/202611190098.aspx ）。
- APEC 深圳峰會 11/19 進入高潮：中午 13:24「川習會」正式登場（盧比歐、貝森特、盧特尼克、葛里爾全數出席），川普稍早亦與普丁場邊簡短會談，會後將舉行美中俄三方峰會；美國會 USCC 年報示警未來 24 個月台海封鎖風險提高（https://www.cna.com.tw/news/acn/202611190138.aspx ；https://www.cna.com.tw/news/aopl/202611190121.aspx ；https://www.uscc.gov/sites/default/files/2026-11/2026_Annual_Report_to_Congress.pdf ）。
- 荷莫茲海峽 11/19 驚傳 **3 艘油輪觸及水雷起火失能**，稍早阿聯 ADNOC 船隻遇襲致 11 傷 1 失蹤；歐盟 11/18 達成「歐洲電網包裹」加速許可臨時協議，同時傳出歐盟反壟斷擬否決 Anglo American 巴西鎳鐵售予中資 MMG 引發關礦斷鏈警告（https://www.aa.com.tr/en/middle-east/3-oil-tankers-disabled-by-mine-blasts-in-strait-of-hormuz-iranian-army/4129906 ；https://www.anews.com.tr/european-union/2026/11/18/eu-reaches-provisional-deal-to-fast-track-permits-for-renewable-energy-projects-electricity-grids ；https://live.euronext.com/en/financial-news/anglo-american-warns-customers-possible-ferronickel-supply-disruption-if-deal ）。
- 台灣半導體供應鏈今日連爆新訊：**日月光投控（3711）動土投資 2,489 億元建高雄仁武 AI 高階測試新廠**；**海龍風電 2A 轉簽 CPPA 售綠電予台積電**；台積電張曉強公開力挺輝達新團隊，輝達董事長瓊斯重申黃仁勳不回鍋並預告 12 月提前加薪留才（https://www.cna.com.tw/news/afe/202611190122.aspx ；https://www.cna.com.tw/news/afe/202611190102.aspx ；https://www.ctee.com.tw/news/20261119700076-439901 ；https://www.cna.com.tw/news/aopl/202611190029.aspx ）。
- 美國商務部 BIS 遠端算力管制新規（`2026-23529`）今日生效，新加坡已與美展開「可信賴用戶」實務磋商；PANW Q1 FY27 財報大好並斥資 45 億美元收購 Applied Compute；今晚（11/19）20:00–22:30 沃爾瑪、阿里巴巴、拼多多公布財報，且 Anthropic（ANT，定價 83 美元、估值 1.5 兆美元）正式在納斯達克掛牌（https://public-inspection.federalregister.gov/2026-23529.pdf ；https://www.channelnewsasia.com/singapore/singapore-us-semiconductor-mddi-josephine-teo-6560761 ；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ；https://w.media/anthropic-ipo-priced-at-us-83-per-share-valuation-increases-to-us-1-5-trillion/ ）。

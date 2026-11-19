台北時間 2026-11-19 18:45

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）、整體 PCE 年增率為 **3.6%**（月增 **0.5%**），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，台北時間 2026-10-29，HTTP 200 確認）。
- 事實：之所以 9 月核心 PCE（3.1%）反過來高於核心 CPI（2.6%），根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 高於核心 CPI 的倒掛現象（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。
- 事實：本地 `research_feed/forecast.json` 第 130 行截至 18:30 重讀仍寫 `9 月核心 PCE 數字：查無。`，與 BEA 官方新聞稿及線上《財經日曆》PCE 卡片顯示的前值不符。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照（無新進展）
- 事實：歐洲央行（ECB）2026 年 11 月《金融穩定評估》Box 3（"The debt financing of AI and its implications for financial stability"）明確列出美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 共識（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，台北時間 2026-11-18，HTTP 200 確認）。
- 事實：ECB Box 3 正文對自由現金流的口徑為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（僅以**資本支出超過營運現金流**作為表層口徑，未把尚未起租的表外租賃算進單季現金流）；同時於圖表 A 與註腳 6 依美國會計準則 **ASC 842** 單獨指出，已簽約但資產尚未投入使用的租賃與算力承諾在起租前不計入資產負債表負債，這類表外承諾合計已逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200 確認）。
- 事實：四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與租賃口徑落差如下：
  - Meta（Q3 2026）：營運現金流 **$32.79B**，資本支出（含融資租賃本金償還）**$34.91B**，自報自由現金流為 **-$2.12B（轉負）**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ，HEAD 200 確認）。
  - Alphabet（Q3 2026）：營運現金流 **$42.29B**（$42,290M），現金 PP&E 購置（不含融資租賃）**$51.36B**（$51,355M），自報自由現金流為 **-$9.07B（-$9,065M，轉負，含 52 億美元歐盟罰款支付）**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ，HEAD 200 確認）。
  - Amazon（Q3 2026／TTM）：單季營運現金流 **$42.42B**、單季淨 PP&E 購置 **$75.93B**（隱含單季 **-$33.51B**），公司自報 **TTM 自由現金流 -$42.36B（-$42,357M，轉負）**，該口徑僅扣現金淨 PP&E、未扣額外揭露之新簽融資租賃資產（Q3 單季 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ，HEAD 200 確認）。
  - Microsoft（Q1 FY27）：營運現金流 **$58.02B**，現金 PP&E 資本支出 **$39.37B**，自報自由現金流為 **+$18.6B（仍為正值，年減 27%）**；若計入新起租之融資租賃，總資本支出達 **$45.2B**，扣除後仍餘約 +$12.8B，印證 ECB 精準寫 `"most"` 而非全部（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ，本輪伺服器回傳 HTTP 403，維持前輪已讀數字）。

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（18:45 補充 17:32 盤中語音稿新實例）
- 推理：檢視 `research_feed/claude_notes.md`、`research_feed/forecast.json`、`research_feed/sessions.json` 與最新 `research_feed/macro_voice.json`（`2026-11-19 17:32 台北` 盤中版），最常「下太快」的是以下兩種思考捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：例如 `claude_notes.md` 第 14 行在還沒核對 `bea.gov` 或本站日曆卡片前值的情況下，因為「核心 PCE 通常比核心 CPI 低」，就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推 10 月區間；以及 `forecast.json` 第 65–73 行先前曾用單一 `BAMLH0A0HYM2`（3.43%）得出「信用市場還沒出現壓力」（第 3 輪你已修正）。
  2. **把「自己的新聞關鍵字只抓到標題或沒對上時間」直接當作「沒有原因」**：最新 `macro_voice.json`（`2026-11-19 17:32 台北` 盤中版）寫「台股今天收盤跌四點四趴…至於原因，我沒有找到時間對得上的單一消息」，同時線上前幾班的 `16:34 緊急加班` 仍寫「能源這邊，我找不到時間對得上的原因」。其實 11/19 台股重挫有明確籌碼與政策結構（自營商避險賣超 **214.40 億元**幾乎比肩外資 -243.12 億元、櫃買大跌 7.22%、上市櫃再爆 **1.29 億元**違約交割與金管會 11/20 升級 3.5% 限空令）；而 11/18 能源股下跌亦有 EIA 原油累庫 340 萬桶／汽油大增 520 萬桶及雪佛龍除息 1.78 美元對得上時間。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標（18:45 補充台積電正式入股與 BABA 剛公布之 FCF 反應）
- 事實：中央社 11/19 16:46 報導，台積電正式代子公司 TSMC Partners 公告以 **每股 83 美元**取得 Anthropic 普通股 **6,024,096 股**，總金額約 **5 億美元**（持股約 0.03%，依美國 1933 年證券法 Rule 144 一次付清，https://www.cna.com.tw/news/afe/202611190254.aspx ，HTTP 200 確認）。此外，阿里巴巴（BABA）剛於 11/19 18:18 前公布 Q2 FY27 財報，雖然 AI 雲與算力收入年增 53%、總營收人民幣 2,715.19 億元優於預期，但因資本開支年增 60% 至 504.77 億元、自由現金流再度淨流出 **344.72 億元**且經調整淨利低於預期，ADR 盤前隨即挫逾 **2%**（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ，HTTP 200 確認）。
- 推理：這印證市場對「AI 算力投資能否轉化為正現金流」極度敏感。若今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，傳導先後順序維持如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：負債比高、高度仰賴大模型算力長約抵押融資，且 Anthropic 轉向透過博通租賃 3.5 GW Google TPU 機櫃自建資料中心（https://www.cna.com.tw/news/afe/202611190156.aspx ），直接稀釋第三方租賃溢價。隔天（11/20）可驗證指標：`CRWV`、`NBIS` 相對 `QQQ` 的開盤超額跌幅，及新雲端無擔保債二級殖利率走勢。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸**：ANT 公開發行募資約 813 億美元（含 260 億美元同步私募合計約 1,073 億美元）、完全稀釋估值約 1.5 兆美元，若破發將壓縮 OpenAI 與晚期 AI 獨角獸 IPO 窗口。隔天可驗證指標：`ARCC`、`BIZD`、`BX`、`APO` 股價與承銷商護盤（stabilizing bid）報導。
  3. **最後且分化：晶片與機櫃合作夥伴（NVDA、AVGO、GOOGL、AMZN、MSFT、MU、台積電等同步私募出資方）**：主要承受公允價值重估回吐，但 Anthropic 轉向自建反而讓博通與 TPU 機櫃組裝廠受關注。隔天可驗證指標：`AVGO`／`NVDA` 相對 `^SOX` 強弱與次日選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態（18:45 更新 BABA 自由現金流淨流出、利雅德 PIF 大樓遇襲、歐洲商業銀行協議與歐盟網攻）
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意且跨海應驗**：ECB Box 3 佐證多家美系雲端商 FCF 轉負、表外承諾逾 4 兆美元，今日（11/19）**阿里巴巴（BABA）**公布 Q2 FY27 亦見單季 CapEx 飆升 60% 至 504.77 億人民幣、FCF 淨流出擴至 **344.72 億人民幣**導致 ADR 盤前挫逾 2%；台積電 11/19 亦正式公告參與 Anthropic 約 5 億美元私募，顯示資金高度綁定但尚未出現信用違約事件。
  2. **主線 2（輝達治理風波 vs 出口調查）— 部分同意，兩條線已證實交織**：中央社 11/19 引述《福斯新聞》專訪指出，與黃仁勳有染的一名女子正受到美國政府調查是否為中國情報機構工作、以及是否協助走私晶片（https://www.cna.com.tw/news/aopl/202611193003.aspx ，HTTP 200 確認）。個人治理風波與國安／晶片出口調查不是二選一，而是**同一人物同時觸發公司治理與國安調查**，建議第 4 輪整併重估。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，補充台股限空令與歐洲緩解**：今日台股集中市場收跌 **1,768.02 點（-4.40%）至 38,426.89 點**、櫃買重挫 **-7.22% 至 285.33 點**、世界／台化／萬泰科爆 **1.29 億元**違約交割，金管會宣布 **11/20 起升級 3.5% 限空令**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://stock.ltn.com.tw/article/m7hjf9c9axqq ，皆 HTTP 200）；但新台幣 16:00 翻升收 32.942 元、日韓印股市收紅、歐股 STOXX 600 早盤反彈 +0.3%（UniCredit 與德國政府就 Commerzbank 達協議），壓力主要集中於高利率折現與亞太高槓桿籌碼。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意，地緣實質衝突再升級**：IEA 11/19《2026 世界能源展望》警告荷莫茲海峽已累計中斷 28 億桶原油與 600 億立方公尺天然氣供應、構成「史上最大能源安全威脅」（https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ，HTTP 200）；且今日葉門胡塞武裝飛彈襲擊沙國首都利雅德，攔截碎片擊中沙國主權基金（PIF）80 層總部大樓（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ，HTTP 200），使荷莫茲與波灣基建尾部風險高於昨日單純的 EIA 累庫定價，仍維持 **55%**（雙尾波動風險升）。
  5. **主線 5（「風險升級」劇本 33% vs 40%）— 同意方向一致**，差距 7 個百分點；台股自營商避險砍倉、1.29 億元違約交割與 BABA 資本支出導致 ADR 盤前下挫，持續印證市場對高利率＋高舉債 AI 商業模式的敏感度。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題（18:45 更新）
- 1. `research_feed/macro_voice.json` 最新版本（`2026-11-19 17:32 台北` 盤中版）對今日台股重挫 4.4% 仍寫「沒有找到時間對得上的單一消息」，而 `16:34 加班版` 也仍寫找不到 11/18 能源股下跌原因。你的語音腳本管線要如何同時接入「三大法人買賣超明細（含自營商避險）＋金管會盤後公告」以及「個股除息日曆＋EIA 週三發布時點」？
- 2. 今日（11/19）一邊是**阿里巴巴（BABA）**因 AI 資本開支年增 60% 導致 FCF 淨流出 344.72 億人民幣、ADR 盤前挫逾 2%；另一邊是 **IEA 警告荷莫茲危機超越 1970 年代＋胡塞飛彈碎片擊中利雅德 PIF 大樓**。第 4 輪你打算如何調整「AI 資本支出現金流壓力」、「輝達事件定性」與「油價／風險升級」的機率？
- 3. 本地 `research_feed/forecast.json` 第 130 行截至 18:30 仍寫「9 月核心 PCE 數字：查無」，與 BEA 官方新聞稿（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）及線上《財經日曆》顯示的 3.1% 不符，請問預計何時在 `forecast.json` 補上基準值？

---

### WIDE-1｜IEA 11/19《2026 世界能源展望》警告荷莫茲為「史上最大能源威脅（累積斷供 28 億桶油）」＋胡塞飛彈碎片擊中沙國主權基金 PIF 利雅德總部（更新）
- 事實：國際能源總署（IEA）於 **2026 年 11 月 19 日**發布《2026 世界能源展望》，執行長 Fatih Birol 指出，今年 2 月爆發的美以伊衝突與伊朗封鎖荷莫茲海峽已造成「**史上最大的能源安全威脅**」，衝擊規模「**讓 1970 年代石油危機相形見絀**」，能源世界「再也回不去從前」；截至 11 月波灣累積供給損失達 **28 億桶原油與 600 億立方公尺天然氣**（https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ，台北時間 2026-11-19，HTTP 200 確認）。同日（11/19 下午）法新社與 Türkiye Today 報導，葉門胡塞武裝朝沙烏地首都利雅德發射飛彈，攔截墜落碎片損及利雅德金融區最高建築、沙國主權財富基金（PIF）80 層總部大樓外牆與多樓層窗戶（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ，台北時間 2026-11-19 14:52，HTTP 200 確認）。
- 推理：美股盤面焦點仍在昨日 EIA 美國庫存增加，忽視了波灣產油國核心金融與主權機構（PIF）建築已出現實體飛彈碎片波及，加上全球緩衝庫存耗盡，一旦油輪保險或沙國境內能源設施再遭干擾，遠月原油曲線與高收益／主權債風險溢價會迅速跳升。
- 先影響資產：布蘭特原油遠月價差、沙烏地與波灣主權債 CDS、油輪與航空燃油成本。

### WIDE-2｜APEC 深圳「川習會（30 對 30 協議）」與美中俄首次三方領袖峰會結束（歷時約 1.5 小時）（更新）
- 事實：11/19 中午美中「川習會」在深圳麒麟山莊登場，川普表示雙方依「**30 對 30 協議**」同意各自對價值 **300 億美元**商品削減關稅，並稱美中在維持荷莫茲海峽暢通及防堵伊朗擁核武上有強烈共識；稍早川普與普丁單獨會談暖身後，下午舉行**史上首次美中俄三方領袖峰會**，塔斯社報稱會談持續約 **1.5 小時**，聚焦俄烏戰爭（川普稱每月 2.5 萬人喪命）、核武軍控與伊朗局勢（https://www.cna.com.tw/news/aopl/202611193005.aspx ，台北時間 2026-11-19，HTTP 200 確認；https://www.channelnewsasia.com/world/trump-xi-putin-summit-apec-shenzhen-china-6564556 ，待補確認；https://www.cna.com.tw/news/acn/202611190062.aspx ）。
- 推理：一般商品小幅降稅搭配同日生效的 BIS 遠端算力封鎖，代表美中形成「傳統貨物降溫、高階算力與能源安全各自角力」的雙軌結構；三方峰會若僅止於政治表態而無具體停火或制裁鬆綁條約，避險溢價回吐後仍易反覆。
- 先影響資產：USD/CNH、中概消費股（KWEB）、歐洲天然氣、美歐國防軍工股。

### WIDE-3｜德國與 UniCredit 11/19 就併購德國商業銀行達成妥協＋歐盟執委會遭 AI 工具網攻癱瘓人資醫療系統逾 10 天（更新歐洲重大事件）
- 事實：路透與 dpa-AFX 11/19 報導，義大利裕信銀行（UniCredit）與德國政府就收購德國商業銀行（Commerzbank）達成框架妥協：UniCredit 承諾保留 Commerzbank 法蘭克福總部與德國上市地位並提名兩名具德國市場專長之獨立董事，柏林則放棄直接指派監事會席次並支持控制權平順轉移；帶動歐股 STOXX 600 早盤反彈 **+0.3% 至 645.85 點**、Commerzbank 漲 1.4%、UniCredit 漲 1.8%（https://www.tradingview.com/news/tradingview:d5957c435105b:0-key-facts-unicredit-board-nominees-commerzbank-takeover-rules-proposed/ ；https://www.euronext.com/en ，請詳新聞頁；註：TradingView `Key facts` 含 AI 摘要免責聲明，另有 Politico／Daily Sabah 11/19 獨立報導歐盟執委會遭駭客利用 AI 滲透工具 ARTEX 網攻逾 10 天，影響人資 Sysper 與醫療報銷 MyPMO 系統並恐致大量員工個資外洩，https://www.dailysabah.com/business/tech/european-commission-hit-by-cyberattack-report ，HTTP 200 確認）。同時英國 10 月 CPI 升至 **3.6%**（https://www.mufgresearch.com/macro/european-macro-18-november-2026/ ，HTTP 200）、ECB 拒替法國公債（10Y OAT 約 4.87%）撐盤，德國 IG Metall 罷工持續。
- 推理：德國對 UniCredit 讓步為歐洲停滯已久的跨境銀行整併開綠燈，短線提振歐洲銀行股；但另一端「ECB 不買債撐法國＋英國高通膨＋德國製造業罷工＋歐盟核心機構遭 AI 網攻」顯示歐洲財政、勞動與資安結構脆弱度仍在上升。
- 先影響資產：歐洲銀行股（EUFN）、法德 10 年期公債利差、EUR/USD、歐系資安與汽車類股。

### WIDE-4｜日本央行植田和男 11/19 國會重申升息決心＋熊本清晨 M5.7 餘震（尚無 JASM 重大停工回報）＋南非央行維持 7.25% 不變（無新進展）
- 事實：路透／CNA 11/19 報導，日本央行（BOJ）總裁植田和男在國會淡化疲軟消費數據、警告潛在通膨有突破 2% 上行風險，強化 12 月升息至 **1.50%** 預期（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ，HTTP 200 確認）。11/19 清晨 02:22（台北 01:22）熊本發生規模 **5.7 地震**（深度 10 公里、7 月 28 日 M7.1 強震之餘震），截至目前無台積電熊本 JASM 廠重大結構損壞或停工回報（https://www.chinadailyasia.com/hk/article/642914 ，HTTP 200）。11/19 日經 225 收漲 **+0.71%** 至 **59,444.21 點**；同日南非央行（SARB）宣布維持基準附買回利率 **7.25%** 不變。
- 推理：市場過度聚焦聯準會 12/9 升息，若 BOJ 於 12/17–18 跟進升息至 1.50%，日圓套利資金回流將對全球高倍數科技股形成第二波流動性擠壓。
- 先影響資產：USD/JPY、日本 10 年期公債、全球科技股估值。

### WIDE-5｜印度 10 月 CPI 破 6% 上限至 6.09%、強氣旋「阿克萬」11/20 中午登陸奧里薩邦（撤離逾 10 萬人）（無新進展）
- 事實：印度 10 月 CPI 升至 **6.09%** 突破央行 6% 上限（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ），11/19 印股 Nifty 50 反彈收漲 **+0.91%** 至 **25,458.75 點**。印度氣象局追蹤強烈氣旋「阿克萬（Akvan）」預計 **11 月 20 日中午**登陸奧里薩邦（Odisha），當地已緊急撤離逾 10 萬人（https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ，HTTP 200）。
- 推理：若氣旋衝擊東岸港口、農產與電力基建，將進一步推升印度食品通膨並壓縮印度央行政策空間。
- 先影響資產：INDA、USD/INR、新興亞洲資金流。

---

### A｜今天的大動（對照 https://wallstreet-sentinel.pages.dev/api/gemini_ask 台北 11/19 18:32 最新 12 檔題目單）

### PANW｜Palo Alto Networks（PANW）今天 +9.6%（盤前）：Q1 FY27 財報優於預期＋45 億美元併購 Applied Compute（無新進展）
- 事實：美東 11/18 盤後公布 Q1 FY27 營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億）、Non-GAAP EPS **1.05 美元**（優於預期 0.97 美元）、NGS ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**（FactSet 共識 141.7 億）、調整後 EPS 指引至 **4.26～4.30 美元**（FactSet 共識 4.18 美元），並宣布以 **45 億美元**全股票收購開源權重 AI 模型平台 **Applied Compute**，推動盤後與今日盤前續漲約 **+9%～+9.6%**（https://www.prnewswire.com/news-releases/palo-alto-networks-reports-fiscal-first-quarter-2027-financial-results-302944393.html ；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，皆 HTTP 200）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。KeyBanc 亦於財報後將 PANW 評等調升至 **Overweight**、看法調高至 **$380**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200）。

### TJX｜TJX Companies（TJX）今天 +8.0%：Q3 FY27 同店銷售成長 4% 超越計畫、上調全年展望至區間上緣
- 事實：TJX 於美東 **2026 年 11 月 18 日**公布 Q3 FY27（截至 10/31）財報，淨銷售年增 **6%** 至 **159.5 億美元**（約 160 億美元，優於預期約 158 億美元）、合併同店銷售成長 **4%**（優於公司原計畫 2%–3%）；GAAP 稀釋後 EPS **1.39 美元**（年增 9%，含 **0.05 美元** IEEPA 關稅退稅淨利益），調整後 EPS **1.34 美元**（年增 5%），並將 FY27 全年展望收斂至區間上緣（全年同店估約 +4%）（https://mlq.ai/news/tjxs-comparable-sales-rise-4-above-its-plan-and-it-narrows-its-full-year-outlook-toward-the-top-of-the-range/ ，美東 2026-11-18 12:44，HTTP 200 確認）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### CRWD｜CrowdStrike（CRWD）今天 +6.5%（盤前）：受同業 PANW 財報驗證企業 AI 資安需求外溢帶動（無新進展）
- 事實：CRWD 預計 **12 月 1 日盤後**才公布財報，11/18–19 本身無單獨公司公告或分析師調整（找不到來源）；美東 11/18 正規盤大漲 +7.95% 收 $237.03 後，盤前受同業 PANW Q1 FY27 財報全面優於預期與 45 億美元 AI 安全併購案外溢提振，資安族群集體走高（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200 確認）。
- 本站漏掉的：屬同業財報外溢效應，非 CRWD 個別公告。

### VLO｜Valero Energy（VLO）今天 -5.5%：EIA 汽油庫存暴增 520 萬桶、蒸餾油與原油同增壓抑煉油族群
- 事實：美東 **2026 年 11 月 18 日** 10:30 美國能源資訊局（EIA）公布截至 11/13 當週報告，**汽油庫存意外大增 520 萬桶至 2.159 億桶**、**蒸餾油增 160 萬桶至 1.049 億桶**、**商業原油庫存連兩週增加（+340 萬桶至 4.178 億桶）**，壓抑原油與成品油裂解價差預期，拖累美國獨立煉油類股（VLO、PSX、MPC）同步下挫（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ，HTTP 200 確認）。
- 傳聞／找不到來源：VLO 11/18 當日無單獨公司公告或分析師降評（找不到來源；`globalbankingandfinance.com` 盤後跌勢快訊為系統自動產生，不採計為人工報導來源）。
- 本站漏掉的：VLO、PSX 與昨日 XOM、CVX、CNQ 屬同一產業（能源與煉油）同日受 EIA 庫存大增連動。

### SKHY｜SK 海力士（SKHY）今天 +5.5%（盤前）：韓股連兩日收漲，受 Anthropic 1.5 兆美元 IPO 定價點燃全球記憶體股盤前大漲
- 事實：SK 海力士（000660.KS）於 **2026 年 11 月 19 日**韓股正規盤收漲 **+3.41%** 至 **1,183,000 韓元**（連兩日走高，https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ，HTTP 200 確認）；同日美股／海外追蹤盤前因 Anthropic 擴大發行至 9.8 億股、以每股 83 美元定價（募資 813 億美元、估值 1.5 兆美元）今晚掛牌，刺激記憶體與儲存族群盤前集體大漲，SK 海力士盤前／追蹤漲逾 **5%**（https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，2026-11-19，HTTP 200 確認）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### HCA｜HCA Healthcare（HCA）今天 -5.0%：受 CMS「CRUSH」醫保反詐欺追溯審計草案與證券詐欺律師調查發酵拖累板塊，抵消摩根大通調高看法
- 事實：美國聯邦醫療保險與醫療補助服務中心（CMS）11/16 提出「CRUSH」反詐欺規則草案（擬擴張 Medicare Advantage 風險調整稽核並回溯至 2018 給付年度），連續兩日重挫管理式醫療板塊（如 UNH 兩日累跌逾一成），恐慌外溢至醫院營運商 HCA（https://fr.tradingview.com/news/gurufocus:3ac55a47d094b:0-unitedhealth-stocks-fall-4-62-as-cms-proposes-wider-medicare-advantage-audits/ ，HTTP 200 確認）；同日（11/18）摩根大通雖維持 HCA `Neutral` 評等並將價格看法由 $425 調高至 **$475**（https://www.tradingview.com/news/tradingview:9eb3a7caf755c:0-jp-morgan-maintains-hca-healthcare-at-neutral-raises-price-target-to-475-from-425/ ，HTTP 200 確認），但仍略低於前收 $501 水準。
- 傳聞／找不到來源：HCA 11/18 當日無官方負面財測新公告；另市場流傳 Pomerantz 律師事務所就 HCA 先前因 ACA 交易所給付不利下修 2026 年獲利指引啟動證券詐欺調查，未見機構或公司正式回應（待證實；`globalbankingandfinance.com` 跌勢快訊屬自動產生不採計）。

### PSX｜Phillips 66（PSX）今天 -4.7%：與 VLO 同受 EIA 汽油／原油庫存暴增壓抑煉油族群；另消化煉油廠排放通報與券商調降看法
- 事實：美東 11/18 同業 VLO、MPC、PSX 同步受 EIA 汽油庫存暴增 520 萬桶、蒸餾油增 160 萬桶與原油累庫 340 萬桶拖累下挫（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ，HTTP 200 確認）。另市場消化 PSX 11/13 德州 Borger 煉油廠製程異常致二氧化硫排放逾 500 磅通報與 Jefferies 將對 PSX 的價格看法自 $280 調降至 $265（搜尋摘要出自 TradingView 轉載路透 AI 摘要，人工全文待查證）。
- 本站漏掉的：與 VLO 屬同一煉油板塊當日集體修正。

### CNQ｜Canadian Natural Resources（CNQ）今天 -4.6%：隨北美油氣股反映 EIA 庫存大增壓低油價與 25.3 億加元併購案（無新進展）
- 事實：CNQ 11/18 正規盤隨北美油氣股下挫收跌 **4.63%** 至 **$45.53**（多倫多收跌 4.06% 至 C$65.52），時間點對得上 EIA 11/18 10:30 公布原油庫存大增 340 萬桶／汽油大增 520 萬桶（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ；https://www.nationthailand.com/news/world/40073656 ，HTTP 200），且市場消化其以 **25.3 億加元**收購 **Advantage Energy** 案（https://www.newsfilecorp.com/release/324091/Canadian-Natural-Resources-Limited-Enters-into-Agreement-to-Acquire-Advantage-Energy-Ltd ）。

### MU｜美光（Micron，MU）今天 +4.6%（盤前）：Anthropic IPO 定價 83 美元今晚掛牌引爆儲存與 AI 記憶體股盤前反彈
- 事實：受 Anthropic（ANT）IPO 定價高於區間、募資 813 億美元今晚於那斯達克掛牌激勵，美光（作為 Anthropic 10 億美元同步私募參與方暨 HBM／DRAM／SSD 策略夥伴）11/19 盤前與 SK 海力士、SanDisk 等儲存／記憶體股集體上揚逾 4%（https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ；https://financefeeds.com/micron-mu-stock-705-thursday-anthropic-ipo-priced-83-bull-746-bear-667/ ，皆 HTTP 200 確認）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### SNDK｜SanDisk（SNDK）今天 +4.5%（盤前）：今日為 1 拆 8 股票分割前最後交易日＋Anthropic IPO 帶動儲存股盤前集體反彈
- 事實：今日（美東 **2026 年 11 月 19 日**）為 SanDisk（SNDK）**1 拆 8 股票分割**盤後分配股權前最後一個拆前交易日（11/20 開盤依拆股後價格交易，https://financefeeds.com/sandisk-sndk-stock-776-thursday-last-session-before-8-for-1-split-bull-831-bear-749/ ；https://www.fool.com/investing/2026/11/16/sandisk-splits-its-stock-8-for-1-on-nov-19-flash-memory-prices-still-matter-more-than-the-share-count/ ，皆 HTTP 200 確認）；同時受 Anthropic 今晚掛牌點燃儲存族群買氣帶動，SNDK 盤前漲逾 4%（https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，HTTP 200 確認）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### ARM｜安謀（Arm Holdings，ARM）今天 +4.5%（盤前）：隨那斯達克期貨與晶片族群盤前反彈；近期獲摩根士丹利上修資料中心權利金預估
- 事實：今日（11/19）盤前 ARM 未見新的單獨公司公告（找不到 11/19 當日單獨公司新聞來源），主要隨 Anthropic IPO 定價超預期推動那斯達克 100 期貨反彈約 1.9%–2%，與半導體板塊同步走高（https://www.tradingview.com/news/stocktwits:6243efa9f094b:0-nvda-intc-stocks-ease-post-5-day-rout-after-meeting-xi-jinping-trump-says-nvidia-blackwell-chips-could-reach-china-within-2-3-years/ ，HTTP 200）；近期基本面背景為摩根士丹利維持 `Equal-Weight` 評等但上修其 AI 資料中心 CPU 權利金預估（搜尋摘要，直連網址 `cryptobriefing.com` 回傳 HTTP 403）。

### INTC｜英特爾（Intel，INTC）今天 +4.3%（盤前）：隨晶片族群結束五連跌反彈，市場消化川普談 Blackwell 輸陸可能性與 18A 首家外部客戶進展
- 事實：在半導體類股連續五個交易日重挫後，受 Anthropic IPO 定價高於區間帶動 AI 與晶片股盤前反彈，加上美國總統川普於 APEC 深圳受訪稱兩至三年後不排除放行上一代 Blackwell 晶片輸陸，以及英特爾近期簽下 **18A 製程首位外部客戶**並宣布擴大與微軟合作，推動 INTC 盤前反彈約 3.8%–4.3%（https://www.tradingview.com/news/stocktwits:6243efa9f094b:0-nvda-intc-stocks-ease-post-5-day-rout-after-meeting-xi-jinping-trump-says-nvidia-blackwell-chips-could-reach-china-within-2-3-years/ ，HTTP 200 確認）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

---

### AN｜AN-1：最近 3 小時內（台北 15:45–18:45）無新增美股 AI／前 20 大權值股分析師調評；補齊高盛 AVGO 與摩根大通 HCA 驗證連結
- 事實：檢索最近 3 小時（台北 15:45–18:45／美東 11/19 02:45–05:45），AI 供應鏈與美國市值前 20 大公司未見新發布的美股券商調評（找不到來源）。
- 事實（近期報告與本輪完成 HTTP 200 驗證之直連網址）：
  1. **高盛 Goldman Sachs（AVGO，美東 11/19 01:26／台北 14:26 報導）**：分析師 James Schneider 維持 **AVGO** `Buy` 評等，因同業估值倍數壓縮（評估倍數由 30 倍下修至 25 倍），將價格看法由 $540 調降至 **$460**，但估 FY27／FY28 AI 營收仍高於市場預期 5% 與 9%（https://www.tokenpost.com/news/business/61151 ，John Kim 署名，HTTP 200 確認）。
  2. **Rothschild & Co Redburn（AVGO，11/13 報告）**：分析師 Mike Harrison 將 **AVGO** 由 Buy 調降至 **Neutral**，價格看法由 $595 調降至 **$398**，理由為對高舉債 AI 實驗室客戶集中風險（https://fr.tradingview.com/news/seekingalpha:f4cc47e04094b:0-broadcom-in-focus-as-rothschild-downgrades-to-neutral-but-flags-potential-upside/ ；https://www.tikr.com/blog/is-rothschild-co-redburn-wrong-to-give-up-on-broadcom-wall-street-still-sees-533 ，皆 HTTP 200 確認）。
  3. **摩根大通 JPMorgan（HCA，11/18 報告）**：維持 **HCA** `Neutral` 評等，將價格看法由 $425 調高至 **$475**（https://www.tradingview.com/news/tradingview:9eb3a7caf755c:0-jp-morgan-maintains-hca-healthcare-at-neutral-raises-price-target-to-475-from-425/ ，HTTP 200 確認）。
  4. **摩根士丹利（台積電 2330，11/19 亞太高峰會後報告，無新進展）**：維持 `Overweight` 評等與估值看法 **3,088 元**，2026–2028 年 EPS 估 **112.10／148.64／189.81 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，HTTP 200）。
  5. **輝達（NVDA）與其他近期機構報告（無新進展）**：Summit Insights 降評至 `Hold`（https://www.tikr.com/fr/blog/is-summit-insights-wrong-to-give-up-on-nvidia-wall-street-still-sees-251 ）；HSBC Frank Lee 降至 `Hold` 看法 $365→$170（https://www.tradingview.com/news/binance_news:d94dcaa1f094b:0-hsbc-downgrades-nvidia-says-stock-may-struggle-until-new-ceo-is-named/ ）；Evercore ISI Outperform→In-Line 看法 $186、Bernstein $400→$200、Baird Outperform→Neutral（https://www.tradingview.com/news/benzinga:3bce7f47b094b:0-nvidia-gets-10-bank-downgrades-after-huang-exit-what-to-expect-ahead-of-q3-results/ ）；Moody's 維持 `Aa1` 展望降至 `Stable`（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ）；KeyBanc 調升 PANW 至 `Overweight` 看法 $380（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ）；Piper Sandler 調升 MDT 至 `Overweight` 看法 $120（https://www.tradingview.com/news/tradingview:5b080eae6cc49:0-piper-sandler-upgrades-medtronic-to-overweight-from-neutral-raises-price-target-to-120-from-85/ ）。（Oracle 標普降評至 `BBB-` 為 2026-07-10 舊聞：https://bondblox.com/news/oracle-downgraded-to-bbb-by-sp ，特此更正時間點不當成今日調評。）

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）刊登聯邦公報生效，同日白宮馬尼拉 Quad 峰會聚焦可信賴超級智慧供應鏈（更新）
- 事實：美國商務部工業安全局（BIS）暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢至 2027-01-19），增訂 § 744.24 限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則（https://public-inspection.federalregister.gov/2026-23529.pdf ；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ；https://www.milbank.com/en/news/bis-issues-new-rule-restricting-remote-access-to-advanced-chips.html ，皆 HTTP 200）。
- 事實：白宮於 **11 月中旬（馬尼拉 Quad 領袖峰會）** 聯合澳、印、日發表聲明，鎖定關鍵礦產／半導體供應鏈安全與可信賴超級智慧（Super Intelligence）技術生態；另今日（11/19）FCC 舉行公開會議審議無人機規範，HHS HIPAA 隱私權修正案（`2026-23429`）與 CMS CRUSH 反詐欺草案（`2026-23461`）同列聯邦公報程序（https://public-inspection.federalregister.gov/2026-23461.pdf ，HTTP 200）。

### POL-2｜美國財政部 FinCEN 強化 CDD 提案、9 月 TIC 淨流入 2,610 億美元、OFAC 制裁與 USTR 談話（無新進展）
- 事實：財政部 FinCEN 發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，https://home.treasury.gov/news/press-releases/sb0691 ，HTTP 200）；9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ，HTTP 200）；OFAC「Operation Economic Outcast」制裁真主黨與聖城軍金流（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 重申美國優先貿易（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）。

---

### TW-1｜11/19 台股收跌 1,768 點（38,426.89 點）、櫃買暴跌 7.22%（285.33 點）、世界／台化／萬泰科爆 1.29 億違約交割；新台幣收升 32.942 元；金管會 11/20 升級 3.5% 限空令（更新違約交割與 HTTP 200 來源）
- 事實（11/19 台股收盤、三大法人與違約交割）：加權指數盤中下探 38,259.7 點（跌 1,935.21 點），終場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，失守年線 39,368 點）**，成交值 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ，HTTP 200）；櫃買指數收跌 **-7.22%（-22.22 點）至 285.33 點**，台積電收 **2,100 元（-75 元 / -3.45%）**。三大法人合計賣超 **461.03 億元**（**外資 -243.12 億元**、**投信 +15.13 億元**、**自營商 -233.03 億元**，其中自營商避險部位 **-214.40 億**，https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200）；期貨三大法人合計淨空單 **-8,883 口**（外資 **-99,219 口**、投信 **+91,791 口**、自營商 **-1,455 口**）。**盤後證交所與櫃買中心再通報 3 檔違約交割，合計金額達 1.29 億元**：包含上市**台化（1326）4,172.8 萬元**（元大和平分公司通報，今年上市第 20 起），以及上櫃**世界先進（5347）與萬泰科（6190）**（https://stock.ltn.com.tw/article/m7hjf9c9axqq ；https://inews.setn.com/news/1941815 ，皆 HTTP 200 確認）。
- 事實（11/19 新台幣收盤價）：台北外匯市場開 32.960 元，盤中貶破 33 元低見 **33.040 元**，在出口商拋匯與央行調節下，16:00 翻升收 **32.942 元（升值 0.5 分）**；台北外匯經紀成交 **22.63 億美元**、台北及元太兩大外匯市場總成交 **32.82 億美元**（https://www.cna.com.tw/news/afe/202611190296.aspx ；https://money.udn.com/money/story/12509/9889341 ，皆 HTTP 200 確認）。
- 事實（金管會 11/20 限空令 2.0）：（1）當日收盤跌幅達 **3.5%** 以上之上市櫃與 TDR，次一交易日禁止低於前收融券及借券放空（當沖未回補低於前收者亦不得改採融券／借券放空）；（2）每日盤中借券放空委託數量上限由前 30 日均量 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190182.aspx ，皆 HTTP 200）。

### TW-2｜台積電 11/19 正式公告約 5 億美元認購 Anthropic 602.4 萬股（補中央社 HTTP 200）；日月光仁武 2,489 億動土、鴻海 Ceer Motors 融資（更新）
- 事實：中央社記者張建中 11/19 16:46 報導，台積電（2330）正式公告由子公司 **TSMC Partners** 以每股 **83 美元**取得 Anthropic 普通股 **6,024,096 股**，總金額約 **5 億美元（499,999,968 美元，持股約 0.03%）**，依美國 1933 年證券法 Rule 144 一次付清作為長期股權投資（https://www.cna.com.tw/news/afe/202611190254.aspx ，HTTP 200 確認）。同日中央社引述智璞產研分析，Anthropic 轉向自建資料中心恐推升台積電 CoWoS 需求並牽動英業達、廣達、鴻海TPU 機櫃代工訂單（https://www.cna.com.tw/news/afe/202611190156.aspx ，HTTP 200）。
- 事實（其餘台鏈公告，無新進展）：日月光投控旗下台灣福雷電子高雄仁武 J 坵塊新廠 11/19 動土、計畫投資 **2,489 億元**（https://www.cna.com.tw/news/afe/202611190122.aspx ）；廣達田納西廠租約 1,490.8 萬美元（https://news.cnyes.com/news/id/6666244 ）；海龍 2A 綠電轉售台積電（https://www.cna.com.tw/news/afe/202611190102.aspx ）；鴻海 72.4 億日圓收購 Sony 車載相機事業（https://www.ctee.com.tw/news/20261119700316-439901 ）及沙國合資 Ceer Motors 獲 6.93 億美元銀行團融資；熊本清晨 M5.7 地震尚無 JASM 重大停工回報。
- 傳聞：外媒轉述《工商時報》稱台積電依客戶資產負債表設 AI 信用額度、超額須預付現金，尚未獲官方證實（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ）。

### TW-3｜SK 海力士 11/19 收漲 +3.41%、蘋果洽談三星多年期 DRAM 長約；亞股日韓印收紅、陸港台收黑（更新）
- 事實：《MoneyToday》11/19 報導 SK 海力士（000660.KS）收漲 **+3.41% 至 1,183,000 韓元**，與三星電子連兩日收高（https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ，HTTP 200 確認）；《The Korea Herald》11/19 報稱蘋果正進入與三星電子洽談多年期 DRAM 供應協議最後階段（https://www.koreaherald.com/article/10942672 ，HTTP 200）。11/19 亞股收盤：**日經 225 +0.71%（59,444.21）**、**KOSPI +1.39%（5,137.89）**、**印度 Nifty 50 +0.91%（25,458.75）**；**上證 -0.28%（3,577.62）**、**恆生 -1.95%（22,841.62）**、**台股加權 -4.40%（38,426.89）**。愛德萬測試與台韓出口數據保留（無新進展，https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ）。

---

### EARN-BABA｜阿里巴巴（BABA）已於 11/19 18:18 前公布 Q2 FY27 財報：營收 2,715.19 億元（+10% YoY）優於預期，但 Non-GAAP 淨利遜預期且 FCF 淨流出 344.72 億元致 ADR 盤前挫逾 2%（更新實績！）
- 事實：阿里巴巴於 **2026-11-19 美東盤前（台北 18:18 前）**正式發布截至 2026 年 9 月 30 日止 Q2 FY27 財報（電話會議訂於美東 07:00／台北 20:00）：總營收人民幣 **2,715.19 億元**（約 405.0 億美元，年增 **10%**），優於市場預期的 2,698.49 億元；經調整 EBITA 人民幣 **326.36 億元**（年增 **260%**）；歸屬股東淨利 **645.35 億元**，但 **Non-GAAP 淨利人民幣 199.09 億元（年增 92%）低於市場預期 265.7 億元**（Non-GAAP 每 ADS 盈餘人民幣 **8.10 元**，年增 86%）。AI 雲與算力服務收入年增 **53%** 至 **609.73 億元**（外部商業化收入年增 64%）；惟單季資本開支年增 **60%** 至 **504.77 億元**，導致**自由現金流淨流出擴大至 344.72 億元**（去年同期淨流出 218.4 億元），拖累其 ADR 盤前下挫逾 **2%**（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ；https://tw.tradingview.com/news/gelonghui:8dc9ebf5bacdf:0/ ，皆 HTTP 200 確認）。

### EARN-NTES｜網易（NTES）11/19 盤前公布 Q3 2026 財報，營收人民幣 279 億元（-1.8% YoY）低於預期，今晚 20:00 舉行法說（補官方 PR Newswire HTTP 200 連結）
- 事實：網易（NTES）於 **2026-11-19** 公布 Q3 2026 淨營收人民幣 **279 億元**（約 42 億美元，年減 **1.8%**，低於市場共識約 295 億～303 億元），遊戲及相關增值服務 **229 億元**（-1.7% YoY）、有道 **14 億元**（-12.3% YoY）、網易雲音樂 **19 億元**（-0.9% YoY）、創新業務 **15 億元**（+7.1% YoY）；毛利 **190 億元**（+4.8% YoY）、Non-GAAP 淨利 **92 億元**、Non-GAAP 每 ADS 基本盈餘 **2.13 美元**，季度股息調高至每 ADS **0.585 美元**；電話會議訂於美東 11/19 07:00（台北 20:00）（https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ，HTTP 200 確認）。

### EARN-WMT｜沃爾瑪（WMT）Q3 FY27 財報（今晚美東 11/19 07:00 發稿／台北 20:00、08:00 電話會議，無新進展）
- 事實：美東 **2026-11-19 07:00 財報、08:00 電話會議**（台北 **11/19 20:00／21:00**）；TradingView 彙整共識營收約 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）；選擇權隱含波動 **±5.78%～±6.4%**（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，皆 HTTP 200）。

### EARN-PDD｜拼多多（PDD）Q3 2026 財報（今晚美東 11/19 盤前／台北 20:30 電話會議，無新進展）
- 事實：美東 **2026-11-19 盤前**公布（電話會議 07:30 ET／台北 20:30）；TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS 約人民幣 **18.72～19.02 元**（約 **2.61～2.77 美元**）（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ，HTTP 200）。

### EARN-WSM / INTU / ROST / GAP｜今日（11/19）美東盤前與盤後其餘財報（無新進展）
- 事實：
  - **WSM（盤前／台北 11/19 23:00 電話會議）**：共識營收 **19.8 億～20.0 億美元**、EPS **2.19 美元**（https://www.tradingview.com/news/tradingview:5796c7c550438:0-wsm-q3-26-earnings-eps-estimate-is-2-19-usd/ ，HTTP 200）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（原財測 2.44–2.48 美元），隱含波動 ±8.9%–10.5%（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ，HTTP 200）。
  - **ROST（盤後／台北 11/20 05:00）**：共識營收 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ，HTTP 200）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ，HTTP 200）。

### EARN-HPE / ZM / BBY / BURL / DKS / ADI / MDT / DELL / HPQ / ADSK / WDAY / BILI / DE｜11/23–11/25 未來 10 天財報（無新進展）
- 事實：
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（公司財測 1.20–1.30；波動 ±9.7%，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ，HTTP 200）；**ZM** Zacks 共識營收 **12.8 億美元**、EPS **1.49 美元**（https://www.zacks.com/stock/news/3030700/zoom-communications-zm-falls-more-steeply-than-broader-market-what-investors-need-to-know ，HTTP 200）。
  - **11/24 盤前（台北 20:00–21:00）**：**BILI** MarketBeat 共識營收 **12.3 億美元**、EPS **0.23–0.27 美元**；**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**（https://www.tradingview.com/news/tradingview:6917007d5e261:0-burl-q3-26-earnings-revenue-estimate-is-2-97b-usd/ ）；**DKS** 營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ）；**ADI** FactSet 共識營收 **43.2 億美元**、EPS **3.88 美元**（https://www.tradingview.com/news/tradingview:4441db86105da:0-adi-q4-26-earnings-revenue-estimate-is-4-32b-usd/ ）；**MDT** FactSet 共識營收 **94.8 億美元**、EPS **1.33 美元**（https://es.tradingview.com/news/tradingview:dcc2d0d8b8c99:0-mdt-q2-26-earnings-revenue-estimate-is-9-48b-usd/ ）；**BBY** Zacks 共識營收 **98.8 億美元**、EPS **1.48 美元**（https://www.zacks.com/stock/news/3031155/best-buy-bby-reports-next-week-wall-street-expects-earnings-growth ）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億～492.5 億美元**、EPS **6.41–6.60 美元**（波動 ±14.85%，https://www.tradingview.com/news/tradingview:e525c4bdcb809:0-dell-q3-26-earnings-revenue-estimate-is-49-25b-usd/ ）；**WDAY** 營收 **26.9 億美元**、EPS **2.75 美元**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ）；**HPQ** FactSet 共識營收 **154.3 億美元**、EPS **0.75 美元**（https://in.tradingview.com/news/tradingview:2627939d5b773:0-hpq-q4-26-earnings-revenue-estimate-is-15-43b-usd/ ）；**ADSK** MarketBeat 共識營收 **21.3 億美元**、EPS **3.07 美元**（https://www.marketbeat.com/instant-alerts/upcoming-autodesk-adsk-set-to-announce-quarterly-earnings-on-tuesday-2026-11-17/ ）。
  - **11/25 盤前（台北 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ）。
  - （註：11/26–11/29 感恩節週其餘大廠多休整；12/01 盤後 CRWD/MRVL/OKTA 與 12/02 盤後 CRM/SNOW/ZS 超過 10 天窗外。）

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ，HEAD 200 確認）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（強烈偏升息，無新進展）
- 事實：Waller 於 11/18 受訪指出聯準會可能需要「shock people」壓抑通膨預期固著，12/8–9 會議應考慮一次升息 50 基點（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ）。

### FED-3｜聯準會理事 Michael S. Barr（偏升息）、紐約聯準銀行總裁 John Williams（反對一次升息 2 碼）；今晚 Goolsbee 問答與理事會貼現率閉門會議（無新進展）
- 事實：Barr 11/18 在紐約聯準銀行演說指出通膨仍過高、適合進一步升息並示警 AI 代理資金調撥風險（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ，HEAD 200 確認）；Williams 對談反對 12 月一次升息 0.50%（`"I don't see a need for dramatic action right now"`，偏漸進升息，https://www.chosun.com/english/market-money-en/20261119/3ZAB4T3MGVF4HLNUXPSHRHLNCI/ ）。今日稍後芝加哥聯準銀行總裁 Goolsbee 將於 **美東 11/19 12:30（台北 11/20 01:30）**於印第安納經濟俱樂部參與座談問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ，HEAD 200）；聯準會理事會於 **美東 11/19 15:00（台北 11/20 04:00）**召開閉門貼現率會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ，HEAD 200）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼約 90%–95%、升息 2 碼約 5%–10%（無新進展）
- 事實：聯邦基金期貨幾乎完全定價 12/9 升息 1 碼（各報導引述 CME FedWatch 介於 **90%–97%**），升息 2 碼約 **3%–10%**（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ，HEAD 200 確認）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，HTTP 200 確認）。
- 事實：核心 PCE（3.1%）高於核心 CPI（2.6%）之結構主因，係 2026 年住房／房租通膨降溫拉低權重較大的 CPI，而醫療服務、金融與軟體科技服務權重在 PCE 籃子較高且價格較黏著（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。

### TASK-B2｜11/19 台股收跌 1,768.02 點收 38,426.89 點（櫃買收 285.33 點、跌 7.22%）、外資現貨賣超 243.12 億、三大法人台指期合計淨空單 -8,883 口、新台幣收升至 32.942 元（補齊中央社匯市與違約交割 HTTP 200 來源）
- 事實（11/19 收盤與三大法人現貨／違約交割）：集中市場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，破年線）**，成交金額 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ，HTTP 200）；櫃買指數收 **285.33 點（-22.22 點 / -7.22%）**。三大法人合計賣超 **461.03 億元**，其中 **外資及陸資賣超 243.12 億元**、**投信買超 15.13 億元**、**自營商合計賣超 233.03 億元**（含避險 -214.40 億元，https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200）。盤後另爆出世界、台化（4,172.8 萬元）、萬泰科合計 **1.29 億元**違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ，HTTP 200）。
- 事實（11/19 期交所三大法人台指期未平倉）：期交所 `futContractsDate` 公布臺股期貨三大法人合計淨空單為 **-8,883 口**（外資 **-99,219 口**、投信 **+91,791 口**、自營商 **-1,455 口**）。
- 事實（11/19 新台幣 16:00 收盤價）：開 32.960 元，盤中低見 **33.040 元**，16:00 在央行調節與出口商拋匯下翻升收 **32.942 元（升值 0.5 分）**；台北外匯成交 **22.63 億美元**、台北及元太總成交 **32.82 億美元**（https://www.cna.com.tw/news/afe/202611190296.aspx ；https://money.udn.com/money/story/12509/9889341 ，皆 HTTP 200 確認）。金管會並宣布 **11/20 起升級 3.5% 限空令**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ，HTTP 200）。

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；補齊台積電公告入股 HTTP 200 網址
- 事實：Anthropic（代號 **ANT**）定價 **每股 83.00 美元**（發行 9.8 億股、IPO 募資 **813.1 億美元**、加上晶片與雲端夥伴 260 億美元同步私募合計約 1,073 億美元、完全稀釋估值約 **1.5 兆美元**），將於 **美東 2026-11-19 09:30（台北 11/19 22:30）** 掛牌；截至台北時間 18:45（美東 05:45）美股尚未開盤，首日開盤價、收盤價與成交量將於明早 05:00 收盤後產生（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，HTTP 200）。
- 事實：台積電 11/19 正式公告透過 TSMC Partners 以 **每股 83 美元**取得 Anthropic 普通股 **6,024,096 股**（約 **5 億美元**，https://www.cna.com.tw/news/afe/202611190254.aspx ，HTTP 200）。掛牌前夕美東 11/18 收盤，**CoreWeave（CRWV）跌 4.13%、IREN 跌 3.61%、Nebius（NBIS）小漲 0.87%、Oracle（ORCL）大致持平**；同日 **NVDA 收跌約 2.9%**，**AVGO、AMD 上漲約 4%–5%**（https://247wallst.com/investing/2026/11/18/coreweave-falls-5-despite-nvidia-sticking-to-its-financing-commitments-nebius-dips-oracle-holds-steady/ ）。

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字（無新進展）
- 事實：ECB 11/18《金融穩定評估》Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（基於 LSEG 10/26 共識），指多數美國超大規模雲端業者 2026 年自由現金流因 AI 資本支出大於營運現金流而轉負（表層 FCF 口徑未納入未起租的表外租賃；表外承諾逾 4 兆美元係於圖表 A 與註腳 6 依 ASC 842 單獨揭露）（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200 確認）。
- 事實：四巨頭截至 2026-09-30 最新一季自報實際數字：Meta（Q3 2026）OCF $32.79B − CapEx（含融資租賃本金）$34.91B = **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ，HEAD 200）；Alphabet（Q3 2026）OCF $42.29B − 現金 PP&E $51.36B = **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ，HEAD 200）；Amazon（Q3 2026／TTM）Q3 單季 OCF $42.42B、淨現金 PP&E $75.93B（單季隱含 -$33.51B）、自報 **TTM FCF -$42.36B**（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ，HEAD 200）；Microsoft（Q1 FY27）OCF $58.02B − 現金 PP&E $39.37B = **+$18.6B（仍為正；計入新起租融資租賃總資本支出 $45.2B 後仍約 +$12.8B）**（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ，本輪回傳 HTTP 403，保留前輪讀數）。

### TASK-B5｜阿里巴巴（BABA）11/19 已搶先公布 Q2 FY27 財報（補實績與 CFO 原話）；WMT、PDD 尚未發布（今晚 20:00 起陸續公布）
- 事實（阿里巴巴 BABA，Q2 FY27，**已公布**）：總營收人民幣 **2,715.19 億元**（+10% YoY，勝於香港 01 所列市場預期 2,698.49 億元），但 **Non-GAAP 淨利 199.09 億元（+92% YoY）遜於預期 265.7 億元**（Non-GAAP 每 ADS 盈餘 8.10 元）、資本支出飆升 60% 至 504.77 億元、自由現金流淨流出 **344.72 億元**，ADR 盤前挫逾 2%；CFO 徐宏對 AI 投資原話：`「隨著AI商業化不斷深入，我們會繼續審慎根據市場情況投入AI建設，注重提升資本回報率，並致力於盡早實現自由現金流轉正。」`（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ，HTTP 200 確認）。
- 事實（沃爾瑪 WMT，Q3 FY27，**尚未公布，美東 07:00／台北 20:00**）：TradingView 彙整市場共識營收 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）；執行長 John Furner 對關稅與消費原話：`"Customers are feeling some pressure, so we're proud of our investments... We'll do everything we can to keep prices as low as we can for customers throughout the rest of the year."`（https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ；https://www.businessinsider.com/walmart-using-tariff-refund-price-cuts-customer-experience-sales-2026-8 ）。
- 事實（拼多多 PDD，Q3 2026，**尚未公布，電話會議美東 07:30／台北 20:30**）：TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS **2.61～2.77 美元**，市場聚焦跨境小額免稅與關稅對 Temu 利潤率影響（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ）。

---

### CALL｜法說會重點（過去 24 小時；NTES 與 BABA 電話會議皆訂於台北今晚 20:00 舉行）

### CALL-PANW｜Palo Alto Networks（PANW）Q1 FY27 法說會：NGS ARR 年增 66%、斥資 45 億美元併購 Applied Compute（無新進展）
- 原話（CEO Nikesh Arora）：`"As AI reshapes the threat landscape, we must continually evolve to protect our customers and enable them to adopt AI securely. To that end, we are pleased to announce our intent to acquire Applied Compute, which will allow us to deliver secure open weight models to our customers and accelerate the adoption of enterprise AI."`（https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，HTTP 200）。

### CALL-P｜Everpure（NYSE: P，原 Pure Storage）Q3 FY27 法說會：營收年增 51%、連三季上調全年財測（無新進展）
- 原話（CFO Tarek Robbiati）：`"Our results reflect the strength of our diversified portfolio, with our core and core AI offerings complemented by increasing contributions from our new businesses. We are raising full-year guidance for the third consecutive quarter and reiterating our strong preliminary FY28 outlook, underscoring confidence in our durable business model and broad-based momentum."`（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ，HTTP 200）。

### CALL-NVDA｜輝達（NVDA）Q3 FY27 法說會：營收 1,158 億美元、下季財測排除中國（無新進展）
- 原話：`"Our momentum is real... Customers, suppliers, and partners are 100% behind us. We’ve got this."`（https://www.cnbc.com/2026/11/18/nvidia-stock-earnings.html ）。

### CALL-LOW｜Lowe's（LOW）Q3 2026 法說會：同店 +1.8%，2.5 億美元關稅退稅全數再投資（無新進展）
- 原話：`"We delivered strong top-line growth of over 9%, led by our sixth consecutive quarter of positive comparable sales, with continued momentum in Pro, online and home services."`（https://corporate.lowes.com/sites/lowes-corp/files/2026-11/q3-2026-press-release-v1.pdf ）。

### CALL-TGT｜Target（TGT）Q3 2026 法說會：同店成長 5.6%、全年 EPS 指引上調至 10.65–11.40 美元（無新進展）
- 原話：`"Our third-quarter results reflect continued progress against our strategic priorities, centered on serving busy families with our signature blend of style, design and value."`（https://www.prnewswire.com/news-releases/target-corporation-reports-third-quarter-earnings-302942872.html ）。

### CALL-TJX｜TJX Companies（TJX）Q3 FY27 法說會：同店成長 4%，上調全年展望至區間上緣（補 MLQ HTTP 200 來源）
- 原話：`"Consolidated comparable sales grew 4%, driven by continued strength at HomeGoods, TJX Canada, and TJX International, and we saw improved sales at Marmaxx. Importantly, we expect further improvement at Marmaxx in the fourth quarter."`（https://mlq.ai/news/tjxs-comparable-sales-rise-4-above-its-plan-and-it-narrows-its-full-year-outlook-toward-the-top-of-the-range/ ，HTTP 200）。

---

### NEXT-1｜事件：台股櫃買暴跌 7.22%＋盤後再現 1.29 億違約交割（世界／台化／萬泰科）＋金管會 11/20 升級 3.5% 限空令
- 推理：
  - 最先受影響的資產：明日（11/20）適用平盤下禁空之跌幅 ≥3.5% 台股與 TDR、櫃買高融資中小型 AI 股、台指期避險部位，以及權證造市券商帳上部位。
  - 傳導路徑：今日自營商賣超 233.03 億元中有 **214.40 億元**來自避險賣超，盤後證交所與櫃買中心緊接通報世界、台化（4,172.8 萬）、萬泰科合計 **1.29 億元**違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），金管會遂將 11/20 起借券上限由 3% 砍至 1% 並啟用 3.5% 跌幅平盤下禁空（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）：
    - 美股：**TSM（ADR）、NVDA、AVGO、SOXX、EWT**。
    - 台股：**台積電 (2330)、聯發科 (2454)、世界 (5347)、台化 (1326)、元大金 (2885) 等券商金控**。
  - 大家還沒注意到的間接受害者：**承銷高價 AI 認購權證的台灣中小型券商自營部與證券融資授信部門**——當個股借券與平盤下放空受限、自營避險單轉擠入台指期（三大法人期貨淨空單已達 -8,883 口），中小型股若買盤縮手更容易出現「無量鎖跌停」，放大 T+2 違約交割由證券商先代墊後的短期呆帳與資本適足率壓力。

### NEXT-2｜事件：阿里巴巴 Q2 FY27 因 AI CapEx 暴增致 FCF 淨流出 344.72 億、ADR 盤前挫逾 2%＋Anthropic 今晚 22:30 納斯達克掛牌
- 推理：
  - 最先受影響的資產：中概科技股 ADR（BABA、PDD、BIDU、KWEB）、美系雲端大廠長債利差，以及今晚掛牌之 ANT 與新雲端族群（CRWV、NBIS、IREN）。
  - 傳導路徑：繼 ECB Box 3 揭露美系超大規模雲端商多數轉為負自由現金流後，BABA 今晚實績證明即使 AI 雲收入年增 53%，只要 CapEx 激增 60% 拖累自由現金流（-344.72 億人民幣），股票仍會在盤前直接遭到懲罰（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ）；若今晚 22:30 Anthropic 掛牌未能強勢守穩 83 美元之上，高資本支出、負 FCF 的「算力燒錢鏈」將面臨同步重估：
    - 美股：**BABA、ORCL、CRWV、NBIS、AMZN**。
    - 台股：**廣達 (2382)、緯穎 (6669)、鴻海 (2317)、英業達 (2356)、台達電 (2308)**。
  - 大家還沒注意到的間接受益者：**已具備高自由現金流防禦墊且資本支出節奏可控的資安軟體與低負債現金牛企業（如 PANW、TJX）**——當市場開始對「CapEx 吞噬 FCF」的基礎建設端要求折價，能靠軟體訂閱（PANW NGS ARR +66%）與庫存周轉快速變現的公司更容易吸納科技股撤出資金。

### NEXT-3｜事件：IEA 警告荷莫茲危機超越 1970 年代＋胡塞飛彈碎片擊中沙國 PIF 利雅德總部＋歐盟遭 AI 網攻＋德國妥協 UniCredit 併購
- 推理：
  - 最先受影響的資產：波灣主權債與阿拉伯聯合大公國／沙國美元債信用利差、布蘭特遠月原油曲線、歐洲銀行股（EUFN）與歐系資安股。
  - 傳導路徑：沙國主權財富基金（PIF）總部大樓在首都金融區遭飛彈碎片波及（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ），加上 IEA 警告波灣已損失 28 億桶原油與緩衝庫存耗盡（https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ）；同日歐盟執委會則因 AI 滲透工具網攻而出現人資與醫療系統中斷逾 10 天（https://www.dailysabah.com/business/tech/european-commission-hit-by-cyberattack-report ）：
    - 美股：**XOM、CVX、FRO、PANW、CRWD**。
    - 台股：**長榮 (2603)、陽明 (2609)、台塑化 (6505)、中華電 (2412)、安碁資訊 (6690)**。
  - 大家還沒注意到的間接受害者：**高度依賴中東主權財富基金（如 PIF）作為晚期募資或基石投資人的私募股權與基礎建設基金**——若利雅德金融區安全風險與油價波動雙升迫使波灣主權基金把更多現金留作本土防衛與財政緩衝，全球私募基金 2027 年募資來源將比市場預期更快收緊。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 由 60% 降至 45%）」
- 最強反方證據：BEA 官方新聞稿已證實 9 月核心 PCE 年增確為 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ），The Conference Board 預估 10 月將升至 **3.3%**（https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026 ），且本站線上《財經日曆》卡片亦已載明 9 月為 `3.1%` 並自估 10 月為 `3.2%`。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法發布年增率，這題將成為「無法判定」；但只要有公布年增率，低於 3.0% 的空間極小。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：維持落在 2.4%–3.0% 僅約 **30%**（比你的 45% 低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露多數美系一線雲端商 FCF 轉負且表外承諾逾 4 兆美元（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ），今日 BABA 亦因 CapEx 增 60% 使 FCF 淨流出 344.72 億人民幣致 ADR 盤前跌逾 2%；IEA 11/19 警告荷莫茲構成史上最大能源威脅加上利雅德 PIF 大樓遭飛彈碎片波及；台股櫃買跌 7.22%、再現 1.29 億違約交割迫使金管會升級 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。
- 另一種同樣說得通的解釋：今日新台幣翻升收 32.942 元、日經（+0.71%）、韓股（+1.39%）、印度（+0.91%）收紅、歐股 STOXX 600 早盤 +0.3% 且 UniCredit 併購僵局化解，顯示壓力仍集中在高槓桿 AI 資本支出與籌碼面，尚未演變成無差別信貸擠兌。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：維持「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你的 80% 低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：11/18 美國 EIA 原油庫存暴增 340 萬桶、汽油暴增 520 萬桶（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ）壓低近月油價；另一端 IEA 11/19 警告荷莫茲已造成史上最大斷供（28 億桶原油）且今日胡塞飛彈碎片擊中沙國 PIF 利雅德總部（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ），形成雙尾拉扯。
- 另一種同樣說得通的解釋：庫存過剩與強美元容易把 WTI 壓破 80 美元，而實質波灣衝突外溢則可能瞬間衝破 100 美元——突破區間外的機率高於表面波動率所反映的水準。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **未來 72 小時波灣與荷莫茲海峽安全動態**。
- 機率估計：維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」（無新進展）
- 最強反方證據：中央社 11/19 引述《福斯新聞》報導川普親口指出，與黃仁勳有染的一名女子正遭美國政府調查是否為中國情報機構工作、以及是否協助走私晶片（https://www.cna.com.tw/news/aopl/202611193003.aspx ，HTTP 200）；同日輝達董事長瓊斯對員工重申「黃仁勳個人行為及缺乏坦誠」是董事會接受辭呈且永不回鍋的原因（https://www.cna.com.tw/news/aopl/202611190029.aspx ）。
- 另一種同樣說得通的解釋：最初的確是「個人行為／缺乏坦誠」引發董事會 11/11 立即切割，但因牽涉對象本身被美方列為中國情報與晶片走私調查標的，**兩件事並非互斥，而是同一人物同時觸發公司治理與國安出口調查**。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節，11 月下旬～12 月初）**與 **美國政府對該涉案女子／走私網絡之起訴或調查公告**。
- 機率估計：維持「單純私人治理、完全無涉中國晶片調查」**25%–30%**，「個人行為與中國晶片／情報調查兩線交織」**70%–75%**。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（無新進展）
- 事實：ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**（已超過帳上負債），且投資級科技長債利差已相對於同評級企業債走寬（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q `Commitments and Contingencies / Uncommenced Leases` 追蹤，及 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜缺少「非公開交易 BDC 限額贖回（Gating）、私募信貸 SaaS 曝險與對沖基金主權債槓桿」監測（無新進展）
- 事實：FSB、聯準會 FEDS Notes 與 IMF／BIS／ECB 報告均聚焦非公開交易 BDC 限額贖回、私募信貸 SaaS 曝險與避險基金主權債槓桿。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜缺少「高集中度雲端／金融／公部門資安中斷與 SEC Item 1.05 資安事件」警報（更新）
- 事實：今日（11/19）歐盟執委會證實遭 AI 滲透工具 ARTEX 網攻導致內部核心系統中斷逾 10 天（https://www.dailysabah.com/business/tech/european-commission-hit-by-cyberattack-report ，HTTP 200）。
- 推理：監測 SEC 8-K Item 1.05 是否涉及高集中度第三方基建（AWS、Azure、GCP、Cloudflare、DTCC），可比股價更早捕捉系統性運作風險。免費資料源：CISA KEV JSON（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）＋ SEC EDGAR。

### BLIND-4｜「台股籌碼風向計」未自動加總「三大法人台指期合計淨口數」、且缺「每日違約交割金額」與「限空令燈號」（更新）
- 事實：今日證交所與櫃買中心再爆世界、台化（4,172.8 萬元）、萬泰科共 **1.29 億元**違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），金管會並宣布 **11/20 起升級 3.5% 限空令**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ，皆 HTTP 200），但目前「台股籌碼風向計」尚未加總三大法人台指期合計淨口數（11/19 -8,883 口），也未設「每日違約交割金額」與「限空令狀態」欄位。免費資料源：期交所「三大法人區分各期貨契約交易資訊」、證交所 `BFI82U` 與「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」（無新進展）
- 推理：建議在「IPO 觀察」補上大型 IPO 納入 S&P 500、Nasdaq-100 指數時程與被動 ETF 權重排擠效應說明。

---

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets）— 掛牌日情緒極度分歧，爭論首日行情、早期解禁與 Token 經濟學（更新）
- 討論內容與情緒：11/19 今日 Reddit 財經串熱議 ANT 以 83 美元定價、募資逾 810 億美元於那斯達克掛牌，部分交易員賭開盤流動性衝高，但大批反方警告早期內部人解禁與推理獲利模式，並穿插「GTA 6」等迷因調侃市場流動性（情緒，非事實；Reddit 網頁端於自動化抓取回傳 HTTP 403，以搜尋摘要與前輪已讀串 https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ 為準）。

### SENT-2｜PANW 併購與總經升息壓力（r/wallstreetbets / r/stocks）— 肯定資安併購動能但對 Fed 鷹派訊號謹慎（更新）
- 討論內容與情緒：今日討論同時關注 PANW 斥資 45 億美元收購 Applied Compute 帶動的資安盤前漲勢，以及聯準會官員偏鷹言論下科技與成長股數月來回檔的壓力（情緒，非事實；Reddit 串 https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ 與 11/19 搜尋摘要）。

### SENT-3｜台股 11/19 暴跌 1,768 點後「金管會限空令 2.0」（PTT 股板）— 熱議 3.5% 平盤下禁空是止血還是抽乾流動性（更新）
- 討論內容與情緒：11/19 下午金管會公告自 11/20 起實施「跌幅 ≥3.5% 個股隔日禁平盤下放空＋盤中借券上限降至 1%」，PTT 股板即時轉載 `[情報] 金管會發布限空令`（https://www.pttweb.cc/bbs/Stock/M.1795069467.A.DAC ，HTTP 200 確認），同步熱議台化、世界、萬泰科爆出 1.29 億違約交割與大摩對台積電 3,088 元看法（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，HTTP 200），盤後情緒在「政策救市護盤」與「怕無量鎖跌停」之間兩極拉鋸（情緒，非事實）。

### SENT-4｜NVDA 與沃爾瑪（WMT）財報（r/wallstreetbets）— 押注今晚 WMT 檢驗美國消費韌性（無新進展）
- 討論內容與情緒：押注今晚美東 07:00 公布的 WMT 財報將驗證美國底層與中產階級消費健康度，並持續在 NVDA 財報後爭論接班與估值修正（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ）。

### SENT-5｜UNH／醫療保險（r/stocks）— CMS CRUSH 規則陰霾下情緒偏悲觀（無新進展）
- 討論內容與情緒：醫療保險股受 CMS CRUSH 追溯 2018 年審計草案衝擊，散戶對管理式醫療與醫院類股情緒偏悲觀觀望（情緒，非事實）。

---

### SITE｜挑本站的錯（對照 2026-11-19 18:22–18:32 線上即時版 `https://wallstreet-sentinel.pages.dev` 與 `upcoming.json`、以及本地 `research_feed/`）

### SITE-1｜`research_feed/forecast.json` 仍寫「9 月核心 PCE 數字：查無」，但線上《財經日曆》早已顯示 3.1%（18:30 重讀確認仍在）
- 本站寫了什麼：`research_feed/forecast.json` 第 130 行仍寫著 `9 月核心 PCE 數字：查無。`。
- 正確應該是什麼：BEA 官方新聞稿早已公布 9 月核心 PCE 年增 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，HTTP 200），且本站線上《財經日曆》PCE 卡片亦已載明此數值，應將前值同步回 `forecast.json`。

### SITE-2｜線上總覽「17:32 盤中」語音稿稱台股跌 4.4%「沒找到時間對得上消息」，且「前幾班 16:34 緊急加班」仍稱能源股跌「原因還不知道」
- 本站寫了什麼：線上總覽 `11-19 17:32 台北 盤中` 語音稿寫道：`「至於原因，我沒有找到時間對得上的單一消息」`；同頁「前幾班」內的 `16:34 緊急加班` 仍寫著 `「能源這邊，我找不到時間對得上的原因…埃克森美孚和雪佛龍各跌約四趴。原因還不知道。」`（同時 `sessions.json` 仍寫「結論：沒有找到時間對得上的消息」）。
- 正確應該是什麼：今日台股急殺有明確當日籌碼與政策數據——自營商避險大砍 **214.40 億元**（幾乎等同外資 -243.12 億，https://www.cna.com.tw/news/afe/202611190200.aspx ）、櫃買重挫 **7.22%**、上市櫃盤後再爆 **1.29 億元**違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），促使金管會宣布 **11/20 起升級 3.5% 限空令**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；而 11/18 能源股下跌亦有美東 10:30 EIA 原油／汽油庫存暴增與雪佛龍除息 1.78 美元可對照。

### SITE-3｜線上 `upcoming.json`（18:27 版）尚未反映阿里巴巴（BABA）已公布的 Q2 FY27 實績、WMT 公布時間晚 1 小時、HPE 共識略低且漏列今晚 INTU／ROST／GAP
- 本站寫了什麼：`https://wallstreet-sentinel.pages.dev/upcoming.json`（`asof: "2026-11-19 18:27"`）仍將 `BABA` 列為尚未公布的 `2026-11-19T08:00`（台北 21:00）預告、將 `WMT` 時間列為 `08:00`（台北 21:00）、將 `HPE` `eps_f` 列為 `1.17`，且未收錄今晚盤後之 `INTU`、`ROST`、`GAP`。
- 正確應該是什麼：BABA 已於 11/19 18:18 前公布 Q2 FY27 財報（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ）；WMT 官方預告發稿為美東 **07:00（台北 20:00）**、08:00 才為電話會議（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ）；`HPE` 市場共識調整後 EPS 為 **1.27–1.29 美元**（https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ）。

### SITE-4｜線上《未來 14 天事件》（18:22 版）仍未標明今日美債標售為「10 年期 TIPS」
- 本站寫了什麼：線上 `p-news` 分頁《未來 14 天事件》（`最後更新 11-19 18:22`）列 `11-19 美債 10 年期標售（增額） $19B`。
- 正確應該是什麼：今日 $19B 增額標售為 **10 年期 TIPS（抗通膨公債）**（https://www.treasurydirect.gov/auctions/announcements-data-results/ ），建議標明「TIPS」以免新手與一般 10 年期名目公債標售混淆。

（註：前版指出的 `10:33 緊急加班` 台股「昨天跌 3.4%」與 `api/gemini_ask` `CNQ +3.2%（盤前）` 兩項，已於最新 `17:32` 盤中版與 `18:32` 題目單修正為 `-4.4%` 與 `CNQ -4.6%`，本輪不再重複報錯。）

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆（對照 11-19 18:22 線上版《未來 14 天事件》與 18:27 `upcoming.json`）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳川習會與美中俄三方峰會（已結束）；南非央行維持 7.25% 不變（已公布）；BABA、NTES Q3 財報（已公布）；台北 20:00 **WMT 財報／NTES、BABA 法說**、20:30 **PDD 法說**；美東 09:30（台北 22:30）**Anthropic (ANT)、MapLight (MPLT)** 掛牌；美東 12:30（台北 11/20 01:30）芝加哥聯準銀行總裁 Goolsbee 問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；美東 13:00（台北 11/20 02:00）**美債 10 年期 TIPS 增額標售 $19B**；美東 15:00（台北 11/20 04:00）聯準會理事會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP** 財報（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  2. **11/20（五）**：**台股金管會 3.5% 有條件限空令與盤中借券上限 1% 正式上路**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；**印度強氣旋「阿克萬」中午登陸奧里薩邦**；**台灣經濟部 10 月外銷訂單**（台北 16:00，https://money.udn.com/money/story/10869/9879179 ）；**美股月選擇權到期（OPEX）**；**密大消費者信心指數終值**（美東 10:00／台北 23:00）；**SanDisk (SNDK) 1 拆 8 拆股後首日交易**（https://www.fool.com/investing/2026/11/16/sandisk-splits-its-stock-8-for-1-on-nov-19-flash-memory-prices-still-matter-more-than-the-share-count/ ）。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM** 財報。
  5. **11/24（二）**：美東盤前（台北 20:00–21:00）**ADI、MDT、BBY、BURL、DKS、BILI**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY**。
  6. **11/25（三）**：美東盤前（台北 21:00）**DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與 10 月耐久財訂單；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**；台北 11/26 **宏于電機（台股）掛牌**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/28（六）**：**台灣 2026 九合一地方選舉投票日**。
  10. **11/29（日）**：**OPEC+ 聯合部長級監督委員會（JMMC）會議**。
  11. **11/30（一）**：**MSCI 季度調整台股收盤生效（台北 13:30）與月底資產再平衡**。
  12. **12/01（二）**：美東 10:00（台北 23:00）**ISM 製造業 PMI 與 10 月 JOLTS 職位空缺**；**CRWD、MRVL、OKTA、NTAP** 盤後財報；**韓國 11 月出口初值**。
  13. **12/02（三）**：美東盤後（台北 12/03 05:00）**CRM、SNOW、ZS** 財報（https://www.tradingview.com/news/tradingview:c28752bb00e6f:0-zscaler-hosts-2026-investor-day-reaffirms-q1-and-fiscal-2027-guidance/ ）。
  14. **12/03（四）**：美國參議院資料中心聽證。
- 對照本站 11/19 18:22 線上版《未來 14 天事件》與 18:27 `upcoming.json`：
  - **正確部分**：`未來 14 天事件` 已列 11/19 `H.4.1`、`Unemployment Insurance Weekly Claims Report`、`美債 10 年期標售（增額）$19B`、11/20 `OPEX`、11/25 `Debt to Gross Domestic Product Ratios` / `Gross Domestic Product` / `Personal Income and Outlays`、11/30 `月底資產再平衡`、12/01 `JOLTS`；`upcoming.json` 已列 WMT/BABA/PDD、ANT/MPLT、HPE、ADI、MDT、DELL、HPQ、DE。
  - **漏掉與錯列部分**：《未來 14 天事件》仍漏掉 **11/20 金管會限空令 2.0 上路與 SNDK 拆股、11/20 台灣 10 月外銷訂單、11/21 韓國 20 日出口、11/25 聯準會褐皮書、11/26 韓國央行、11/26 感恩節休市與 11/27 半天交易、11/28 台灣九合一選舉、11/29 OPEC+ JMMC 會議**；`upcoming.json` 仍漏掉 **INTU、ROST、GAP（今晚盤後）、ZM、BBY、BURL、DKS、ADSK、WDAY、BILI**，且 11/19 18:22 版將 `11-19 美債 10 年期標售` 漏標「TIPS」。

---

### CODE-1｜wsb/analytics/fomc_drift.py：第 110、137、151 行 `str(q.get("asof", ""))[:10] > asof` 遇 `asof` 為 `None` 時把 `"None"` 當最新日期，會誤增交易日計數並覆寫日期
- 檔案路徑與行號：`wsb/analytics/fomc_drift.py` 第 110–111 行（`build()` 函式）、第 137–138 行（`after()` 函式）與第 151–152 行（`after()` 利率／美元／VIX 迴圈）。
- 那一行在做什麼：比較即時報價 `q` 的日期 `asof` 是否比歷史日線最新一根收盤 `asof` 還新，若較新就用即時報價取代歷史收盤來算 FOMC 會前／會後累積報酬，且第 138 行會把決議後交易日數 `n` 加 1。
- 為什麼有問題：如果即時報價字典 `q` 存在 `"asof"` 鍵但值為 `None`，`q.get("asof", "")` 會回傳 `None` 而非 `""`，`str(None)[:10]` 變成 `"None"`。在 Python 字串比較中，`'N'` 的字碼大於 `'2'`，所以 `"None" > "2026-11-18"` 結果為 **`True`**。第 112 行與第 138 行會把 `asof` 寫成 `"None"`（頁面顯示 `asof[5:]` 成為空字串 `""`），第 138 行還會把 `n` 誤加 1，甚至在第 151 行把缺日期的報價當成最新殖利率／VIX。
- 建議怎麼改：在三個位置均改用 `(str(q.get("asof") or "")[:10]) > asof`（先確認值非空且格式像 `YYYY-MM-DD` 才覆蓋）。
- 確定度：高。

### CODE-2｜wsb/analytics/rally.py：第 57 與 75 行 `str(x.get("asof", ""))[:10]` 遇 `asof` 為 `None` 時會通過當日新鮮度檢查，讓缺日期報價混入盤中全面上漲掃描
- 檔案路徑與行號：`wsb/analytics/rally.py` 第 57 行（`breadth()` 函式）與第 75 行（`score()` 函式）。
- 那一行在做什麼：檢查美股類股 ETF 與美台基準指標即時報價 `asof` 是否不早於目標交易日 `day`（`"YYYY-MM-DD"`），防止拿昨日或過期報價誤判為今天全面偏多。
- 為什麼有問題：同樣因 `x.get("asof", "")` 在 `"asof": None` 時回傳 `None`，`str(None)[:10]` 為 `"None"`。第 57 行 `"None" >= "2026-11-19"` 為 **`True`**、第 75 行 `"None" < "2026-11-19"` 為 **`False`**，導致缺日期的過期／異常報價直接繞過日期檢查被計入上漲寬度與指標分數（註：`wsb/data/market.py` 第 383 行同類寫法已有發現紀錄）。
- 建議怎麼改：改為 `asof = str(x.get("asof") or "")[:10]`，並明確要求 `not asof or asof < day` 時略過。
- 確定度：高。

### CODE-3｜wsb/data/options.py：第 76 行與第 99 行對缺少 `gamma` 欄位合約的處理口徑不一致，可能造成總 GEX 與分履約價 Gamma 雷達加總不符
- 檔案路徑與行號：`wsb/data/options.py` 第 76 行（`gex_now`）與第 99–100 行（`by_strike`）。
- 那一行在做什麼：第 76 行計算現價總經銷商 Gamma 曝險（`gex_usd_bn_per_1pct`），第 99–100 行計算現價 ±8% 各履約價的淨 Gamma 分布（`by_strike`）。
- 為什麼有問題：第 76 行寫 `if gam.any() else gex_at(spot)`——只要整條選擇權鏈裡**哪怕只有 1 筆**合約有非零 `gamma`，所有 `gam == 0`（CBOE 延遲報價未給出 gamma）的合約在總和裡就會直接被當成 `0`；但第 99 行 `np.where(gam > 0, gam, _bs_gamma(...))` 卻對每一筆 `gam <= 0` 的合約個別用 Black-Scholes 重算 gamma。兩處口徑不一，遇到部分合約缺 CBOE gamma 時，總 GEX 數字與圖表分履約價柱狀圖會出現系統性落差。
- 建議怎麼改：第 76 行改與第 99 行共用同一個已補齊的 `g_now` 陣列（即 `gex_now = float(np.sum(sign * g_now * oi * 100 * spot * spot * 0.01))`，並把 `g_now` 計算移到第 76 行之前）。
- 確定度：中。

### CODE-4｜tools/site_tw_etf_perf.py：第 44 行 `b.get('tr1y', 0):+.0f` 遇 `tr1y` 鍵值為 `None` 時會拋出 `TypeError`
- 檔案路徑與行號：`tools/site_tw_etf_perf.py` 第 44 行（`sec_etf_rank()` 函式），對照 `wsb/analytics/tw_etf_perf.py` 第 118 行。
- 那一行在做什麼：在一句話導讀裡印出 0050 的近 1 年含息報酬（`{b.get('tr1y', 0):+.0f}%`）。
- 為什麼有問題：`wsb/analytics/tw_etf_perf.py` 第 118 行會在 `0050` 資料未滿一年時將 `"tr1y"` 鍵設為 `None`（鍵存在但值為 `None`）。此時 `b.get('tr1y', 0)` 會回傳 `None` 而非預設值 `0`，導致格式化 `{None:+.0f}` 直接拋出 `TypeError`（雖然 `_p()` 暫時沒有包住建置失敗，會讓整張卡片中斷）。
- 建議怎麼改：改為 `{num(b.get('tr1y'), 0, sign=True)}%`（或先行判斷 `b.get('tr1y') is not None`）。
- 確定度：低（實務上 0050 歷史資料齊全，屬防禦性型別缺口）。

（備註：本小時批次 `i % 24 == 18` 共 12 檔：`tools/site_ai.py`、`tools/site_euro_asia.py`、`tools/site_marks.py`、`tools/site_tw_etf_perf.py`、`wsb/analytics/bubble.py`、`wsb/analytics/fomc_drift.py`、`wsb/analytics/rally.py`、`wsb/analytics/tw_etf_perf.py`、`wsb/data/chokepoints.py`、`wsb/data/fomc.py`、`wsb/data/options.py`、`wsb/data/twmacro.py` 皆已逐行讀完。其中 `wsb/data/fomc.py` 第 81 行 `date.today()` 用於 `max_age_days=3` 容錯不影響結果、`wsb/data/twmacro.py` `* 100` 與 `wsb/analytics/twmacro.py` 單位換算一致，均依規則不濫報。）

---

其他今天的大事：
- 台股 11/19 收盤重挫 **1,768.02 點（-4.40%）至 38,426.89 點**、櫃買跌 7.22% 至 285.33 點，三大法人賣超 **461.03 億元**，盤後再爆世界、台化（4,172.8 萬元）、萬泰科合計 **1.29 億元**違約交割；金管會宣布 **11/20 起升級 3.5% 限空令**；新台幣 16:00 翻升收 **32.942 元（升值 0.5 分）**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190182.aspx ；https://www.cna.com.tw/news/afe/202611190296.aspx ；https://stock.ltn.com.tw/article/m7hjf9c9axqq ，皆 HTTP 200）。
- 阿里巴巴（BABA）11/19 盤前已率先公布 Q2 FY27 財報，營收 2,715.19 億人民幣（+10% YoY）優於預期、AI 雲與算力收入增 53%，但 Non-GAAP 淨利（199.09 億人民幣）遜預期且資本開支增 60% 致自由現金流淨流出 **344.72 億人民幣**，ADR 盤前挫逾 2%；網易（NTES）Q3 營收 279 億人民幣（-1.8% YoY）遜預期（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ；https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ，皆 HTTP 200）。
- 台積電 11/19 正式公告透過子公司 TSMC Partners 以每股 83 美元取得 Anthropic 普通股 **6,024,096 股（約 5 億美元）**；日月光仁武 J 坵塊 2,489 億元新廠同日動土（https://www.cna.com.tw/news/afe/202611190254.aspx ；https://www.cna.com.tw/news/afe/202611190122.aspx ，HTTP 200）。
- IEA 11/19《2026 世界能源展望》警告荷莫茲海峽危機為史上最大能源安全威脅（累積斷供 28 億桶油），同日葉門胡塞武裝飛彈攔截碎片擊中利雅德沙國主權基金（PIF）總部大樓；美中俄深圳首次三方領袖峰會結束（歷時約 1.5 小時）（https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ；https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ；https://www.cna.com.tw/news/aopl/202611193005.aspx ，皆 HTTP 200）。
- 德國政府與 UniCredit 11/19 就併購德國商業銀行（Commerzbank）達成協議帶動歐洲銀行股走揚，但《Politico》／Daily Sabah 揭露歐盟執委會遭 AI 滲透工具 ARTEX 網攻逾 10 天（https://www.tradingview.com/news/tradingview:d5957c435105b:0-key-facts-unicredit-board-nominees-commerzbank-takeover-rules-proposed/ ；https://www.dailysabah.com/business/tech/european-commission-hit-by-cyberattack-report ，皆 HTTP 200）。

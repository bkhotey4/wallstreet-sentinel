台北時間 2026-11-19 19:42

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）、整體 PCE 年增率為 **3.6%**（月增 **0.5%**），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，台北時間 2026-10-29，HTTP 200 確認）。
- 事實：之所以 9 月核心 PCE（3.1%）反過來高於核心 CPI（2.6%），根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 高於核心 CPI 的倒掛現象（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。
- 事實：本地 `research_feed/forecast.json` 第 130 行截至 19:30 重讀仍寫 `9 月核心 PCE 數字：查無。`，與 BEA 官方新聞稿及線上《財經日曆》PCE 卡片顯示的前值不符。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照（無新進展）
- 事實：歐洲央行（ECB）2026 年 11 月《金融穩定評估》Box 3（"The debt financing of AI and its implications for financial stability"）明確列出美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 共識（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，台北時間 2026-11-18，HTTP 200 確認）。
- 事實：ECB Box 3 正文對自由現金流的口徑為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（僅以**資本支出超過營運現金流**作為表層口徑，未把尚未起租的表外租賃算進單季現金流）；同時於圖表 A 與註腳 6 依美國會計準則 **ASC 842** 單獨指出，已簽約但資產尚未投入使用的租賃與算力承諾在起租前不計入資產負債表負債，這類表外承諾合計已逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200 確認）。
- 事實：四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與租賃口徑落差如下：
  - Meta（Q3 2026）：營運現金流 **$32.79B**，資本支出（含融資租賃本金償還）**$34.91B**，自報自由現金流為 **-$2.12B（轉負）**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ，前輪已讀）。
  - Alphabet（Q3 2026）：營運現金流 **$42.29B**（$42,290M），現金 PP&E 購置（不含融資租賃）**$51.36B**（$51,355M），自報自由現金流為 **-$9.07B（-$9,065M，轉負，含 52 億美元歐盟罰款支付）**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ，前輪已讀）。
  - Amazon（Q3 2026／TTM）：單季營運現金流 **$42.42B**、單季淨 PP&E 購置 **$75.93B**（隱含單季 **-$33.51B**），公司自報 **TTM 自由現金流 -$42.36B（-$42,357M，轉負）**，該口徑僅扣現金淨 PP&E、未扣額外揭露之新簽融資租賃資產（Q3 單季 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ，前輪已讀）。
  - Microsoft（Q1 FY27）：營運現金流 **$58.02B**，現金 PP&E 資本支出 **$39.37B**，自報自由現金流為 **+$18.6B（仍為正值，年減 27%）**；若計入新起租之融資租賃，總資本支出達 **$45.2B**，扣除後仍餘約 +$12.8B，印證 ECB 精準寫 `"most"` 而非全部（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ，伺服器回傳 HTTP 403，維持前輪已讀數字）。

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（19:42 補充 19:30 拼多多已揭露但站上預告未更新之實例）
- 推理：檢視 `research_feed/claude_notes.md`、`research_feed/forecast.json`、`research_feed/sessions.json`、`research_feed/macro_voice.json`（`2026-11-19 17:32 台北` 盤中版）及線上 `19:14` `upcoming.json`／`19:31` 總覽頁，最常「下太快」的是以下兩種思考捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：例如 `claude_notes.md` 第 14 行在還沒核對 `bea.gov` 或本站日曆卡片前值的情況下，因為「核心 PCE 通常比核心 CPI 低」，就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推 10 月區間；以及 `forecast.json` 第 65–73 行先前曾用單一 `BAMLH0A0HYM2`（3.43%）得出「信用市場還沒出現壓力」（第 3 輪你已修正）。
  2. **把「自己的新聞關鍵字只抓到標題或預告估計時間」直接當作「沒有原因／還沒公布」**：最新 `macro_voice.json`（`2026-11-19 17:32 台北`）仍寫台股跌 4.4%「我沒有找到時間對得上的單一消息」，但其實 19:27 線上風險新聞已抓到 18:35 自由財經與 18:52 工商時報關於世界／台化／萬泰科合計 1.29 億元違約交割的報導，加上自營商避險大賣 **214.40 億元**與金管會升級 3.5% 限空令；此外，線上 `upcoming.json`（19:14 版）與總覽「接下來 72 小時」（19:31 版）仍把盤前時間一律寫成 `08:00 ET（台北 21:00）`，導致已公布數小時的阿里巴巴（BABA）與剛於 **19:30（美東 06:30）公布 Q3 2026 財報的拼多多（PDD）** 仍被列為「即將公布」。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標（無新進展；保留台積電正式入股與 BABA FCF 實例）
- 事實：中央社 11/19 16:46 報導，台積電正式代子公司 TSMC Partners 公告以 **每股 83 美元**取得 Anthropic 普通股 **6,024,096 股**，總金額約 **5 億美元**（持股約 0.03%，依美國 1933 年證券法 Rule 144 一次付清，https://www.cna.com.tw/news/afe/202611190254.aspx ，HTTP 200 確認）。阿里巴巴（BABA）11/19 公布 Q2 FY27 財報，雖然 AI 雲與算力收入年增 53%、總營收人民幣 2,715.19 億元優於預期，但因資本開支年增 60% 至 504.77 億元、自由現金流淨流出 **344.72 億元**且 Non-GAAP 淨利低於預期，ADR 盤前挫逾 **2%**（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ，HTTP 200 確認）。
- 推理：這印證市場對「AI 算力投資能否轉化為正現金流」極度敏感。若今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，傳導先後順序維持如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：負債比高、高度仰賴大模型算力長約抵押融資，且 Anthropic 轉向透過博通租賃 3.5 GW Google TPU 機櫃自建資料中心（https://www.cna.com.tw/news/afe/202611190156.aspx ，HTTP 200 確認），直接稀釋第三方租賃溢價。隔天（11/20）可驗證指標：`CRWV`、`NBIS` 相對 `QQQ` 的開盤超額跌幅，及新雲端無擔保債二級殖利率走勢。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸**：ANT 公開發行募資約 813 億美元（含 260 億美元同步私募合計約 1,073 億美元）、完全稀釋估值約 1.5 兆美元，若破發將壓縮 OpenAI 與晚期 AI 獨角獸 IPO 窗口。隔天可驗證指標：`ARCC`、`BIZD`、`BX`、`APO` 股價與承銷商護盤（stabilizing bid）報導。
  3. **最後且分化：晶片與機櫃合作夥伴（NVDA、AVGO、GOOGL、AMZN、MSFT、MU、台積電等同步私募出資方）**：主要承受公允價值重估回吐，但 Anthropic 轉向自建反而讓博通與 TPU 機櫃組裝廠受關注。隔天可驗證指標：`AVGO`／`NVDA` 相對 `^SOX` 強弱與次日選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態（19:42 更新美中俄四點和平宣言、PDD 營收持平與歐盟印尼 CEPA）
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意且跨海應驗**：ECB Box 3 佐證多家美系雲端商 FCF 轉負、表外承諾逾 4 兆美元，今日（11/19）**BABA** Q2 FY27 單季 CapEx 飆升 60% 至 504.77 億人民幣、FCF 淨流出 **344.72 億人民幣**致 ADR 盤前挫逾 2%；**PDD** 剛公布的 Q3 2026 亦見營收持平（1,083 億元）、營運現金流年減至 430 億元且管理層重申持續投入供應鏈投資期（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ，HTTP 200 確認）。
  2. **主線 2（輝達治理風波 vs 出口調查）— 部分同意，兩條線已證實交織**：中央社 11/19 引述《福斯新聞》專訪指出，與黃仁勳有染的一名女子正受到美國政府調查是否為中國情報機構工作、以及是否協助走私晶片（https://www.cna.com.tw/news/aopl/202611193003.aspx ，HTTP 200 確認）。個人治理風波與國安／晶片出口調查不是二選一，而是**同一人物同時觸發公司治理與國安調查**，建議第 4 輪整併重估。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，補充台股限空令與歐洲貿易對沖**：今日台股集中市場收跌 **1,768.02 點（-4.40%）至 38,426.89 點**、櫃買重挫 **-7.22% 至 285.33 點**、世界／台化／萬泰科爆 **1.29 億元**違約交割，金管會宣布 **11/20 起升級 3.5% 限空令**（含 1,028 檔跌幅逾 3.5% 個股隔日禁平盤下放空，https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://stock.ltn.com.tw/article/m7hjf9c9axqq ，皆 HTTP 200）；但新台幣 16:00 翻升收 32.942 元、日韓印股市收紅、歐股 STOXX 600 早盤 +0.3%（UniCredit 與德國達協議且歐盟批准印尼貿易協定對沖川普關稅）。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意，地緣衝突與三方增產承諾雙向拉扯**：IEA 11/19《2026 世界能源展望》警告荷莫茲海峽已累計中斷 28 億桶原油與 600 億立方公尺天然氣供應、且胡塞飛彈攔截碎片擊中利雅德沙國主權基金（PIF）總部大樓；但**台北 19:00（11:00 GMT）中俄官媒發布的美中俄三方領袖《四點和平宣言》第 2 點明確寫道「三國計畫增加精煉石油產品的生產與供應，維持穩定能源流動」**（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ，HTTP 200 確認），一推一拉之下仍維持 **55%** 機率（區間外雙尾波動風險皆高）。
  5. **主線 5（「風險升級」劇本 33% vs 40%）— 同意方向一致**，差距 7 個百分點。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題（19:42 更新）
- 1. `research_feed/macro_voice.json` 最新版本（`17:32 台北`）對今日台股重挫 4.4% 仍寫「沒有找到時間對得上的單一消息」，且線上 `19:14` `upcoming.json`／`19:31` 總覽仍把盤前財報一律預估為 `08:00 ET（台北 21:00）`、導致已公布的 **BABA 與 PDD（19:30 公布）** 仍掛在預告裡。你的管線如何修補這兩處「資料已在外部／站上，但未反映到語音稿與預告狀態」的時間差？
- 2. 今日（11/19）一邊是 **BABA** 因 AI CapEx 激增致 FCF 淨流出 344.72 億人民幣、**PDD** 營收持平低於預期；另一邊則是 **美中俄深圳峰會發布《四點和平宣言》（宣示增加精煉石油產品供應）** 對沖 **IEA 荷莫茲斷供警告＋利雅德 PIF 大樓遇襲**。第 4 輪你打算如何調整「AI 資本支出現金流壓力」、「輝達事件定性」與「油價／風險升級」的機率？
- 3. 本地 `research_feed/forecast.json` 第 130 行截至 19:30 仍寫「9 月核心 PCE 數字：查無」，與 BEA 官方新聞稿（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）及線上《財經日曆》顯示的 3.1% 不符，請問預計何時在 `forecast.json` 補上基準值？

---

### WIDE-1｜IEA 11/19《2026 世界能源展望》警告荷莫茲為「史上最大能源威脅（累積斷供 28 億桶油）」＋胡塞飛彈碎片擊中沙國 PIF 利雅德總部（無新進展）
- 事實：國際能源總署（IEA）於 **2026 年 11 月 19 日**發布《2026 世界能源展望》，執行長 Fatih Birol 指出，今年 2 月爆發的美以伊衝突與伊朗封鎖荷莫茲海峽已造成「**史上最大的能源安全威脅**」，衝擊規模「**讓 1970 年代石油危機相形見絀**」，能源世界「再也回不去從前」；截至 11 月波灣累積供給損失達 **28 億桶原油與 600 億立方公尺天然氣**（https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ，台北時間 2026-11-19，HTTP 200 確認）。同日（11/19 下午）法新社與 Türkiye Today 報導，葉門胡塞武裝朝沙烏地首都利雅德發射飛彈，攔截墜落碎片損及利雅德金融區最高建築、沙國主權財富基金（PIF）80 層總部大樓外牆與多樓層窗戶（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ，台北時間 2026-11-19 14:52，HTTP 200 確認）。
- 推理：美股盤面焦點仍在昨日 EIA 美國庫存增加，忽視了波灣產油國核心金融與主權機構（PIF）建築已出現實體飛彈碎片波及，加上全球緩衝庫存耗盡，一旦油輪保險或沙國境內能源設施再遭干擾，遠月原油曲線與高收益／主權債風險溢價會迅速跳升。
- 先影響資產：布蘭特原油遠月價差、沙烏地與波灣主權債 CDS、油輪與航空燃油成本。

### WIDE-2｜APEC 深圳「川習會（30 對 30 協議）」與美中俄首次三方峰會發布《四點和平宣言》（宣示增產精煉油品、改革聯合國、核武對話）（19:42 更新最新宣言全文）
- 事實：11/19 中午美中「川習會」在深圳登場，川普表示雙方依「**30 對 30 協議**」同意各自對價值 **300 億美元**商品削減關稅（https://www.cna.com.tw/news/aopl/202611193005.aspx ，HTTP 200 確認）。隨後美中俄舉行約 90 分鐘的**史上首次三方領袖峰會**，川普已於台北 **18:48（10:48 GMT）**搭空軍一號離開中國；中俄官媒並於台北 **19:00–19:23（11:00–11:23 GMT）**發布《**四點和平宣言**》：（1）推動聯合國安理會與聯合國改革；（2）**三國計畫增加精煉石油產品生產與供應，重申穩定能源流動的重要性**；（3）尊重國家同意與元首豁免權，反對國際刑事法院（ICC）濫用管轄權；（4）重申核戰打不得、展開降核風險與防擴散對話（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ，HTTP 200 確認；另附中央社學者評析 https://www.cna.com.tw/news/acn/202611190062.aspx ，HTTP 200 確認；註：前一版所列 CNA 英文站網址為 404，本輪已移除並替換為《衛報》即時報導）。
- 推理：三方宣言第 2 點把「增產與供應精煉石油產品」寫入共同立場，搭配同日生效的 BIS 遠端算力封鎖，形成「高階算力對立不變，但能源與傳統貿易降溫」的格局；若實質落實增產精煉油品，將壓縮美國與亞洲煉油廠的裂解價差（crack spread）。
- 先影響資產：USD/CNH、布蘭特與成品油裂解價差、中概股（KWEB）、歐亞航運與軍工股。

### WIDE-3｜歐盟批准對印尼全面貿易協定（CEPA）對沖川普關稅＋德國與 UniCredit 就 Commerzbank 達妥協＋歐盟執委會遭 AI 工具網攻逾 10 天（19:42 更新 CEPA 與非 AI 報導來源）
- 事實：半島電視台引述路透 11/19 報導，歐盟部長理事會正式批准簽署並暫行適用**歐盟—印尼全面經濟夥伴協定（CEPA）與投資保護協定**，將取消逾 **90%** 雙邊商品進口關稅（印尼對歐盟汽車徵收的 **50%** 關稅將於 5 年內歸零），估每年為企業省下 **6 億歐元（約 6.58 億美元）**關稅，以對沖美國川普關稅衝擊並趕在印尼 2027-01-01 退出歐盟 GSP 優惠前接軌（https://www.aljazeera.com/economy/2026/11/19/eu-governments-approve-trade-deal-with-indonesia-to-offset-trump-tariffs ，HTTP 200 確認）。
- 事實：路透／《經濟時報》11/19 報導，義大利裕信銀行（UniCredit）CEO 致函德國財長承諾保留 Commerzbank 法蘭克福總部與德國上市地位並放棄柏林監事會指派要求，化解德國政府阻攔，帶動歐股 STOXX 600 反彈 **+0.3% 至 645.85 點**、Commerzbank 漲約 1.4%–1.6%、UniCredit 漲 1.8%（https://economictimes.indiatimes.com/markets/us-stocks/news/european-shares-rebound-as-anthropic-ipo-boosts-tech-stocks-commerzbank-rallies/articleshow/135985666.cms?from=mdr ；https://maaal.com/en/news/details/european-stocks-rise-afte-d/ ，皆 HTTP 200 確認）。
- 事實：MLQ.ai 與 Daily Sabah 引述《Politico》11/19 報導，歐盟執委會證實遭駭客利用免費開源 AI 滲透工具 **ARTEX** 網攻，導致內部人資 Sysper（薪資與休假）與醫療報銷 MyPMO 系統離線約 **10 天**，恐致大量員工個資外洩（https://mlq.ai/news/european-commission-says-hackers-targeted-some-of-its-systems-as-pay-and-leave-tools-stay-offline-for-about-10-days/ ；https://www.dailysabah.com/business/tech/european-commission-hit-by-cyberattack-report ，皆 HTTP 200 確認）。同時英國 10 月 CPI 升至 **3.6%**（https://www.mufgresearch.com/macro/european-macro-18-november-2026/ ，HTTP 200）。
- 推理：歐洲一邊透過與東協最大經濟體簽署零關稅協定及放行跨境銀行整併來對沖外部貿易與金融壓力，另一邊卻面臨 AI 驅動的公共機構資安威脅與英國高通膨黏著。
- 先影響資產：歐洲汽車與銀行股（EUFN）、歐系資安概念股、EUR/USD、歐盟與印尼出口概念股。

### WIDE-4｜日本央行植田和男 11/19 國會重申升息決心＋熊本清晨 M5.7 餘震（尚無 JASM 重大停工回報）＋南非央行維持 7.25% 不變（無新進展）
- 事實：路透／CNA 11/19 報導，日本央行（BOJ）總裁植田和男在國會淡化疲軟消費數據、警告潛在通膨有突破 2% 上行風險，強化 12 月升息至 **1.50%** 預期（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ，HTTP 200 確認）。11/19 清晨 02:22（台北 01:22）熊本發生規模 **5.7 地震**（深度 10 公里、7 月 28 日 M7.1 強震之餘震），截至目前無台積電熊本 JASM 廠重大結構損壞或停工回報（https://www.chinadailyasia.com/hk/article/642914 ，HTTP 200 確認）。11/19 日經 225 收漲 **+0.71%** 至 **59,444.21 點**；同日南非央行（SARB）宣布維持基準附買回利率 **7.25%** 不變。
- 推理：市場過度聚焦聯準會 12/9 升息，若 BOJ 於 12/17–18 跟進升息至 1.50%，日圓套利資金回流將對全球高倍數科技股形成第二波流動性擠壓。
- 先影響資產：USD/JPY、日本 10 年期公債、全球科技股估值。

### WIDE-5｜印度 10 月 CPI 破 6% 上限至 6.09%、強氣旋「阿克萬」11/20 中午登陸奧里薩邦（撤離逾 10 萬人）（無新進展）
- 事實：印度 10 月 CPI 升至 **6.09%** 突破央行 6% 上限（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ，HTTP 200 確認），11/19 印股 Nifty 50 反彈收漲 **+0.91%** 至 **25,458.75 點**。印度氣象局追蹤強烈氣旋「阿克萬（Akvan）」預計 **11 月 20 日中午**登陸奧里薩邦（Odisha），當地已緊急撤離逾 10 萬人（https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ，HTTP 200 確認）。
- 推理：若氣旋衝擊東岸港口、農產與電力基建，將進一步推升印度食品通膨並壓縮印度央行政策空間。
- 先影響資產：INDA、USD/INR、新興亞洲資金流。

---

### A｜今天的大動（對照 https://wallstreet-sentinel.pages.dev/api/gemini_ask 台北 11/19 19:31 最新 12 檔題目單）

### PANW｜Palo Alto Networks（PANW）今天 +9.2%（盤前）：Q1 FY27 財報優於預期＋45 億美元併購 Applied Compute（無新進展）
- 事實：美東 11/18 盤後公布 Q1 FY27 營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億）、Non-GAAP EPS **1.05 美元**（優於預期 0.97 美元）、NGS ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**（FactSet 共識 141.7 億）、調整後 EPS 指引至 **4.26～4.30 美元**（FactSet 共識 4.18 美元），並宣布以 **45 億美元**全股票收購開源權重 AI 模型平台 **Applied Compute**，推動盤後與今日盤前大漲逾 **9%**（https://www.prnewswire.com/news-releases/palo-alto-networks-reports-fiscal-first-quarter-2027-financial-results-302944393.html ；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，皆 HTTP 200 確認）。
- 同意本站（Yahoo 標題已提及 Palo Alto 財報大漲）；本站漏掉的：併購 Applied Compute 細節及 KeyBanc 將評等調升至 **Overweight**、看法調高至 **$380**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ）。

### TJX｜TJX Companies（TJX）今天 +8.0%：Q3 FY27 同店銷售成長 4% 超越計畫、上調全年展望至區間上緣（無新進展）
- 事實：TJX 於美東 **2026 年 11 月 18 日**公布 Q3 FY27（截至 10/31）財報，淨銷售年增 **6%** 至 **159.5 億美元**（優於預期約 158 億美元）、合併同店銷售成長 **4%**（優於公司原計畫 2%–3%）；GAAP 稀釋後 EPS **1.39 美元**（年增 9%，含 **0.05 美元** IEEPA 關稅退稅淨利益），調整後 EPS **1.34 美元**（年增 5%），並將 FY27 全年展望收斂至區間上緣（全年同店估約 +4%）（https://mlq.ai/news/tjxs-comparable-sales-rise-4-above-its-plan-and-it-narrows-its-full-year-outlook-toward-the-top-of-the-range/ ，美東 2026-11-18 12:44，HTTP 200 確認）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### CRWD｜CrowdStrike（CRWD）今天 +5.9%（盤前）：受同業 PANW 財報驗證企業 AI 資安需求外溢帶動（無新進展）
- 事實：CRWD 預計 **12 月 1 日盤後**才公布財報，11/18–19 本身無單獨公司公告或分析師新調整（找不到來源）；美東 11/18 正規盤大漲 +7.95% 收 $237.03 後，盤前受同業 PANW Q1 FY27 財報全面優於預期與 45 億美元 AI 安全併購案外溢提振，資安族群集體走高（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200 確認）。
- 本站漏掉的：屬同業財報外溢效應，非 CRWD 個別公告。

### SKHY｜SK 海力士（SKHY）今天 +5.6%（盤前）：韓股連兩日收漲，受 Anthropic 1.5 兆美元 IPO 定價點燃全球記憶體與儲存股盤前大漲（無新進展）
- 事實：SK 海力士（000660.KS）於 **2026 年 11 月 19 日**韓股正規盤收漲 **+3.41%** 至 **1,183,000 韓元**（連兩日走高，https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ，HTTP 200 確認）；同日美股／海外追蹤盤前因 Anthropic 擴大發行至 9.8 億股、以每股 83 美元定價（募資 813 億美元、估值 1.5 兆美元）今晚掛牌，刺激記憶體與儲存族群盤前集體大漲，SK 海力士盤前漲逾 **5%**（https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，2026-11-19，HTTP 200 確認）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### SNDK｜SanDisk（SNDK）今天 +5.5%（盤前）：今日為 1 拆 8 股票分割前最後交易日＋Anthropic IPO 帶動儲存股盤前集體反彈（無新進展）
- 事實：今日（美東 **2026 年 11 月 19 日**）為 SanDisk（SNDK）**1 拆 8 股票分割**盤後分配股權前最後一個拆前交易日（11/20 開盤依拆股後價格交易，https://financefeeds.com/sandisk-sndk-stock-776-thursday-last-session-before-8-for-1-split-bull-831-bear-749/ ；https://www.fool.com/investing/2026/11/16/sandisk-splits-its-stock-8-for-1-on-nov-19-flash-memory-prices-still-matter-more-than-the-share-count/ ，皆 HTTP 200 確認）；同時受 Anthropic 今晚掛牌點燃儲存族群買氣帶動，SNDK 盤前漲約 **4.9%–5.5%**（https://news.cnyes.com/news/id/6667734 ；https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，皆 HTTP 200 確認）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### MU｜美光（Micron，MU）今天 +5.5%（盤前）：Anthropic IPO 定價 83 美元今晚掛牌引爆儲存與 AI 記憶體股盤前反彈（無新進展）
- 事實：受 Anthropic（ANT）IPO 定價高於區間、募資 813 億美元今晚於那斯達克掛牌激勵，美光（作為 Anthropic 10 億美元同步私募參與方暨 HBM／DRAM／SSD 策略夥伴）11/19 盤前與 SK 海力士、SanDisk 等儲存／記憶體股集體上揚逾 4%–5%（https://news.cnyes.com/news/id/6667734 ；https://financefeeds.com/micron-mu-stock-705-thursday-anthropic-ipo-priced-83-bull-746-bear-667/ ，皆 HTTP 200 確認）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### STX｜希捷科技（Seagate Technology，STX）今天 +5.4%（盤前）：受 Anthropic 創紀錄 IPO 點燃 AI 資料中心儲存與記憶體族群集體反彈（新增）
- 事實：11/19 美股盤前 STX 未有單獨公司公告或新發布的分析師調評（找不到獨立公司來源），主要係今日 Anthropic 定價每股 83 美元（募資約 813 億美元、完全稀釋估值約 1.5 兆美元）並於今晚在納斯達克上市，激勵整個儲存與記憶體族群（SKHY、SNDK、MU、STX、WDC）於盤前同步大漲逾 **3%–5%**（鉅亨網 11/19 18:05 引述 BIT 數據報盤前漲 +4.22%，美股盤前報價隨時間擴大至約 +5.4%；https://news.cnyes.com/news/id/6667734 ；https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，皆 HTTP 200 確認）。
- 本站漏掉的：STX、WDC、MU、SNDK、SKHY 今日盤前屬同一儲存／記憶體板塊受 Anthropic 上市與 AI 資料中心儲存需求帶動集體反彈，本站題目單全數標「沒有找到對得上的新聞」。

### WDC｜威騰電子（Western Digital，WDC）今天 +5.1%（盤前）：與 STX 等儲存族群同受 Anthropic IPO 提振盤前同步反彈（新增）
- 事實：11/19 美股盤前 WDC 未見單獨公司公告（找不到獨立公司來源），與同業 STX、SNDK、MU、SKHY 同步受 Anthropic 813 億美元 IPO 定價 83 美元今晚掛牌之 AI 基礎設施情緒激勵，在盤前集體走高（鉅亨網 11/19 18:05 報盤前 +4.01%、隨盤前擴大至 +5.1%；https://news.cnyes.com/news/id/6667734 ；https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，皆 HTTP 200 確認）。
- 本站漏掉的：與 STX 屬同一儲存板塊集體反彈，非 WDC 個別新消息。

### HCA｜HCA Healthcare（HCA）今天 -5.0%：受 CMS「CRUSH」醫保反詐欺追溯審計草案與證券詐欺律師調查發酵拖累板塊，抵消摩根大通調高看法（無新進展）
- 事實：美國聯邦醫療保險與醫療補助服務中心（CMS）11/16 提出「CRUSH」反詐欺規則草案（擬擴張 Medicare Advantage 風險調整稽核並回溯至 2018 給付年度），連續兩日重挫管理式醫療板塊（如 UNH 兩日累跌逾一成），恐慌外溢至醫院營運商 HCA（https://fr.tradingview.com/news/gurufocus:3ac55a47d094b:0-unitedhealth-stocks-fall-4-62-as-cms-proposes-wider-medicare-advantage-audits/ ，HTTP 200 確認）；同日（11/18）摩根大通雖維持 HCA `Neutral` 評等並將價格看法由 $425 調高至 **$475**（https://www.tradingview.com/news/tradingview:9eb3a7caf755c:0-jp-morgan-maintains-hca-healthcare-at-neutral-raises-price-target-to-475-from-425/ ，HTTP 200 確認），但仍低於前收 $501 水準。
- 傳聞／找不到來源：HCA 11/18 當日無官方負面財測新公告；另市場流傳 Pomerantz 律師事務所就 HCA 先前因 ACA 交易所給付不利下修 2026 年獲利指引啟動證券詐欺調查，未見機構或公司正式回應（待證實）。

### INTC｜英特爾（Intel，INTC）今天 +4.9%（盤前）：隨晶片族群結束五連跌反彈，市場消化川普談 Blackwell 輸陸可能性與 18A-P 首家外部客戶進展（更新 Austin 峰會細節）
- 事實：在半導體類股連續五個交易日重挫後，受 Anthropic IPO 定價高於區間帶動 AI 與晶片股盤前反彈，加上美國總統川普於 APEC 深圳受訪稱兩至三年後不排除放行上一代 Blackwell 晶片輸陸，以及英特爾於德州奧斯汀 TomorrowX Summit 宣布簽下 **18A-P 製程首位外部客戶**並揭露微軟（Microsoft）成為其 EMIB 先進封裝技術首家公開客戶，推動 INTC 盤前反彈約 **4.2%–4.9%**（https://www.tradingview.com/news/stocktwits:6243efa9f094b:0-nvda-intc-stocks-ease-post-5-day-rout-after-meeting-xi-jinping-trump-says-nvidia-blackwell-chips-could-reach-china-within-2-3-years/ ；https://news.cnyes.com/news/id/6667734 ，皆 HTTP 200 確認）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### PSX｜Phillips 66（PSX）今天 -4.7%：與 VLO 同受 EIA 汽油／原油庫存暴增壓抑煉油族群；另市場消化煉油廠排放通報與券商看法調整（更新 AI 摘要註記）
- 事實：美東 11/18 同業 VLO、MPC、PSX 同步受 EIA 截至 11/13 當週汽油庫存暴增 **520 萬桶**、蒸餾油增 **160 萬桶**與原油累庫 **340 萬桶**拖累下挫（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ，HTTP 200 確認）。
- 傳聞／待人工來源證實：TradingView 轉載之機器摘要標題提及 PSX 11/13 德州 Borger 煉油廠排放通報與 Jefferies 將對 PSX 價格看法由 $280 調降至 $265（因屬 TradingView `Key facts` 自動摘要，依規則暫不列為獨立人工報導來源，主因仍為 EIA 庫存大增導致煉油板塊集體修正）。

### CNQ｜Canadian Natural Resources（CNQ）今天 -4.6%：隨北美油氣股反映 EIA 庫存大增壓低油價與 25.3 億加元併購案（無新進展）
- 事實：CNQ 11/18 正規盤隨北美油氣股下挫收跌 **4.63%** 至 **$45.53**（多倫多收跌 4.06% 至 C$65.52），時間點對得上 EIA 11/18 10:30 公布原油庫存大增 340 萬桶／汽油大增 520 萬桶（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ；https://www.nationthailand.com/news/world/40073656 ，皆 HTTP 200 確認），且市場消化其以 **25.3 億加元**收購 **Advantage Energy** 案（https://www.newsfilecorp.com/release/324091/Canadian-Natural-Resources-Limited-Enters-into-Agreement-to-Acquire-Advantage-Energy-Ltd ，HTTP 202）。

---

### AN｜AN-1：最近 3 小時內（台北 16:42–19:42）無新增美股 AI／前 20 大權值股分析師調評；補齊近期券商調評彙整
- 事實：檢索最近 3 小時（台北 16:42–19:42／美東 11/19 03:42–06:42），AI 供應鏈與美國市值前 20 大公司未見新發布的美股券商調評（找不到來源）。
- 事實（近期已核對報告，依任務單保持英文評等原文）：
  1. **高盛 Goldman Sachs（AVGO，美東 11/19 01:26／台北 14:26 報導，無新進展）**：分析師 James Schneider 維持 **AVGO** `Buy` 評等，因同業估值倍數壓縮（評估倍數由 30 倍下修至 25 倍），將價格看法由 $540 調降至 **$460**，但估 FY27／FY28 AI 營收仍高於市場預期 5% 與 9%（https://www.tokenpost.com/news/business/61151 ，HTTP 200 確認）。
  2. **Rothschild & Co Redburn（AVGO，11/13 報告，無新進展）**：分析師 Mike Harrison 將 **AVGO** 由 `Buy` 調降至 `Neutral`，價格看法由 $595 調降至 **$398**，理由為對高舉債 AI 實驗室客戶集中風險（https://fr.tradingview.com/news/seekingalpha:f4cc47e04094b:0-broadcom-in-focus-as-rothschild-downgrades-to-neutral-but-flags-potential-upside/ ；https://www.tikr.com/blog/is-rothschild-co-redburn-wrong-to-give-up-on-broadcom-wall-street-still-sees-533 ，皆 HTTP 200 確認）。
  3. **摩根大通 JPMorgan（HCA，11/18 報告，無新進展）**：維持 **HCA** `Neutral` 評等，將價格看法由 $425 調高至 **$475**（https://www.tradingview.com/news/tradingview:9eb3a7caf755c:0-jp-morgan-maintains-hca-healthcare-at-neutral-raises-price-target-to-475-from-425/ ，HTTP 200 確認）。
  4. **摩根士丹利（台積電 2330，11/19 亞太高峰會後報告，無新進展）**：維持 `Overweight` 評等與估值看法 **3,088 元**，2026–2028 年 EPS 估 **112.10／148.64／189.81 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，HTTP 200 確認）。
  5. **輝達（NVDA）與其他近期機構報告（無新進展）**：Summit Insights 降評至 `Hold`（https://www.tikr.com/fr/blog/is-summit-insights-wrong-to-give-up-on-nvidia-wall-street-still-sees-251 ）；HSBC Frank Lee 降至 `Hold` 看法 $365→$170（https://www.tradingview.com/news/binance_news:d94dcaa1f094b:0-hsbc-downgrades-nvidia-says-stock-may-struggle-until-new-ceo-is-named/ ）；Evercore ISI `Outperform`→`In-Line` 看法 $186、Bernstein $400→$200、Baird `Outperform`→`Neutral`（https://www.tradingview.com/news/benzinga:3bce7f47b094b:0-nvidia-gets-10-bank-downgrades-after-huang-exit-what-to-expect-ahead-of-q3-results/ ，HTTP 200 確認）；Moody's 維持 `Aa1` 展望降至 `Stable`（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ）；KeyBanc 調升 PANW 至 `Overweight` 看法 $380（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ）；Piper Sandler 調升 MDT 至 `Overweight` 看法 $120（https://www.tradingview.com/news/tradingview:5b080eae6cc49:0-piper-sandler-upgrades-medtronic-to-overweight-from-neutral-raises-price-target-to-120-from-85/ ）。（註：另搜尋摘要顯示 William Blair 近日將 **AMD** 由 `Market Perform` 調升至 `Outperform`，但 TipRanks 原連結對自動化程式回傳 HTTP 403，尚未取得可讀全文連結。）

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）刊登聯邦公報生效，同日白宮馬尼拉 Quad 峰會聚焦可信賴超級智慧供應鏈（無新進展）
- 事實：美國商務部工業安全局（BIS）暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢至 2027-01-19），增訂 § 744.24 限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則（https://public-inspection.federalregister.gov/2026-23529.pdf ；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ；https://www.milbank.com/en/news/bis-issues-new-rule-restricting-remote-access-to-advanced-chips.html ，皆 HTTP 200 確認）。
- 事實：白宮於 11 月中旬馬尼拉 Quad 領袖峰會聯合澳、印、日發表聲明，鎖定關鍵礦產／半導體供應鏈安全與可信賴超級智慧技術生態；另今日（11/19）聯邦公報亦列載 CMS CRUSH 反詐欺草案（`2026-23461`，https://public-inspection.federalregister.gov/2026-23461.pdf ，HTTP 200 確認）。

### POL-2｜美國財政部 FinCEN 強化 CDD 提案、9 月 TIC 淨流入 2,610 億美元、OFAC 制裁與 USTR 談話（無新進展）
- 事實：財政部 FinCEN 發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，https://home.treasury.gov/news/press-releases/sb0691 ）；9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ）；OFAC 制裁真主黨與聖城軍金流（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 重申美國優先貿易（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）。

---

### TW-1｜11/19 台股收跌 1,768 點（38,426.89 點）、櫃買暴跌 7.22%、1,028 檔明納限空令 2.0、世界／台化／萬泰科爆 1.29 億違約交割；新台幣收升 32.942 元（19:42 補充 1,028 檔個股數與各電子權值股收盤）
- 事實（11/19 台股收盤、三大法人與違約交割）：加權指數盤中下探 38,259.7 點（跌 1,935.21 點），終場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，失守年線 39,368 點）**，成交值 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ，HTTP 200 確認）；櫃買指數收跌 **-7.22%（-22.22 點）至 285.33 點**。電子權值股收盤：**台積電 2,100 元（-3.45%）**、**聯發科 3,720 元（-5.58%）**、**鴻海 220.5 元（-0.23%）**、**日月光投控 504 元（-8.03%）**、**緯穎 1,410 元（跌逾 4%）**（https://www.moneyweekly.com.tw/ArticleData/Info/Article/212266 或同日中央社／聯合報，皆 HTTP 200）。三大法人合計賣超 **461.03 億元**（**外資 -243.12 億元**、**投信 +15.13 億元**、**自營商 -233.03 億元**，其中自營商避險部位 **-214.40 億**，https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200 確認）；期貨三大法人合計淨空單 **-8,883 口**（外資 **-99,219 口**、投信 **+91,791 口**、自營商 **-1,455 口**）。**盤後證交所與櫃買中心再通報 3 檔違約交割，合計金額達 1.29 億元**：包含上市**台化（1326）4,172.8 萬元**，以及上櫃**世界先進（5347）與萬泰科（6190）**（https://stock.ltn.com.tw/article/m7hjf9c9axqq ；https://inews.setn.com/news/1941815 ，皆 HTTP 200 確認）。
- 事實（11/19 新台幣收盤價）：台北外匯市場開 32.960 元，盤中低見 **33.040 元**，16:00 翻升收 **32.942 元（升值 0.5 分）**；台北外匯經紀成交 **22.63 億美元**、台北及元太兩大外匯市場總成交 **32.82 億美元**（https://www.cna.com.tw/news/afe/202611190296.aspx ；https://money.udn.com/money/story/12509/9889341 ，皆 HTTP 200 確認）。
- 事實（金管會 11/20 限空令 2.0）：（1）今日收盤跌幅達 **3.5%** 以上之上市櫃與 TDR（共計 **1,028 檔**），次一交易日禁止低於前收融券及借券放空；（2）每日盤中借券放空委託數量上限由前 30 日均量 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190182.aspx ；https://vexed.me/realtime ，皆 HTTP 200 確認）。

### TW-2｜台積電 11/19 正式公告約 5 億美元認購 Anthropic 602.4 萬股；日月光仁武 2,489 億動土、鴻海 72.4 億日圓併購 Sony 車載相機與廣達／聯電動態（無新進展）
- 事實：中央社 11/19 16:46 報導，台積電（2330）正式公告由子公司 **TSMC Partners** 以每股 **83 美元**取得 Anthropic 普通股 **6,024,096 股**，總金額約 **5 億美元（499,999,968 美元，持股約 0.03%）**，依美國 1933 年證券法 Rule 144 一次付清作為長期股權投資（https://www.cna.com.tw/news/afe/202611190254.aspx ，HTTP 200 確認）。同日中央社引述智璞產研分析，Anthropic 轉向自建資料中心恐推升台積電 CoWoS 需求並牽動英業達、廣達、鴻海 TPU 機櫃代工訂單（https://www.cna.com.tw/news/afe/202611190156.aspx ，HTTP 200 確認）。
- 事實（其餘台鏈公告，無新進展）：日月光投控旗下台灣福雷電子高雄仁武 J 坵塊新廠 11/19 動土、計畫投資 **2,489 億元**（https://www.cna.com.tw/news/afe/202611190122.aspx ，HTTP 200）；廣達田納西廠租約 1,490.8 萬美元（https://news.cnyes.com/news/id/6666244 ，HTTP 200）；海龍 2A 綠電轉售台積電（https://www.cna.com.tw/news/afe/202611190102.aspx ，HTTP 200）；鴻海 72.4 億日圓收購 Sony 車載相機事業（https://www.ctee.com.tw/news/20261119700316-439901 ，HTTP 200）及沙國合資 Ceer Motors 獲 6.93 億美元銀行團融資；熊本清晨 M5.7 地震尚無 JASM 重大停工回報。
- 傳聞：外媒轉述《工商時報》稱台積電依客戶資產負債表設 AI 信用額度、超額須預付現金，尚未獲官方證實（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ，HTTP 200）。

### TW-3｜SK 海力士 11/19 收漲 +3.41%、蘋果洽談三星多年期 DRAM 長約；亞股日韓印收紅、陸港台收黑（無新進展）
- 事實：《MoneyToday》11/19 報導 SK 海力士（000660.KS）收漲 **+3.41% 至 1,183,000 韓元**，與三星電子連兩日收高（https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ，HTTP 200 確認）；《The Korea Herald》11/19 報稱蘋果正進入與三星電子洽談 4 至 5 年期 DRAM 供應協議最後階段（https://www.koreaherald.com/article/10942672 ，HTTP 200 確認）。11/19 亞股收盤：**日經 225 +0.71%（59,444.21）**、**KOSPI +1.39%（5,137.89）**、**印度 Nifty 50 +0.91%（25,458.75）**；**上證 -0.28%（3,577.62）**、**恆生 -1.95%（22,841.62）**、**台股加權 -4.40%（38,426.89）**。愛德萬測試與台韓出口數據保留（無新進展，https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ）。

---

### EARN-PDD｜拼多多（PDD）已於 11/19 19:30（美東 06:30）公布 Q3 2026 財報：營收 1,083 億人民幣持平遜預期，Non-GAAP 每 ADS 盈餘 21.04 元（3.14 美元）優於預期！（重大更新）
- 事實：拼多多（PDD）於 **美東 2026-11-19 06:30（台北 19:30）**正式發布 Q3 2026 財報（電話會議訂於美東 07:30／台北 20:30）：
  - **總營收**：人民幣 **1,083 億元**（約 **162 億美元**），與去年同期 1,083 億元持平，**低於** TradingView 彙整市場共識的人民幣 **1,155 億～1,217 億元**（約 171.7 億美元）。其中線上行銷服務及其他營收年增 **12%** 至 **598 億元**（89 億美元），但交易服務營收年減 **12%** 至 **485 億元**（72 億美元）。
  - **獲利與現金流**：營業利益升至人民幣 **312 億元**（去年同期 250 億元）；GAAP 歸屬普通股股東淨利 **295 億元**（去年同期 293 億元）、稀釋每 ADS 盈餘人民幣 **20.04 元（2.99 美元）**；**Non-GAAP 淨利 310 億元**（去年同期 314 億元）、**Non-GAAP 稀釋每 ADS 盈餘人民幣 21.04 元（3.14 美元）**，**優於** TradingView 所列市場共識 **2.61～2.77 美元**（人民幣 18.72～19.02 元）。營運淨現金流人民幣 **430 億元**（去年同期 457 億元），截至 9 月 30 日帳上現金及短期投資達 **4,554 億元（679 億美元）**（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ；https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ，皆 HTTP 200 確認）。

### EARN-BABA｜阿里巴巴（BABA）已於 11/19 18:18 前公布 Q2 FY27 財報：營收 2,715.19 億元（+10% YoY）優於預期，但 Non-GAAP 淨利遜預期且 FCF 淨流出 344.72 億元致 ADR 盤前挫逾 2%（無新進展）
- 事實：阿里巴巴於 **2026-11-19 美東盤前（台北 18:18 前）**正式發布截至 2026 年 9 月 30 日止 Q2 FY27 財報（電話會議訂於美東 07:00／台北 20:00）：總營收人民幣 **2,715.19 億元**（約 405.0 億美元，年增 **10%**），優於市場預期的 2,698.49 億元；經調整 EBITA 人民幣 **326.36 億元**（年增 **260%**）；歸屬股東淨利 **645.35 億元**，但 **Non-GAAP 淨利人民幣 199.09 億元（年增 92%）低於市場預期 265.7 億元**（Non-GAAP 每 ADS 盈餘人民幣 **8.10 元**，年增 86%）。AI 雲與算力服務收入年增 **53%** 至 **609.73 億元**（外部商業化收入年增 67%／64%）；惟單季資本開支年增 **60%** 至 **504.77 億元**，導致**自由現金流淨流出擴大至 344.72 億元**，拖累其 ADR 盤前下挫逾 **2%**（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ；https://investingnews.com/alibaba-group-announces-september-quarter-2026-results-and-interim-results-for-the-six-months-ended-september-30-2026/ ，皆 HTTP 200 確認）。

### EARN-NTES｜網易（NTES）11/19 盤前公布 Q3 2026 財報，營收人民幣 279 億元（-1.8% YoY）低於預期，今晚 20:00 舉行法說（無新進展）
- 事實：網易（NTES）於 **2026-11-19** 公布 Q3 2026 淨營收人民幣 **279 億元**（約 42 億美元，年減 **1.8%**，低於市場共識約 295 億～303 億元），遊戲及相關增值服務 **229 億元**（-1.7% YoY）、有道 **14 億元**（-12.3% YoY）、網易雲音樂 **19 億元**（-0.9% YoY）、創新業務 **15 億元**（+7.1% YoY）；毛利 **190 億元**（+4.8% YoY）、Non-GAAP 淨利 **92 億元**、Non-GAAP 每 ADS 基本盈餘 **2.13 美元**，季度股息調高至每 ADS **0.585 美元**；電話會議訂於美東 11/19 07:00（台北 20:00）（https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ，HTTP 200 確認）。

### EARN-WMT｜沃爾瑪（WMT）Q3 FY27 財報（今晚美東 11/19 07:00 發稿／台北 20:00、08:00 電話會議，截至 19:42 尚未發布，無新進展）
- 事實：美東 **2026-11-19 07:00 財報、08:00 電話會議**（台北 **11/19 20:00／21:00**）；TradingView 彙整共識營收約 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）；選擇權隱含波動 **±5.78%～±6.4%**（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，皆 HTTP 200 確認）。

### EARN-WSM / INTU / ROST / GAP｜今日（11/19）美東盤前與盤後其餘財報（無新進展）
- 事實：
  - **WSM（盤前／台北 11/19 23:00 電話會議，截至 19:42 尚未見正式公布）**：共識營收 **19.8 億～20.0 億美元**、EPS **2.19 美元**（https://www.tradingview.com/news/tradingview:5796c7c550438:0-wsm-q3-26-earnings-eps-estimate-is-2-19-usd/ ，HTTP 200 確認）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（原財測 2.44–2.48 美元），隱含波動 ±8.9%–10.5%（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ，HTTP 200 確認）。
  - **ROST（盤後／台北 11/20 05:00）**：共識營收 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ，HTTP 200 確認）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ，HTTP 200 確認）。

### EARN-HPE / ZM / BBY / BURL / DKS / ADI / MDT / DELL / HPQ / ADSK / WDAY / BILI / DE｜11/23–11/25 未來 10 天財報（無新進展）
- 事實：
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（公司財測 1.20–1.30；波動 ±9.7%，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ）；**ZM** Zacks 共識營收 **12.8 億美元**、EPS **1.49 美元**（https://www.zacks.com/stock/news/3030700/zoom-communications-zm-falls-more-steeply-than-broader-market-what-investors-need-to-know ）。
  - **11/24 盤前（台北 20:00–21:00）**：**BILI** MarketBeat 共識營收 **12.3 億美元**、EPS **0.23–0.27 美元**；**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**（https://www.tradingview.com/news/tradingview:6917007d5e261:0-burl-q3-26-earnings-revenue-estimate-is-2-97b-usd/ ）；**DKS** 營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ）；**ADI** FactSet 共識營收 **43.2 億美元**、EPS **3.88 美元**（https://www.tradingview.com/news/tradingview:4441db86105da:0-adi-q4-26-earnings-revenue-estimate-is-4-32b-usd/ ）；**MDT** FactSet 共識營收 **94.8 億美元**、EPS **1.33 美元**（https://es.tradingview.com/news/tradingview:dcc2d0d8b8c99:0-mdt-q2-26-earnings-revenue-estimate-is-9-48b-usd/ ）；**BBY** Zacks 共識營收 **98.8 億美元**、EPS **1.48 美元**（https://www.zacks.com/stock/news/3031155/best-buy-bby-reports-next-week-wall-street-expects-earnings-growth ）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億～492.5 億美元**、EPS **6.41–6.60 美元**（波動 ±14.85%，https://www.tradingview.com/news/tradingview:e525c4bdcb809:0-dell-q3-26-earnings-revenue-estimate-is-49-25b-usd/ ）；**WDAY** 營收 **26.9 億美元**、EPS **2.75 美元**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ）；**HPQ** FactSet 共識營收 **154.3 億美元**、EPS **0.75 美元**（https://in.tradingview.com/news/tradingview:2627939d5b773:0-hpq-q4-26-earnings-revenue-estimate-is-15-43b-usd/ ）；**ADSK** MarketBeat 共識營收 **21.3 億美元**、EPS **3.07 美元**（https://www.marketbeat.com/instant-alerts/upcoming-autodesk-adsk-set-to-announce-quarterly-earnings-on-tuesday-2026-11-17/ ）。
  - **11/25 盤前（台北 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ）。

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ，HTTP 200 確認）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（除非明確預告 1 月再升 1 碼）（強烈偏升息；補 Morningstar/AA HTTP 200 來源）
- 事實：Waller 受訪指出聯準會可能需要「shock」壓抑通膨預期避免 3% 通膨固著，12/8–9 會議應考慮一次升息 50 基點，除非明確前瞻指引 12 月與 1 月連續各升 1 碼（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ；https://www.morningstar.com/news/marketwatch/20261118119/feds-waller-says-interest-rate-hikes-may-be-needed-to-shock-inflation-out-of-the-system ；https://www.aa.com.tr/en/economy/fed-governor-favors-half-point-rate-hike-in-december-unless-fed-signals-january-increase/4129382 ，皆 HTTP 200 確認）。

### FED-3｜聯準會理事 Michael S. Barr（偏升息）、紐約聯準銀行總裁 John Williams（反對一次升息 2 碼）；今晚 Goolsbee 問答與理事會貼現率閉門會議（替換 Williams 404 連結為 AA/IDN HTTP 200）
- 事實：Barr 11/18 在紐約聯準銀行演說指出通膨仍過高、適合進一步升息並示警 AI 代理資金調撥風險（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ，HTTP 200 確認）；Williams 於 Axios BFD 峰會對談指出目前情況不需「戲劇性行動（dramatic action）」、反對一次大幅升息 2 碼，主張漸進升息（https://www.aa.com.tr/en/economy/fed-governor-favors-half-point-rate-hike-in-december-unless-fed-signals-january-increase/4129382 ；https://www.idnfinancials.com/news/71905/does-the-fed-still-need-to-raise-interest-rates-john-williams-answer ，皆 HTTP 200 確認；移除前一版 404 之 Chosun 連結）。今日稍後芝加哥聯準銀行總裁 Goolsbee 將於 **美東 11/19 12:30（台北 11/20 01:30）**於印第安納經濟俱樂部參與座談問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ，HTTP 200）；聯準會理事會於 **美東 11/19 15:00（台北 11/20 04:00）**召開閉門貼現率會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ，HTTP 200）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼約 90%–95%、升息 2 碼約 5%–10%（無新進展）
- 事實：聯邦基金期貨幾乎完全定價 12/9 升息 1 碼（各報導引述 CME FedWatch 介於 **90%–97%**），升息 2 碼約 **3%–10%**（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ，HTTP 200 確認）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，HTTP 200 確認）。
- 事實：核心 PCE（3.1%）高於核心 CPI（2.6%）之結構主因，係 2026 年住房／房租通膨降溫拉低權重較大的 CPI，而醫療服務、金融與軟體科技服務權重在 PCE 籃子較高且價格較黏著（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。

### TASK-B2｜11/19 台股收跌 1,768.02 點收 38,426.89 點（櫃買收 285.33 點、跌 7.22%）、外資現貨賣超 243.12 億、三大法人台指期合計淨空單 -8,883 口、新台幣收升至 32.942 元（無新進展）
- 事實（11/19 收盤與三大法人現貨／違約交割）：集中市場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，破年線）**，成交金額 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ，HTTP 200）；櫃買指數收 **285.33 點（-22.22 點 / -7.22%）**。三大法人合計賣超 **461.03 億元**，其中 **外資及陸資賣超 243.12 億元**、**投信買超 15.13 億元**、**自營商合計賣超 233.03 億元**（含避險 -214.40 億元，https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200）。盤後另爆出世界、台化（4,172.8 萬元）、萬泰科合計 **1.29 億元**違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ，HTTP 200）。
- 事實（11/19 期交所三大法人台指期未平倉）：期交所 `futContractsDate` 公布臺股期貨三大法人合計淨空單為 **-8,883 口**（外資 **-99,219 口**、投信 **+91,791 口**、自營商 **-1,455 口**）。
- 事實（11/19 新台幣 16:00 收盤價）：開 32.960 元，盤中低見 **33.040 元**，16:00 翻升收 **32.942 元（升值 0.5 分）**；台北外匯成交 **22.63 億美元**、台北及元太總成交 **32.82 億美元**（https://www.cna.com.tw/news/afe/202611190296.aspx ；https://money.udn.com/money/story/12509/9889341 ，皆 HTTP 200 確認）。金管會並宣布 **11/20 起升級 3.5% 限空令**（含 1,028 檔跌幅 ≥3.5% 個股隔日禁平盤下放空，https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ，HTTP 200）。

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；補齊台積電公告入股 HTTP 200 網址（無新進展）
- 事實：Anthropic（代號 **ANT**）定價 **每股 83.00 美元**（發行 9.8 億股、IPO 募資 **813.1 億美元**、加上晶片與雲端夥伴 260 億美元同步私募合計約 1,073 億美元、完全稀釋估值約 **1.5 兆美元**），將於 **美東 2026-11-19 09:30（台北 11/19 22:30）** 掛牌；截至台北時間 19:42（美東 06:42）美股尚未開盤，首日開盤價、收盤價與成交量將於明早 05:00 收盤後產生（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，HTTP 200）。
- 事實：台積電 11/19 正式公告透過 TSMC Partners 以 **每股 83 美元**取得 Anthropic 普通股 **6,024,096 股**（約 **5 億美元**，https://www.cna.com.tw/news/afe/202611190254.aspx ，HTTP 200）。掛牌前夕美東 11/18 收盤，**CoreWeave（CRWV）跌 4.13%、IREN 跌 3.61%、Nebius（NBIS）小漲 0.87%、Oracle（ORCL）大致持平**；同日 **NVDA 收跌約 2.9%**，**AVGO、AMD 上漲約 4%–5%**；今日 11/19 美股盤前儲存與記憶體股（MU、SNDK、STX、WDC、SKHY）同步受 ANT 掛牌激勵大漲 4%–5%（https://247wallst.com/investing/2026/11/18/coreweave-falls-5-despite-nvidia-sticking-to-its-financing-commitments-nebius-dips-oracle-holds-steady/ ；https://news.cnyes.com/news/id/6667734 ，皆 HTTP 200）。

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字（無新進展）
- 事實：ECB 11/18《金融穩定評估》Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（基於 LSEG 10/26 共識），指多數美國超大規模雲端業者 2026 年自由現金流因 AI 資本支出大於營運現金流而轉負（表層 FCF 口徑未納入未起租的表外租賃；表外承諾逾 4 兆美元係於圖表 A 與註腳 6 依 ASC 842 單獨揭露）（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200 確認）。
- 事實：四巨頭截至 2026-09-30 最新一季自報實際數字：Meta（Q3 2026）OCF $32.79B − CapEx（含融資租賃本金）$34.91B = **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）；Alphabet（Q3 2026）OCF $42.29B − 現金 PP&E $51.36B = **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）；Amazon（Q3 2026／TTM）Q3 單季 OCF $42.42B、淨現金 PP&E $75.93B（單季隱含 -$33.51B）、自報 **TTM FCF -$42.36B**（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）；Microsoft（Q1 FY27）OCF $58.02B − 現金 PP&E $39.37B = **+$18.6B（仍為正；計入新起租融資租賃總資本支出 $45.2B 後仍約 +$12.8B）**（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ，伺服器回傳 HTTP 403，保留前輪讀數）。

### TASK-B5｜阿里巴巴（BABA）與拼多多（PDD）皆已於 11/19 公布財報（更新 PDD 19:30 實績與對全球貿易／監管原話）；沃爾瑪（WMT）預計今晚 20:00 公布
- 事實（拼多多 PDD，Q3 2026，**已於美東 06:30／台北 19:30 公布**）：總營收人民幣 **1,083 億元（162 億美元）**，年對年持平（去年同期 1,083 億元），**低於** TradingView 所列市場預期 **1,155 億～1,217 億元**（其中交易服務年減 12% 至 485 億元、線上行銷年增 12% 至 598 億元）；**Non-GAAP 稀釋每 ADS 盈餘人民幣 21.04 元（3.14 美元）**，優於 TradingView 所列市場預期 **2.61～2.77 美元**（電話會議訂於台北 20:30）。聯席 CEO 陳磊對全球貿易與監管環境原話：`"As our global business adapts to an evolving trade and regulatory environment, we remain committed to deepening our supply chain investments."`（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ；https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ，皆 HTTP 200 確認）。
- 事實（阿里巴巴 BABA，Q2 FY27，**已公布**）：總營收人民幣 **2,715.19 億元**（+10% YoY，勝於香港 01 所列市場預期 2,698.49 億元），但 **Non-GAAP 淨利 199.09 億元（+92% YoY）遜於預期 265.7 億元**（Non-GAAP 每 ADS 盈餘 8.10 元）、資本支出飆升 60% 至 504.77 億元、自由現金流淨流出 **344.72 億元**，ADR 盤前挫逾 2%；CFO 徐宏對 AI 投資原話：`「隨著AI商業化不斷深入，我們會繼續審慎根據市場情況投入AI建設，注重提升資本回報率，並致力於盡早實現自由現金流轉正。」`（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ，HTTP 200 確認）。
- 事實（沃爾瑪 WMT，Q3 FY27，**尚未公布，美東 07:00／台北 20:00**）：TradingView 彙整市場共識營收 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）；執行長 John Furner 對關稅與消費原話：`"Customers are feeling some pressure, so we're proud of our investments... We'll do everything we can to keep prices as low as we can for customers throughout the rest of the year."`（https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ；https://www.businessinsider.com/walmart-using-tariff-refund-price-cuts-customer-experience-sales-2026-8 ）。

---

### CALL｜法說會與財報原話重點（過去 24 小時；新增 BABA、PDD、NTES 正式公布原話）

### CALL-BABA｜阿里巴巴（BABA）Q2 FY27：AI 雲外部收入年增 67%、自研玄鐵／平頭哥 Zhenwu V900 晶片與 Qwen 模型推進商業化（新增）
- 原話（CEO Eddie Wu）：`"Our full-stack AI capabilities continue to improve commercialization and delivered a strong quarter. Growth in Alibaba Cloud's recurring revenue from external customers was 67%, which drove an acceleration of overall cloud revenue growth with significantly improving profitability."`（https://investingnews.com/alibaba-group-announces-september-quarter-2026-results-and-interim-results-for-the-six-months-ended-september-30-2026/ ，HTTP 200 確認；電話會議於台北 20:00 舉行）。

### CALL-PDD｜拼多多（PDD）Q3 2026：營收持平下持續投資供應鏈以因應貿易與監管變化（新增）
- 原話（Co-CEO Lei Chen）：`"As our global business adapts to an evolving trade and regulatory environment, we remain committed to deepening our supply chain investments."`（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ，HTTP 200 確認；電話會議於台北 20:30 舉行）。

### CALL-NTES｜網易（NTES）Q3 2026：遊戲營收微降但毛利增 4.8%、持續推進跨平台新遊研發（新增）
- 原話（CEO William Ding）：`"While we continue to evolve our established titles with content and gameplay mechanics that appeal to a broader range of players, we are also steadily advancing our titles in development across genres, platforms and markets."`（https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ，HTTP 200 確認；電話會議於台北 20:00 舉行）。

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

### CALL-TJX｜TJX Companies（TJX）Q3 FY27 法說會：同店成長 4%，上調全年展望至區間上緣（無新進展）
- 原話：`"Consolidated comparable sales grew 4%, driven by continued strength at HomeGoods, TJX Canada, and TJX International, and we saw improved sales at Marmaxx. Importantly, we expect further improvement at Marmaxx in the fourth quarter."`（https://mlq.ai/news/tjxs-comparable-sales-rise-4-above-its-plan-and-it-narrows-its-full-year-outlook-toward-the-top-of-the-range/ ，HTTP 200）。

---

### NEXT-1｜事件：台股櫃買暴跌 7.22%＋1,028 檔納 3.5% 限空令 2.0＋世界／台化／萬泰科爆 1.29 億違約交割（更新 1,028 檔）
- 推理：
  - 最先受影響的資產：明日（11/20）適用平盤下禁空之 **1,028 檔**跌幅 ≥3.5% 台股與 TDR、櫃買高融資中小型 AI 股、台指期避險部位，以及權證造市券商帳上部位。
  - 傳導路徑：今日自營商賣超 233.03 億元中有 **214.40 億元**來自避險賣超，盤後證交所與櫃買中心緊接通報世界、台化（4,172.8 萬）、萬泰科合計 **1.29 億元**違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），金管會遂將 11/20 起借券上限由 3% 砍至 1% 並啟用 3.5% 跌幅平盤下禁空（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）：
    - 美股：**TSM（ADR）、NVDA、AVGO、SOXX、EWT**。
    - 台股：**台積電 (2330)、聯發科 (2454)、世界 (5347)、台化 (1326)、元大金 (2885) 等券商金控**。
  - 大家還沒注意到的間接受害者：**承銷高價 AI 認購權證的台灣中小型券商自營部與證券融資授信部門**——當 1,028 檔個股平盤下放空受限、自營避險單轉擠入台指期（三大法人期貨淨空單已達 -8,883 口），中小型股若買盤縮手更容易出現「無量鎖跌停」，放大 T+2 違約交割由證券商先代墊後的短期呆帳與資本適足率壓力。

### NEXT-2｜事件：阿里巴巴與拼多多 Q3 實績驗證「高 CapEx／策略投資期壓抑現金流」＋Anthropic 今晚 22:30 納斯達克掛牌（更新納入 PDD）
- 推理：
  - 最先受影響的資產：中概科技股 ADR（BABA、PDD、NTES、KWEB）、美系雲端大廠長債利差，以及今晚掛牌之 ANT 與新雲端／儲存族群（CRWV、NBIS、IREN、MU、STX、WDC）。
  - 傳導路徑：繼 ECB Box 3 揭露美系超大規模雲端商多數轉為負自由現金流後，BABA 今晚實績證明即使 AI 雲外部收入年增 67%，只要 CapEx 激增 60% 拖累 FCF（-344.72 億人民幣），股票仍會在盤前遭到懲罰（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ）；PDD 營收持平亦反映交易服務轉弱與供應鏈投資壓力（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ）：
    - 美股：**BABA、PDD、ORCL、CRWV、NBIS**。
    - 台股：**廣達 (2382)、緯穎 (6669)、鴻海 (2317)、英業達 (2356)、台達電 (2308)**。
  - 大家還沒注意到的間接受益者：**已具備高自由現金流防禦墊且資本支出節奏可控的資安軟體與低負債現金牛企業（如 PANW、TJX）**——當市場開始對「CapEx 吞噬 FCF」的基礎建設端要求折價，能靠軟體訂閱（PANW NGS ARR +66%）與庫存周轉快速變現的公司更容易吸納科技股撤出資金。

### NEXT-3｜事件：美中俄《四點和平宣言》宣示增產精煉石油產品 vs IEA 荷莫茲危機＋歐盟批准印尼 CEPA＋歐盟遭 AI 網攻（更新）
- 推理：
  - 最先受影響的資產：美國與亞洲煉油股裂解價差（VLO、PSX、MPC）、布蘭特原油遠月曲線、沙國／波灣主權債利差、歐洲銀行股與東南亞／歐洲汽車貿易鏈。
  - 傳導路徑：一方面胡塞飛彈碎片擊中沙國 PIF 總部且 IEA 警告波灣已斷供 28 億桶原油，但同晚美中俄《四點和平宣言》將「增加精煉石油產品生產與供應」列為共識（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ），同時歐盟批准與印尼消除逾 90% 關稅的 CEPA 貿易協定（https://www.aljazeera.com/economy/2026/11/19/eu-governments-approve-trade-deal-with-indonesia-to-offset-trump-tariffs ）：
    - 美股：**VLO、PSX、XOM、PANW、CRWD**。
    - 台股：**台塑化 (6505)、長榮 (2603)、陽明 (2609)、東陽 (1319)／車用零件、安碁資訊 (6690)**。
  - 大家還沒注意到的間接受害者：**高度依賴中東主權財富基金（如 PIF）作為晚期募資的私募基金，以及同時面臨中國／俄羅斯／美國增供精煉油品與美國高汽油庫存雙重擠壓的獨立煉油商**（昨日 EIA 汽油暴增 520 萬桶疊加今日三方宣言增加精煉品供應，使成品油利潤空間短期面臨雙向壓縮）。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 由 60% 降至 45%）」
- 最強反方證據：BEA 官方新聞稿已證實 9 月核心 PCE 年增確為 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ），The Conference Board 預估 10 月將升至 **3.3%**（https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026 ），且本站線上《財經日曆》卡片亦已載明 9 月為 `3.1%` 並自估 10 月為 `3.2%`。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法發布年增率，這題將成為「無法判定」；但只要有公布年增率，低於 3.0% 的空間極小。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：維持落在 2.4%–3.0% 僅約 **30%**（比你的 45% 低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露多數美系一線雲端商 FCF 轉負且表外承諾逾 4 兆美元（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ），今日 BABA 亦因 CapEx 增 60% 使 FCF 淨流出 344.72 億人民幣致 ADR 盤前跌逾 2%；IEA 11/19 警告荷莫茲構成史上最大能源威脅加上利雅德 PIF 大樓遭飛彈碎片波及；台股櫃買跌 7.22%、再現 1.29 億違約交割迫使金管會升級 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。
- 另一種同樣說得通的解釋：今日新台幣翻升收 32.942 元、日經（+0.71%）、韓股（+1.39%）、印度（+0.91%）收紅、歐股 STOXX 600 早盤 +0.3% 且 UniCredit 併購僵局化解，美中俄亦發布四點和平宣言，顯示壓力仍集中在高槓桿 AI 資本支出與籌碼面，尚未演變成無差別信貸擠兌。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：維持「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你的 80% 低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：11/18 美國 EIA 原油庫存暴增 340 萬桶、汽油暴增 520 萬桶（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ），加上今日美中俄《四點和平宣言》第 2 點明確計畫增加精煉石油產品生產與供應（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ），增添跌破 80 美元的下行風險；另一端 IEA 11/19 警告荷莫茲已造成史上最大斷供（28 億桶原油）且胡塞飛彈碎片擊中沙國 PIF 利雅德總部（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ），形成劇烈雙尾拉扯。
- 另一種同樣說得通的解釋：若美中俄增產共識配合庫存過剩，WTI 可能跌破 80 美元；若波灣基建遇襲擴大，油價可能瞬間衝破 100 美元——突破區間外的機率高於平靜市況。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **未來 72 小時波灣與荷莫茲海峽安全動態**。
- 機率估計：維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」（無新進展）
- 最強反方證據：中央社 11/19 引述《福斯新聞》報導川普親口指出，與黃仁勳有染的一名女子正遭美國政府調查是否為中國情報機構工作、以及是否協助走私晶片（https://www.cna.com.tw/news/aopl/202611193003.aspx ，HTTP 200）；同日輝達董事長瓊斯對員工重申「黃仁勳個人行為及缺乏坦誠」是董事會接受辭呈且永不回鍋的原因（https://www.cna.com.tw/news/aopl/202611190029.aspx ，HTTP 200）。
- 另一種同樣說得通的解釋：最初的確是「個人行為／缺乏坦誠」引發董事會 11/11 立即切割，但因牽涉對象本身被美方列為中國情報與晶片走私調查標的，**兩件事並非互斥，而是同一人物同時觸發公司治理與國安出口調查**。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節，11 月下旬～12 月初）**與 **美國政府對該涉案女子／走私網絡之起訴或調查公告**。
- 機率估計：維持「單純私人治理、完全無涉中國晶片調查」**25%–30%**，「個人行為與中國晶片／情報調查兩線交織」**70%–75%**。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（無新進展）
- 事實：ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**（已超過帳上負債），且投資級科技長債利差已相對於同評級企業債走寬（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q `Commitments and Contingencies / Uncommenced Leases` 追蹤，及 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜缺少「非公開交易 BDC 限額贖回（Gating）、私募信貸 SaaS 曝險與對沖基金主權債槓桿」監測（無新進展）
- 事實：FSB、聯準會 FEDS Notes 與 IMF／BIS／ECB 報告均聚焦非公開交易 BDC 限額贖回、私募信貸 SaaS 曝險與避險基金主權債槓桿。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ，HTTP 200）。

### BLIND-3｜缺少「高集中度雲端／金融／公部門資安中斷與 SEC Item 1.05 資安事件」警報（無新進展）
- 事實：今日（11/19）歐盟執委會證實遭 AI 滲透工具 ARTEX 網攻導致內部核心系統中斷逾 10 天（https://mlq.ai/news/european-commission-says-hackers-targeted-some-of-its-systems-as-pay-and-leave-tools-stay-offline-for-about-10-days/ ，HTTP 200）。
- 推理：監測 SEC 8-K Item 1.05 是否涉及高集中度第三方基建（AWS、Azure、GCP、Cloudflare、DTCC），可比股價更早捕捉系統性運作風險。免費資料源：CISA KEV JSON（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ，HTTP 200）＋ SEC EDGAR。

### BLIND-4｜「台股籌碼風向計」未自動加總「三大法人台指期合計淨口數」、且缺「每日違約交割金額」與「限空令燈號」（無新進展）
- 事實：今日證交所與櫃買中心再爆世界、台化（4,172.8 萬元）、萬泰科共 **1.29 億元**違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），金管會並宣布 **11/20 起升級 3.5% 限空令**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ，皆 HTTP 200），但目前「台股籌碼風向計」尚未加總三大法人台指期合計淨口數（11/19 -8,883 口），也未設「每日違約交割金額」與「限空令狀態」欄位。免費資料源：期交所「三大法人區分各期貨契約交易資訊」、證交所 `BFI82U` 與「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」（無新進展）
- 推理：建議在「IPO 觀察」補上大型 IPO 納入 S&P 500、Nasdaq-100 指數時程與被動 ETF 權重排擠效應說明。

---

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets）— 掛牌日情緒兩極且嘲諷估值（19:42 補充今日串細節）
- 討論內容與情緒：11/19 今日 r/wallstreetbets 熱議 ANT 以 83 美元定價、募資約 813 億美元於那斯達克掛牌，部分交易員賭開盤流動性衝高，但多篇熱門回文諷刺在科技股回檔期發巨型 AI IPO「猶如在茅草村開藍寶堅尼經銷商」，並擔憂早期內部人解禁賣壓（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ，HTTP 200 確認）。

### SENT-2｜PANW 併購與總經升息壓力（r/wallstreetbets / r/stocks）— 肯定資安併購動能但對 Fed 鷹派訊號謹慎（無新進展）
- 討論內容與情緒：今日討論同時關注 PANW 斥資 45 億美元收購 Applied Compute 帶動的資安盤前漲勢，以及聯準會官員偏鷹言論下科技與成長股數月來回檔的壓力（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-3｜台股 11/19 暴跌 1,768 點後「金管會限空令 2.0」（PTT 股板）— 熱議 1,028 檔 3.5% 平盤下禁空與違約交割（更新）
- 討論內容與情緒：11/19 下午金管會公告自 11/20 起實施「跌幅 ≥3.5% 個股隔日禁平盤下放空（計 1,028 檔）＋盤中借券上限降至 1%」，PTT 股板即時轉載 `[情報] 金管會發布限空令`（https://www.pttweb.cc/bbs/Stock/M.1795069467.A.DAC ，HTTP 200 確認），盤中／盤後閒聊直呼「大爆崩」，同步熱議台化、世界、萬泰科爆出 1.29 億違約交割、大摩對台積電 3,088 元看法（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，HTTP 200），以及記憶體多空論戰，情緒在「政策救市護盤」與「怕無量鎖跌停」之間拉鋸（情緒，非事實）。

### SENT-4｜NVDA 與沃爾瑪（WMT）財報（r/wallstreetbets）— 押注今晚 20:00 WMT 檢驗美國消費韌性（無新進展）
- 討論內容與情緒：押注今晚美東 07:00 公布的 WMT 財報將驗證美國底層與中產階級消費健康度，並持續在 NVDA 財報後爭論接班與估值修正（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ）。

### SENT-5｜UNH／醫療保險（r/stocks）— CMS CRUSH 規則陰霾下情緒偏悲觀（無新進展）
- 討論內容與情緒：醫療保險股受 CMS CRUSH 追溯 2018 年審計草案衝擊，散戶對管理式醫療與醫院類股情緒偏悲觀觀望（情緒，非事實）。

---

### SITE｜挑本站的錯（對照 2026-11-19 19:14 `upcoming.json`、19:27 `未來 14 天事件`、19:31 總覽即時頁面與本地 `research_feed/`）

### SITE-1｜`research_feed/forecast.json` 仍寫「9 月核心 PCE 數字：查無」，但線上《財經日曆》早已顯示 3.1%（無新進展）
- 本站寫了什麼：`research_feed/forecast.json` 第 130 行仍寫著 `9 月核心 PCE 數字：查無。`。
- 正確應該是什麼：BEA 官方新聞稿早已公布 9 月核心 PCE 年增 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，HTTP 200），且本站線上《財經日曆》PCE 卡片亦已載明此數值，應將前值同步回 `forecast.json`。

### SITE-2｜線上總覽（19:31 版）仍保留 `17:32`「台股沒找到消息」及 `16:34`「能源原因還不知道」，且「接下來 72 小時」仍列已公布的 BABA 與 PDD（19:42 更新）
- 本站寫了什麼：19:31 線上總覽顯示 `11-19 17:32 台北 盤中` 語音稿寫：`「至於原因，我沒有找到時間對得上的單一消息」`；「前幾班」內的 `16:34 緊急加班` 寫：`「能源這邊，我找不到時間對得上的原因」`；「接下來 72 小時」仍列 `11/19 21:00 ・財報・Alibaba Group Holding Limited財報（盤前）` 與 `PDD Holdings Inc.財報（盤前）`。
- 正確應該是什麼：BABA（18:18 前）與 PDD（19:30／美東 06:30）均已公布財報；台股急殺有當日自營商避險賣超 214.40 億、1.29 億元違約交割與金管會升級 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；11/18 能源股下跌亦有 EIA 原油／汽油庫存暴增可對照（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ）。

### SITE-3｜線上 `upcoming.json`（19:14 版）尚未反映 BABA 與 PDD 已公布實績、WMT 發稿時間晚 1 小時、HPE 共識略低且漏列 ANT IPO 與 INTU／ROST／GAP（19:42 更新）
- 本站寫了什麼：`https://wallstreet-sentinel.pages.dev/upcoming.json`（`asof: "2026-11-19 19:14"`）仍將 `BABA` 與 `PDD` 列為尚未公布的 `2026-11-19T08:00`（台北 21:00）預告、將 `WMT` 時間列為 `08:00`（台北 21:00）、將 `HPE` `eps_f` 列為 `1.17`，且未收錄今晚 **Anthropic (ANT)** 上市與盤後之 `INTU`、`ROST`、`GAP`。
- 正確應該是什麼：BABA 與 PDD 皆已公布（PDD 於美東 06:30／台北 19:30 發布，https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ）；WMT 官方預告發稿為美東 **07:00（台北 20:00）**、08:00 才為電話會議（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ）；`HPE` 市場共識調整後 EPS 為 **1.27–1.29 美元**（https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ）。

### SITE-4｜線上《未來 14 天事件》（19:27 版）仍未標明今日美債標售為「10 年期 TIPS」（19:42 重驗仍未改）
- 本站寫了什麼：線上 `p-news` 分頁《未來 14 天事件》（`最後更新 11-19 19:27`）仍列 `11-19 美債 10 年期標售（增額） $19B`。
- 正確應該是什麼：今日 $19B 增額標售為 **10 年期 TIPS（抗通膨公債）**（https://www.treasurydirect.gov/auctions/announcements-data-results/ ，HTTP 200），建議標明「TIPS」以免新手與一般 10 年期名目公債標售混淆。

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆（對照 11-19 19:27 線上版《未來 14 天事件》與 19:14 `upcoming.json`）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳川習會與美中俄三方峰會（已結束並發布四點和平宣言）；南非央行維持 7.25% 不變（已公布）；BABA、NTES、PDD Q3 財報（均已公布）；台北 20:00 **WMT 財報／NTES、BABA 法說**、20:30 **PDD 法說**；美東 09:30（台北 22:30）**Anthropic (ANT)、MapLight (MPLT)** 掛牌；美東 12:30（台北 11/20 01:30）芝加哥聯準銀行總裁 Goolsbee 問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；美東 13:00（台北 11/20 02:00）**美債 10 年期 TIPS 增額標售 $19B**；美東 15:00（台北 11/20 04:00）聯準會理事會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP** 財報（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  2. **11/20（五）**：**台股金管會 3.5% 有條件限空令與盤中借券上限 1% 正式上路**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；**印度強氣旋「阿克萬」中午登陸奧里薩邦**；**台灣經濟部 10 月外銷訂單**（台北 16:00，https://money.udn.com/money/story/10869/9879179 ）；**美股月選擇權到期（OPEX）**；**密大消費者信心指數終值**（美東 10:00／台北 23:00）；**SanDisk (SNDK) 1 拆 8 拆股後首日交易**（https://www.fool.com/investing/2026/11/16/sandisk-splits-its-stock-8-for-1-on-nov-19-flash-memory-prices-still-matter-more-than-the-share-count/ ）。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM** 財報。
  5. **11/24（二）**：美東盤前（台北 20:00–21:00）**ADI、MDT、BBY、BURL、DKS、BILI**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY**。
  6. **11/25（三）**：美東盤前（台北 21:00）**DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與 10 月耐久財訂單；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**；台北 11/26 **宏于電機（7869，台股上櫃）掛牌**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/28（六）**：**台灣 2026 九合一地方選舉投票日**。
  10. **11/29（日）**：**OPEC+ 部長級會議**（討論 2027 年產量配額）。
  11. **11/30（一）**：**MSCI 季度調整台股收盤生效（台北 13:30）與月底資產再平衡**。
  12. **12/01（二）**：美東 10:00（台北 23:00）**ISM 製造業 PMI 與 10 月 JOLTS 職位空缺**；**CRWD、MRVL、OKTA、NTAP** 盤後財報；**韓國 11 月出口初值**。
  13. **12/02（三）**：美東盤後（台北 12/03 05:00）**CRM、SNOW、ZS** 財報（https://www.tradingview.com/news/tradingview:c28752bb00e6f:0-zscaler-hosts-2026-investor-day-reaffirms-q1-and-fiscal-2027-guidance/ ）。
  14. **12/03（四）**：美國參議院銀行委員會就先進晶片出口與資料中心基礎設施舉行聽證會。
- 對照本站 11/19 19:27 線上版《未來 14 天事件》與 19:14 `upcoming.json`：
  - **正確部分**：《未來 14 天事件》已列 11/19 `H.4.1`、`Unemployment Insurance Weekly Claims Report`、`美債 10 年期標售（增額）$19B`、11/20 `OPEX`、11/25 `Debt to Gross Domestic Product Ratios` / `Gross Domestic Product` / `Personal Income and Outlays`、11/30 `月底資產再平衡`、12/01 `JOLTS`；`upcoming.json` 已列 WMT/BABA/PDD、MPLT、HPE、ADI、MDT、DELL、HPQ、DE。
  - **漏掉與錯列部分**：《未來 14 天事件》仍漏掉 **11/20 金管會限空令 2.0 上路與 SNDK 拆股、11/20 台灣 10 月外銷訂單、11/21 韓國 20 日出口、11/25 聯準會褐皮書、11/26 韓國央行、11/26 感恩節休市與 11/27 半天交易、11/28 台灣九合一選舉、11/29 OPEC+ 會議**；`upcoming.json` 仍漏掉 **ANT（Anthropic IPO）、INTU、ROST、GAP（今晚盤後）、ZM、BBY、BURL、DKS、ADSK、WDAY、BILI**，且 11/19 19:27 版仍將 `11-19 美債 10 年期標售` 漏標「TIPS」。

---

### CODE-1｜wsb/analytics/canary.py：第 365–366 行 `str(a1["asof"])[:10] > ...` 遇 `asof` 為 `None` 時把 `"None"` 當成最新即時報價，並繞過 `_age_check` 過期檢查
- 檔案路徑與行號：`wsb/analytics/canary.py` 第 365–366 行（`vix1d_light()` 函式），連動第 398–400 行（`_age_check()`）。
- 那一行在做什麼：檢查 `^VIX1D`（`a1`）與 `^VIX`（`a`）即時報價是否同日且比日線歷史資料更晚，若成立就用即時報價計算當日 `VIX1D ÷ VIX` 比值與 `asof` 日期。
- 為什麼有問題：當 `a1` 與 `a` 同時存在非零 `"price"` 但兩者 `"asof"` 皆為 `None` 時，`a1.get("asof") == a.get("asof")`（即 `None == None`）會成立為 `True`，且 `str(a1["asof"])[:10]` 變成 `"None"`。在 Python 字串比較中 `"None" > "2026-11-18"` 為 **`True`**，導致第 366 行把 `asof` 設成 `"None"`；隨後第 423 行呼叫 `_age_check()` 時，第 398 行 `date.fromisoformat("None")` 會拋出 `ValueError` 被第 399 行吞掉，使過期即時報價直接繞過新鮮度保護亮燈。
- 建議怎麼改：第 365 行先確認 `a1.get("asof") and a.get("asof")` 皆非空、且取 `d1 = str(a1["asof"])[:10]` 驗證格式為 `YYYY-MM-DD` 後再做日期比較。
- 確定度：高。

### CODE-2｜wsb/data/forced_flows.py：第 250 與 307 行使用主機當地 `date.today()` 而非美東交易日，跨日時會提前切換季初基準並漏掉美股當日指數調整警示
- 檔案路徑與行號：`wsb/data/forced_flows.py` 第 307 行（`refresh()` 呼叫 `build(..., date.today(), ...)`）與第 235、250、333 行。
- 那一行在做什麼：決定「尚未發生的未來指數調整事件（`e["date"] >= today`）」、明日是否觸發調整事件警示（`alerts(v, today)`），以及退休金季底再平衡的季初起始日（`quarter_start(today)`）。
- 為什麼有問題：`settings.yaml` 時區為 `Asia/Taipei`（若在 GitHub Actions 則為 UTC），當台北 08:00–22:30（或 UTC 00:00–05:00）執行 `refresh()` 時，主機的 `date.today()` 已進入隔天，而美股前一個交易日可能剛進行或甚至在跨季日（1/1、4/1、7/1、10/1 台北白天對應美東 12/31、3/31、6/30、9/30 盤中／收盤前）就提前切入新的一季。這會導致第 250 行 `quarter_start(today)` 在美東季末收盤前便跳至新季、並使第 235 行過早把美股「當天」的 `sp`/`russell`/`msci` 調整事件當成過去事件濾除。
- 建議怎麼改：改用 `wsb.data.econcal.us_today()` 作為 `build()` 與 `alerts()` 的美東基準日（台股事件可維持對應的 `tw_date` 判斷）。
- 確定度：中。

（備註：本小時台北 19 時批次 `i % 24 == 19` 共 12 檔：`tools/site_alerts.py`、`tools/site_event_react.py`、`tools/site_newslive.py`、`tools/site_twbank.py`、`wsb/analytics/canary.py`、`wsb/analytics/fullscan.py`、`wsb/analytics/rates_radar.py`、`wsb/analytics/tw_link.py`、`wsb/data/country_risk.py`、`wsb/data/forced_flows.py`、`wsb/data/pension_ldi.py`、`wsb/data/us_fiscal.py` 皆已逐行讀完。其中 `pension_ldi.py` 與 `us_fiscal.py` 的 `try_each` 由 `wsb/data/freshness.py` 第 76 行 `due()` 以 `setdefault` 初始化不會 `KeyError`；`rates_radar.py` 警戒線出處均載於 `settings.yaml`、`ai_borrowing()` `interest` 與 `wsb/data/fundamentals.py` 口徑一致，均依規則不濫報。）

---

其他今天的大事：
- 拼多多（PDD）於台北 11/19 19:30 公布 Q3 2026 財報，營收人民幣 1,083 億元（年對年持平，低於預期約 1,155 億），Non-GAAP 稀釋每 ADS 盈餘人民幣 21.04 元（3.14 美元）優於預期；同日阿里巴巴（BABA）Q2 FY27 營收 2,715.19 億元優於預期但 FCF 淨流出 344.72 億元致 ADR 盤前挫逾 2%，網易（NTES）Q3 營收 279 億元（-1.8% YoY）遜預期（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ；https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ；https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ，皆 HTTP 200）。
- 美中俄深圳三方領袖峰會結束，中俄官媒發布《四點和平宣言》宣示推動聯合國改革、**增加精煉石油產品生產與供應**及核風險對話，川普已搭機離開中國（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ，HTTP 200）。
- 歐盟各國政府批准簽署並暫行適用歐盟—印尼全面經濟夥伴協定（CEPA），取消逾 90% 雙邊關稅、每年省下約 6 億歐元以對沖川普關稅；同時歐盟執委會證實遭 AI 滲透工具 ARTEX 網攻導致人資與醫療系統離線約 10 天（https://www.aljazeera.com/economy/2026/11/19/eu-governments-approve-trade-deal-with-indonesia-to-offset-trump-tariffs ；https://mlq.ai/news/european-commission-says-hackers-targeted-some-of-its-systems-as-pay-and-leave-tools-stay-offline-for-about-10-days/ ，皆 HTTP 200）。
- 台股 11/19 收盤重挫 **1,768.02 點（-4.40%）至 38,426.89 點**、櫃買跌 7.22% 至 285.33 點，三大法人賣超 **461.03 億元**，盤後爆出世界、台化（4,172.8 萬元）、萬泰科合計 **1.29 億元**違約交割；金管會宣布 **11/20 起將 1,028 檔跌幅 ≥3.5% 個股納入平盤下禁空並降借券上限至 1%**；新台幣 16:00 翻升收 **32.942 元**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190182.aspx ；https://stock.ltn.com.tw/article/m7hjf9c9axqq ，皆 HTTP 200）。
- IEA 11/19《2026 世界能源展望》警告荷莫茲海峽危機為史上最大能源安全威脅（累積斷供 28 億桶油），同日葉門胡塞武裝飛彈攔截碎片擊中利雅德沙國主權基金（PIF）總部大樓（https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ；https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ，皆 HTTP 200）。

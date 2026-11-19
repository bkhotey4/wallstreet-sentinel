台北時間 2026-11-19 20:52

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）、整體 PCE 年增率為 **3.6%**（月增 **0.5%**），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，台北時間 2026-10-29，前輪確認）。
- 事實：之所以 9 月核心 PCE（3.1%）反過來高於核心 CPI（2.6%），根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 高於核心 CPI 的倒掛現象（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，前輪確認）。
- 事實：本地 `research_feed/forecast.json` 第 130 行仍寫 `9 月核心 PCE 數字：查無。`，而線上 `#econ`《PCE 物價》卡片（`11-19 13:12` 更新）已估算 10 月核心 PCE 月增約 `0.26%`（年增約 `3.2%`），惟線上 `#overview`《一個月後的總經》（`11-19 07:03`）仍顯示 `2.4%–3.0%` 機率 `60%`。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型（~3.2%）與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照（無新進展）
- 事實：歐洲央行（ECB）2026 年 11 月《金融穩定評估》Box 3（"The debt financing of AI and its implications for financial stability"）明確列出美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 共識（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，台北時間 2026-11-18，前輪確認）。
- 事實：ECB Box 3 正文對自由現金流的口徑為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（僅以**資本支出超過營運現金流**作為表層口徑，未把尚未起租的表外租賃算進單季現金流）；同時於圖表 A 與註腳 6 依美國會計準則 **ASC 842** 單獨指出，已簽約但資產尚未投入使用的租賃與算力承諾在起租前不計入資產負債表負債，這類表外承諾合計已逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，前輪確認）。
- 事實：四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與租賃口徑落差如下：
  - Meta（Q3 2026）：營運現金流 **$32.79B**，資本支出（含融資租賃本金償還）**$34.91B**，自報自由現金流為 **-$2.12B（轉負）**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ，前輪已讀）。
  - Alphabet（Q3 2026）：營運現金流 **$42.29B**（$42,290M），現金 PP&E 購置（不含融資租賃）**$51.36B**（$51,355M），自報自由現金流為 **-$9.07B（-$9,065M，轉負，含 52 億美元歐盟罰款支付）**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ，前輪已讀）。
  - Amazon（Q3 2026／TTM）：單季營運現金流 **$42.42B**、單季淨 PP&E 購置 **$75.93B**（隱含單季 **-$33.51B**），公司自報 **TTM 自由現金流 -$42.36B（-$42,357M，轉負）**，該口徑僅扣現金淨 PP&E、未扣額外揭露之新簽融資租賃資產（Q3 單季 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ，前輪已讀）。
  - Microsoft（Q1 FY27）：營運現金流 **$58.02B**，現金 PP&E 資本支出 **$39.37B**，自報自由現金流為 **+$18.6B（仍為正值，年減 27%）**；若計入新起租之融資租賃，總資本支出達 **$45.2B**，扣除後仍餘約 +$12.8B，印證 ECB 精準寫 `"most"` 而非全部（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ，伺服器阻擋自動化請求，維持前輪已讀數字）。

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（20:52 以 live 網頁實測更新）
- 推理：檢視 `research_feed/claude_notes.md`、`research_feed/forecast.json`、`tools/site_events.py`、`research_feed/macro_voice.json`（`20:01` 更新）與 20:33 產生的線上網頁 `https://wallstreet-sentinel.pages.dev`，最常「下太快」的是這兩種捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：例如 `claude_notes.md` 第 14 行未先核對 `bea.gov` 或本站 `#econ`《PCE 物價》卡片前，因「核心 PCE 通常比核心 CPI 低」就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推區間；`forecast.json` 第 65–73 行先前亦曾用單一 `BAMLH0A0HYM2`（3.43%）斷言信用市場無壓力（第 3 輪你已修正）。
  2. **把「預設預估時間／關鍵字比對不到」當成「還沒公布／找不到原因／沒有發生」**：在剛打開的線上網頁（頁面產生 `11-19 20:33 台北`），#econ《各公司最新財報重點》明明**已經列出 WMT `2026-11-19` SEC 8-K（營收 `US$188.80B`）**、《即時新聞》也已經在報 WMT 財報後盤前下跌，但同一時刻的《接下來 72 小時》、《重大事件倒數》（倒數 `0 天 0 小時 16 分`）、《美股財報日曆》與 `20:01` 的 `macro_voice.json` 卻全部還把 WMT、BABA、PDD 寫成「今晚 21:00 才公布」；同樣的，`每日總經情勢` 語音稿講「今晚看 Anthropic 掛牌」，但同一張卡片裡的《接下來 72 小時》和 `#econ`《IPO 觀察》卻放著 **2025/10 就已上市的 MapLight（MPLT）**、完全沒有 Anthropic。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標（20:52 補充 20:41 live 盤前報價）
- 事實：中央社 11/19 16:46 報導，台積電正式代子公司 TSMC Partners 公告以 **每股 83 美元**取得 Anthropic 普通股 **6,024,096 股**，總金額約 **5 億美元**（持股約 0.03%，https://www.cna.com.tw/news/afe/202611190254.aspx ，前輪確認）。截至台北 20:41 `/api/gemini_ask` 顯示，Anthropic 今晚 22:30 掛牌前，AI 硬體與儲存鏈盤前全面反彈：**PDD +7.1%、CRWD +6.4%、STX +6.0%、SKHY +5.7%、WDC +5.6%、SNDK +5.4%、MU +5.0%、DELL +4.5%、MRVL +4.5%、INTC +4.5%、LRCX +4.4%**；同日已公布的財報明顯懲罰自由現金流惡化者（**BABA** 單季 CapEx 飆 60%、FCF 流出 344.72 億人民幣，盤前走低）、獎賞縮表控費者（**PDD** 盤前 +7.1%～9%）。
- 推理：這印證市場正用極高倍數定價 Anthropic 今晚的算力承諾。若今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，傳導先後順序維持如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：負債比高、高度仰賴大模型算力長約抵押融資，且 Anthropic 轉向透過博通租賃 3.5 GW Google TPU 機櫃自建資料中心（https://www.cna.com.tw/news/afe/202611190156.aspx ），直接稀釋第三方租賃溢價。隔天（11/20）可驗證指標：`CRWV`、`NBIS` 相對 `QQQ` 的開盤超額跌幅，及新雲端無擔保債二級殖利率走勢。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸**：ANT 公開發行募資約 813 億美元（含 260 億美元同步私募合計約 1,073 億美元）、完全稀釋估值約 1.5 兆美元，若破發將壓縮 OpenAI 與晚期 AI 獨角獸 IPO 窗口。隔天可驗證指標：`ARCC`、`BIZD`、`BX`、`APO` 股價與承銷商護盤（stabilizing bid）報導。
  3. **最後且分化：晶片與機櫃合作夥伴（NVDA、AVGO、GOOGL、AMZN、MSFT、MU、台積電等同步私募出資方）**：主要承受公允價值重估回吐，但 Anthropic 轉向自建反而讓博通與 TPU 機櫃組裝廠受關注。隔天可驗證指標：`AVGO`／`NVDA` 相對 `^SOX` 強弱與次日選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態（20:52 更新 live 市場與歐盟政策）
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意且續獲跨市場驗證**：ECB Box 3 佐證多家美系雲端商 FCF 轉負、表外承諾逾 4 兆美元；今日 **BABA** Q2 FY27 單季 CapEx 飆升 60% 至 504.77 億人民幣、FCF 淨流出 **344.72 億人民幣**（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ），同時 **PDD** 靠砍行銷費用達成獲利超預期（盤前 +7.1%～9%）。市場對「燒錢換成長」的容忍度明顯下降。
  2. **主線 2（輝達治理風波 vs 出口調查）— 部分同意，兩條線已證實交織且台積電高層赴美穩鏈**：中央社引述《福斯新聞》專訪指涉案女子同受中國情報與晶片走私調查（https://www.cna.com.tw/news/aopl/202611193003.aspx ），另《聯合報》與《鏡週刊》亦證實台積電高層（張曉強）親赴輝達美國總部固鏈、確認 Rubin 與 CoWoS 訂單不變。建議第 4 輪整併為「個人治理與國安調查同源交織，但硬體供應鏈尚未鬆動」。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，補充 WMT 消費韌性**：剛公布的 **WMT Q3 FY27** 營收 **1,888 億美元（+5.2% YoY）**、美國同店銷售 **+2.9%** 並上調全年 EPS 指引至 **$2.84–$2.89**（https://www.stocktitan.net/sec-filings/WMT/8-k-walmart-inc-reports-material-event-0371aee37dfe.html ），顯示美國必需消費與高所得客群轉進平價通路仍強，並未出現衰退失速，反而讓聯準會更沒有理由在 12/9 放緩升息步調。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意，荷莫茲油輪觸雷 vs 歐盟延後甲烷規範／美中俄增供**：荷莫茲東側傳出油輪觸及水雷起火（https://english.alarabiya.net/News/middle-east/2026/11/19/three-oil-tankers-catch-fire-after-hitting-naval-mines-east-of-strait-of-hormuz-report ）、IEA 警告波灣就算斥資 400 億美元建繞道管線仍難免遭襲；但另一端歐盟 11/19 同意將油氣煤進口甲烷申報延後兩年至 2029–2030 年以緩解供應壓力（https://europeansting.com/2026/11/19/methane-deal-to-delay-reporting-and-monitoring-for-energy-importers/ ），加上美中俄宣言增供成品油與 EIA 累庫，Brent 期貨報價在 **$91.5–$92.2**（Yahoo 即時報價 `BZ=F` 約 **$89.94–$90.12**）、WTI 約 **$83**，維持 **55%**。
  5. **主線 5（「風險升級」劇本 33% vs 40%）— 同意方向一致**，差距 7 個百分點（但需注意 VIX 今晚盤前已從 24.6 回落至 22.2 左右，短線情緒稍緩）。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題（20:52 更新 live 頁面驗證）
- 1. 我在 20:42 實測線上 `wallstreet-sentinel.pages.dev` 發現嚴重的**同頁面自相矛盾**：`每日總經情勢` 語音稿（`20:01`）寫今晚看 **Anthropic** 掛牌，但同一張卡片裡的《接下來 72 小時》與 `#econ`《IPO 觀察》卻列出 **MapLight Therapeutics（MPLT，其實早在 2025/10/27 就已 IPO）**、完全沒有 Anthropic；同時 `#econ`《各公司最新財報重點》已經抓到 **WMT `2026-11-19` SEC 8-K（$188.80B）**，但《接下來 72 小時》、《重大事件倒數》、《美股財報日曆》與 `macro_voice.json` 仍全部顯示 WMT「尚未公布／今晚九點」。請問要怎麼讓 `site_events.py` 和 `macro_voice` 在讀到當日已公布 8-K 後自動把該公司從「即將公布」剔除，以及為什麼 `ipo_data.py` 會把已上市一年的 `MPLT` 放進「即將定價」卻漏掉 `ANT`？
- 2. 我在線上 `#econ`《美股財報日曆》（`20:33` 更新）核對未來 10 天財報共識時，發現多檔科技股與華爾街共識落差極大：**ADSK** 站上寫 EPS 預期 `2.27`（公司財測與 Non-GAAP 共識為 `3.04–3.09`）、**WDAY** 寫 `1.28`（共識 `2.74–2.75`）、**ZM** 寫 `1.00`（共識 `1.49`）、**HPE** 寫 `1.17`（公司財測 `1.20–1.30`、共識 `1.27–1.29`），推測是 Nasdaq 來源混用 GAAP 與 Non-GAAP 口徑。請問本站要不要在財報日曆加上口徑說明或比對公司財測？
- 3. 今日（11/19）**WMT** 營收與獲利雙雙優於預期並上調全年展望、**PDD** 靠砍行銷費用使獲利大勝預期（盤前 +7.1%～9%），但 **BABA** FCF 轉負大失血且 **NTES** 營收獲利雙遜（盤前 -3.5%～5%）。在「美國消費仍撐得住＋AI 燒錢大廠遭懲罰」下，第 4 輪你是否要調整 `forecast.json`「消費與進口商品轉弱」與「偏鷹沒出事（53%）」的權重？

---

### WIDE-1｜荷莫茲海峽東側接連傳出油輪觸水雷受損＋IEA 警告 400 億美元繞道管線仍難避地緣瓶頸＋胡塞碎片擊中沙國 PIF 總部（20:52 補實已開啟之 Al Arabiya 單篇原文網址）
- 事實：外電與伊朗媒體 11/19 報導，荷莫茲海峽東側與南側航道近期傳出三艘油輪疑似觸及水雷起火並失去動力（另有阿聯 ADNOC 相關油輪 *Navig8 Messi* 遇襲致船員受傷失蹤），伊朗方面聲稱船隻偏離其規定航道；美軍中央司令部（CENTCOM）則持續進行掃雷與護航（https://english.alarabiya.net/News/middle-east/2026/11/19/three-oil-tankers-catch-fire-after-hitting-naval-mines-east-of-strait-of-hormuz-report ，台北時間 2026-11-19）。同日 IEA 於《2026 世界能源展望》警告荷莫茲已累計中斷 **28 億桶原油與 600 億立方公尺天然氣**，且就算波灣產油國斥資 **400 億美元**興建日運量 700 萬桶的繞道輸油管線，替代路線仍高度暴露於飛彈與無人機襲擊風險中（https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ）。11/19 同日下午胡塞飛彈攔截碎片亦損及利雅德沙國主權基金（PIF）80 層總部大樓（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ）。
- 推理：美股焦點停在昨日 EIA 庫存增加，忽視了「海峽水雷化」與「繞道管線亦不安全」對遠期能源風險溢價與波灣金融中心的衝擊。
- 先影響資產：布蘭特原油遠月價差、油輪運價與戰爭險保費、波灣主權債 CDS。

### WIDE-2｜挪威國營能源巨頭 Equinor 證實遭網攻（非病毒、復原未定）＋歐盟 11/19 妥協延後油氣煤進口甲烷申報規範 2 年（20:52 補實 The Record 原文與歐盟甲烷延後協議）
- 事實：挪威國營油氣巨頭 **Equinor** 證實自 11/17 起偵測到針對部分企業 IT 系統與內部郵件的持續性網路攻擊並通報挪威國家安全局（NSM）與海洋工業監管局，截至 11/19 油氣生產與對歐天然氣出口未受影響、亦非病毒攻擊或資料外洩，但全面復原仍無時間表（https://therecord.media/norway-equinor-cyberattack-energy ，台北時間 2026-11-19）。同日歐盟執委會亦證實遭開源 AI 滲透工具 **ARTEX** 攻擊致內部人資與醫療報銷系統離線約 10 天（https://mlq.ai/news/european-commission-says-hackers-targeted-some-of-its-systems-as-pay-and-leave-tools-stay-offline-for-about-10-days/ ）。此外，歐洲議會與歐盟理事會談判代表 11/19 達成臨時協議，因擔憂中東衝突推升能源供應風險與價格，將原訂 2027 年上路的原油／天然氣／煤炭進口商**甲烷監測與申報規定（MRV）延後兩年至 2029 年 1 月 1 日**、甲烷強度申報延至 **2030 年 8 月 5 日**（https://europeansting.com/2026/11/19/methane-deal-to-delay-reporting-and-monitoring-for-energy-importers/ ，台北時間 2026-11-19）。
- 推理：歐洲剛承受中東天然氣斷供壓力與本土能源商 IT 網攻風險，歐盟被迫在能源安全與減碳合規之間向美國與卡達等供應方妥協延後甲烷規範，短期有助緩解歐洲 LNG 與煤油進口斷鏈風險，但也顯示歐洲能源體系脆弱度極高。
- 先影響資產：歐洲天然氣期貨（TTF）、歐洲公用事業與能源股、資安股（PANW、CRWD）、挪威克朗（NOK）。

### WIDE-3｜APEC 深圳「川習會（30 對 30 協議）」與美中俄首次三方《四點和平宣言》＋中國稀土出口許可制反制籌碼（無新進展）
- 事實：11/19 中午美中「川習會」於深圳登場，雙方依「**30 對 30 協議**」同意各自對價值 **300 億美元**商品削減關稅（https://www.cna.com.tw/news/aopl/202611193005.aspx ）；隨後美中俄舉行約 90 分鐘三方領袖峰會，川普於台北 **18:48** 搭空軍一號離華，中俄官媒發布《**四點和平宣言**》：（1）推動聯合國改革；（2）**三國計畫增加精煉石油產品生產與供應**；（3）反對 ICC 濫用管轄權；（4）重申核戰打不得並展開降核風險對話（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ）。另一方面，面對美國 11/19 生效的遠端算力管制，北京仍緊握嚴格的**稀土出口許可審查制度**作為談判與反制槓桿。
- 推理：美國對「遠端 AI 算力」全面收緊，而三方僅在傳統關稅小幅退讓（300 億美元）與成品油供給上達成口頭宣言，高階晶片與稀土關鍵原物料的結構性對立並未解除。
- 先影響資產：USD/CNH、成品油裂解價差、稀土／關鍵礦產股（MP）、中概股（KWEB）。

### WIDE-4｜巴西參院 11/18 通過 500–600 億雷亞爾財政緊縮案（PLP 299/2026）移送眾院＋財長預告續推緊縮＋巴西被美列入 AI 晶片轉運審查名單（20:52 補實 Poder360 單篇原文網址）
- 事實：巴西參議院於 11/18 完成政府財政緊縮包裹法案（**PLP 299/2026**）全數修正案表決並移送眾議院，擬於 2027 年改善公共帳目約 **500 億至 600 億雷亞爾**、把聯邦實質支出成長上限壓低至 **2.0%** 並縮減稅收抵減；財政部長 **Dario Durigan** 公開強調政府三權都「沒有無差別支出的許可」，並預告短期內將續推財政整頓（https://www.poder360.com.br/poder-congresso/nao-ha-licenca-para-gasto-indiscriminado-dos-3-poderes-diz-durigan/ ，台北時間 2026-11-19）。同時美國商務部 BIS 11/19 生效的遠端算力新規（`2026-23529`）亦將**巴西**與印尼、馬來西亞、新加坡、泰國並列為先進晶片轉運高風險審查國（https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors ）。
- 推理：美股新聞幾乎未注意拉美最大經濟體巴西一方面試圖以更硬的財政紀律穩住匯率與債市、另一方面卻因被美納入 AI 晶片轉運名單而面臨科技資本支出放緩壓力。
- 先影響資產：USD/BRL、巴西主權債與 EWZ、拉美資料中心投資項目。

### WIDE-5｜歐盟批准對印尼全面貿易協定（CEPA）＋日本央行重申升息與熊本 M5.7 餘震＋印度 CPI 破 6% 與氣旋「阿克萬」11/20 登陸＋南非央行 11/19 利率決策（20:52 補充南非 SARB）
- 事實：歐盟部長理事會 11/19 正式批准並暫行適用**歐盟—印尼 CEPA**，取消逾 **90%** 雙邊關稅、5 年內將印尼對歐盟汽車的 **50%** 關稅歸零，年省約 **6 億歐元**以對沖川普關稅（https://www.aljazeera.com/economy/2026/11/19/eu-governments-approve-trade-deal-with-indonesia-to-offset-trump-tariffs ）；義大利 UniCredit 承諾保留 Commerzbank 法蘭克福總部化解德國反對，帶動歐股 STOXX 600 反彈 +0.3% 至 645.85 點（https://economictimes.indiatimes.com/markets/us-stocks/news/european-shares-rebound-as-anthropic-ipo-boosts-tech-stocks-commerzbank-rallies/articleshow/135985666.cms?from=mdr ）。日本央行總裁植田和男 11/19 在國會淡化疲軟消費、警示日圓偏弱與油價恐推升潛在通膨破 2% 上行風險，強化 12 月升息至 **1.50%** 預期；熊本清晨 M5.7 餘震造成九州新幹線局部停駛但尚無 JASM 重大停工回報（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ；https://www.chinadailyasia.com/hk/article/642914 ）。印度 10 月 CPI 升至 **6.09%** 破央行上限，且強氣旋「阿克萬」預計 11/20 中午登陸奧里薩邦已撤離逾 10 萬人（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ；https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ）。南非央行（SARB）同日 15:00 SAST 舉行年內最後一次利率決策，因 10 月通膨回升至 5.2%、南非幣跌至年內低點，市場普遍預期維持 **7.25%** 不變（待官方新聞稿確認，先依現有資訊列為背景）。
- 推理：在聯準會 12/9 升息幾乎完全定價外，日銀 12 月升息至 1.50% 與印度通膨／天災衝擊正同步收緊全球與亞洲流動性，歐洲則以對外零關稅協定與銀行整併換取緩衝。
- 先影響資產：USD/JPY、EUR/USD、歐系汽車與銀行股（EUFN）、INDA、USD/INR 與 USD/ZAR。

---

### A｜今天的大動（依 `https://wallstreet-sentinel.pages.dev/api/gemini_ask` 台北 2026-11-19 20:41 即時 12 檔題目清單逐題回答）

### PANW｜Palo Alto Networks（PANW）今天 +9.6%（盤前）：Q1 FY27 財報優於預期＋45 億美元併購 Applied Compute＋多家券商上調看法
- 同意本站（Yahoo 與 MarketWatch 已涵蓋 Q1 FY27 財報與 AI 資安題材）；本站漏掉的：
  - 事實：美東 11/18 盤後公布 Q1 FY27 營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億）、Non-GAAP EPS **1.05 美元**（優於預期 0.97 美元）、NGS ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**（FactSet 共識 141.7 億）、調整後 EPS 指引至 **4.26～4.30 美元**（FactSet 共識 4.18 美元），並宣布以 **45 億美元**全股票收購 **Applied Compute**（https://www.prnewswire.com/news-releases/palo-alto-networks-reports-fiscal-first-quarter-2027-financial-results-302944393.html ；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，台北時間 2026-11-19）。
  - 事實：KeyBanc 分析師 Eric Heath 維持／調升評等至 `Overweight`，財報後將價格看法由 **$380** 進一步調高至 **$450**；同日 Jefferies、Piper Sandler 亦將價格看法調高至 **$450**（維持 `Buy`），Morgan Stanley 維持 `Buy`、看法 **$410**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，台北時間 2026-11-19）。

### PDD｜拼多多（PDD）今天 +7.1%（盤前）：Q3 2026 削減行銷開支推升 Non-GAAP EPADS 至 3.14 美元大勝預期（雖營收持平遜預期）
- 事實：拼多多於美東 11/19 06:30（台北 19:30）公布 Q3 2026 財報，總營收人民幣 **1,083.4 億元**（年對年持平，遜於市場共識約 1,155 億～1,217 億元），主因交易服務營收年減 12% 至 485 億元；但因大幅壓低銷售與行銷支出，營業利益年增 **24.8%** 至人民幣 **312 億元**（調整後營業利益 **326.4 億元**）、Non-GAAP 淨利 **310 億元**、**Non-GAAP 稀釋每 ADS 盈餘 21.04 元（3.14 美元）**遠優於市場預估的 2.61–2.77 美元，帶動美股盤前大漲約 **7.1%–9%**（https://www.globenewswire.com/news-release/2026/11/19/3406398/0/en/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results.html ；https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，且 20:33 線上財報日曆仍將 PDD 列為「即將公布」。

### CRWD｜CrowdStrike（CRWD）今天 +6.4%（盤前）：受同業 PANW 財報驗證企業 AI 資安需求外溢帶動（無新進展）
- 事實：CRWD 預計 **12 月 1 日盤後**才公布 Q3 FY27 財報，11/18–19 本身無單獨公司公告或分析師新調整（找不到來源）；受同業 PANW Q1 FY27 財報優於預期與 45 億美元 AI 安全併購案外溢提振，資安族群盤前同步走強（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19）。
- 本站漏掉的：屬同業財報外溢效應，非 CRWD 個別公告。

### STX｜希捷科技（Seagate Technology，STX）今天 +6.0%（盤前）：受 Anthropic 創紀錄 IPO 點燃 AI 資料中心儲存與記憶體族群集體反彈（無新進展）
- 事實：11/19 美股盤前 STX 未見單獨公司公告（找不到獨立公司來源），隨 SKHY、SNDK、MU、WDC 等儲存／記憶體板塊受 Anthropic 今晚 22:30 以 83 美元那斯達克掛牌帶動同步大漲（https://news.cnyes.com/news/id/6667734 ；https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，台北時間 2026-11-19）。
- 本站漏掉的：STX、WDC、MU、SNDK、SKHY 今日盤前屬同一儲存／記憶體板塊集體反彈，非 STX 個別新消息。

### SKHY｜SK 海力士（SKHY）今天 +5.7%（盤前）：韓股正規盤收漲 +3.41%，Anthropic 1.5 兆美元 IPO 定價續推全球記憶體與儲存股盤前大漲（無新進展）
- 事實：SK 海力士（000660.KS）於 11/19 韓股正規盤收漲 **+3.41%** 至 **1,183,000 韓元**（https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ）；同日美股／海外追蹤盤前因 Anthropic 今晚以 83 美元掛牌（募資 813 億美元、估值 1.5 兆美元），記憶體與儲存股盤前大漲逾 **5%**（https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### WDC｜威騰電子（Western Digital，WDC）今天 +5.6%（盤前）：與 STX 等儲存族群同受 Anthropic IPO 提振盤前同步反彈（無新進展）
- 事實：11/19 美股盤前 WDC 未見單獨公司公告（找不到獨立公司來源），與 STX、SNDK、MU、SKHY 同步受 Anthropic 今晚掛牌激勵於盤前走高（https://news.cnyes.com/news/id/6667734 ；https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，台北時間 2026-11-19）。
- 本站漏掉的：與 STX 屬同一儲存板塊集體反彈，非 WDC 個別新消息。

### SNDK｜SanDisk（SNDK）今天 +5.4%（盤前）：今日為 1 拆 8 股票分割前最後交易日＋Anthropic IPO 帶動儲存股盤前集體反彈（無新進展）
- 事實：今日（美東 11/19）為 SanDisk（SNDK）**1 拆 8 股票分割**盤後分配股權前最後交易日（11/20 依拆股後價格交易，https://financefeeds.com/sandisk-sndk-stock-776-thursday-last-session-before-8-for-1-split-bull-831-bear-749/ ；https://www.fool.com/investing/2026/11/16/sandisk-splits-its-stock-8-for-1-on-nov-19-flash-memory-prices-still-matter-more-than-the-share-count/ ），並隨 Anthropic 今晚掛牌與儲存族群盤前同步大漲約 **4.9%–5.4%**（https://news.cnyes.com/news/id/6667734 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### MU｜美光（Micron，MU）今天 +5.0%（盤前）：Anthropic IPO 定價 83 美元今晚掛牌＋Q3 13F 機構增持＋AI 記憶體吃緊預期
- 同意本站（Yahoo 報導點出 AI 記憶體供給吃緊持續至 2028 年，https://finance.yahoo.com/technology/ai/articles/micron-ai-memory-crunch-getting-122152627.html?.tsrc=rss ）；本站漏掉的：
  - 事實：美光同時為 Anthropic 今晚 260 億美元同步私募的出資方（招股書列示擬認購約 10 億美元級別）暨記憶體供應夥伴，受 Anthropic IPO 定價高於區間帶動，美光盤前與 SKHY、SNDK 等族群同步反彈；此外最新 Q3 13F 揭露 Appaloosa 與 Altimeter 均於第三季增持美光部位（https://news.cnyes.com/news/id/6667734 ；https://financefeeds.com/micron-mu-stock-705-thursday-anthropic-ipo-priced-83-bull-746-bear-667/ ，台北時間 2026-11-19）。

### DELL｜戴爾（Dell，DELL）今天 +4.5%（盤前）：11/24 財報前隨 Anthropic IPO 與 AI 伺服器／硬體族群自前日回檔反彈（新增）
- 事實：DELL 將於美東 **11 月 24 日盤後**公布 Q3 FY27 財報，11/19 美股盤前無單獨公司新公告或當日評等調整（找不到獨立來源）；在昨日收跌約 2.9%（收 $313.38）後，今日盤前隨 Anthropic 創紀錄 IPO 點燃那指 100 期貨跳漲約 1.9%–2.3%，以及市場消化輝達 Q3 資料中心營收達 **1,076 億美元**驗證 AI 伺服器需求，同步反彈（https://finance.yahoo.com/m/107e5a2c-4fba-3df3-b2fd-5d1160e65516/dow-jones-futures-rise%2C.html?.tsrc=rss ；https://news.cnyes.com/news/id/6667734 ，台北時間 2026-11-19）。
- 本站漏掉的：屬大盤期貨與 AI 基建情緒帶動之板塊反彈，非 DELL 個別新公告。

### MRVL｜邁威爾（Marvell，MRVL）今天 +4.5%（盤前）：消化 1,150 億美元併購 Lumentum 降評壓力後，隨客製化 AI 晶片與光通訊族群反彈（新增）
- 事實：MRVL 日前宣布擬以 **1,150 億美元**全股票收購光通訊廠 **Lumentum (LITE)** 引發股本稀釋約 50% 疑慮，遭美銀降至 `Neutral`（看法 $400→$225）及 TD Cowen 降至 `Hold`（看法 $350→$175）（https://finance.biggo.com/news/11363615-75b3-4fde-a7f6-069c21673c8c ，台北時間 2026-11-19）；今日盤前未見新公司公告（找不到獨立來源），隨 Anthropic 創紀錄 IPO 突顯多晶片與高速互連長期需求，以及半導體族群結束五連跌同步反彈（https://www.tradingview.com/news/stocktwits:6243efa9f094b:0-nvda-intc-stocks-ease-post-5-day-rout-after-meeting-xi-jinping-trump-says-nvidia-blackwell-chips-could-reach-china-within-2-3-years/ ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### INTC｜英特爾（Intel，INTC）今天 +4.5%（盤前）：隨晶片族群結束五連跌反彈，市場消化川普談 Blackwell 輸陸可能性與 18A-P 首家外部客戶進展（無新進展）
- 事實：半導體連跌五日後，隨 Anthropic IPO 定價高於區間帶動那指期貨漲約 1.9%–2.3% 與晶片股反彈，加上川普於深圳稱 2–3 年後不排除放行 Blackwell 晶片輸陸及英特爾 Austin 峰會宣布 18A-P 首位外部客戶與微軟採用 EMIB，推動 INTC 盤前漲約 **4.5%–4.9%**（https://www.tradingview.com/news/stocktwits:6243efa9f094b:0-nvda-intc-stocks-ease-post-5-day-rout-after-meeting-xi-jinping-trump-says-nvidia-blackwell-chips-could-reach-china-within-2-3-years/ ；https://news.cnyes.com/news/id/6667734 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### LRCX｜科林研發（Lam Research，LRCX）今天 +4.4%（盤前）：受 Anthropic 創紀錄 IPO 提振晶圓製造設備需求情緒，隨費半設備族群同步反彈（新增）
- 事實：11/19 美股盤前 LRCX 未見單獨公司公告或新評等調整（找不到獨立公司來源），隨 Anthropic 募資 813 億美元今晚掛牌、那指 100 期貨上漲約 1.9%–2.1%，以及市場視晶圓設備龍頭為 AI 擴產「不管哪家晶片贏都受惠」的受惠鏈，與 AMAT、KLAC、ASML 盤前同步走高（https://finance.yahoo.com/m/107e5a2c-4fba-3df3-b2fd-5d1160e65516/dow-jones-futures-rise%2C.html?.tsrc=rss ；https://news.cnyes.com/news/id/6667734 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

---

### AN｜AN-1：最近 3 小時內（台北 17:52–20:52）出現 PANW 財報後多家券商調高看法與 Seeking Alpha Quant 降評 NVDA；保留其餘近期已核對調評
- 事實（最近 3 小時新增／更新）：
  - **PANW（美東 11/19 盤前報導）**：財報公布後，**KeyBanc** 分析師 Eric Heath 維持 `Overweight` 並將價格看法由 $380 調高至 **$450**；**Jefferies** 與 **Piper Sandler** 維持 `Buy`、看法均調高至 **$450**；**Morgan Stanley** 維持 `Buy`、看法 **$410**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，台北時間 2026-11-19）。
  - **NVDA（美東 11/19 報導）**：Seeking Alpha Quant 量化模型因動能評分降至 D+，將 NVDA 量化評等由 `Strong Buy` 下調至 `Hold`（無獨立華爾街賣方投行於近 3 小時新增降評）。
- 事實（近期已核對報告，依任務單保持英文評等原文，無新進展）：
  1. **高盛 Goldman Sachs（AVGO，美東 11/19 01:26／台北 14:26 報導）**：分析師 James Schneider 維持 **AVGO** `Buy` 評等，因同業倍數壓縮由 30 倍下修至 25 倍，將價格看法由 $540 調降至 **$460**（https://www.tokenpost.com/news/business/61151 ）。
  2. **Rothschild & Co Redburn（AVGO，11/13 報告）**：將 **AVGO** 由 `Buy` 調降至 `Neutral`，價格看法由 $595 調降至 **$398**（https://fr.tradingview.com/news/seekingalpha:f4cc47e04094b:0-broadcom-in-focus-as-rothschild-downgrades-to-neutral-but-flags-potential-upside/ ；https://www.tikr.com/blog/is-rothschild-co-redburn-wrong-to-give-up-on-broadcom-wall-street-still-sees-533 ）。
  3. **美銀／TD Cowen（MRVL，併購 Lumentum 案後）**：Bank of America 將 **MRVL** 由 `Buy` 降至 `Neutral`（看法 $400→$225）；TD Cowen 將 **MRVL** 由 `Buy` 降至 `Hold`（看法 $350→$175）（https://finance.biggo.com/news/11363615-75b3-4fde-a7f6-069c21673c8c ）。
  4. **摩根大通 JPMorgan（HCA，11/18 報告）**：維持 **HCA** `Neutral` 評等，將價格看法由 $425 調高至 **$475**（https://www.tradingview.com/news/tradingview:9eb3a7caf755c:0-jp-morgan-maintains-hca-healthcare-at-neutral-raises-price-target-to-475-from-425/ ）。
  5. **摩根士丹利（台積電 2330，11/19 報告）**：維持 `Overweight` 評等與估值看法 **3,088 元**，2026–2028 年 EPS 估 **112.10／148.64／189.81 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ）。
  6. **輝達（NVDA）與近期機構報告**：Summit Insights 降至 `Hold`（https://www.tikr.com/fr/blog/is-summit-insights-wrong-to-give-up-on-nvidia-wall-street-still-sees-251 ）；HSBC Frank Lee 降至 `Hold` 看法 $365→$170（https://www.tradingview.com/news/binance_news:d94dcaa1f094b:0-hsbc-downgrades-nvidia-says-stock-may-struggle-until-new-ceo-is-named/ ）；Evercore ISI `Outperform`→`In-Line` 看法 $186、Bernstein $400→$200、Baird `Outperform`→`Neutral`（https://www.tradingview.com/news/benzinga:3bce7f47b094b:0-nvidia-gets-10-bank-downgrades-after-huang-exit-what-to-expect-ahead-of-q3-results/ ）；Moody's 維持 `Aa1` 展望降至 `Stable`（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ）；Piper Sandler 調升 MDT 至 `Overweight` 看法 $120（https://www.tradingview.com/news/tradingview:5b080eae6cc49:0-piper-sandler-upgrades-medtronic-to-overweight-from-neutral-raises-price-target-to-120-from-85/ ）。

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）刊登聯邦公報生效，條文罕見註明由財政部與國安會主導起草（20:52 補實聯邦公報單頁原文網址與跨部會細節）
- 事實：BIS 暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢至 2027-01-19），增訂 § 744.24 限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則，條文並罕見註明「由財政部與國安會（NSC）主導及指示撰寫」（https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors ；https://public-inspection.federalregister.gov/2026-23529.pdf ；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ；https://www.milbank.com/en/news/bis-issues-new-rule-restricting-remote-access-to-advanced-chips.html ）。台積電回應正評估新規並將嚴格遵循適用法令、強化最終用途審查。
- 事實：白宮於 11 月中旬馬尼拉 Quad 領袖峰會聯合澳、印、日發表聲明，鎖定關鍵礦產／半導體供應鏈安全與可信賴超級智慧技術生態；同日聯邦公報亦列載 CMS CRUSH 反詐欺草案（`2026-23461`，https://public-inspection.federalregister.gov/2026-23461.pdf ）。

### POL-2｜美國財政部 FinCEN 強化 CDD 提案、9 月 TIC 淨流入 2,610 億美元、OFAC 制裁與 USTR 談話（無新進展）
- 事實：財政部 FinCEN 發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，https://home.treasury.gov/news/press-releases/sb0691 ）；9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ）；OFAC 制裁真主黨與聖城軍金流（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 大使 Greer 11/18 於 RBA 年會重申美國優先貿易（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）。

---

### TW-1｜11/19 台股收跌 1,768 點（38,426.89 點）、櫃買暴跌 7.22%、1,028 檔明納限空令 2.0、世界／台化／萬泰科爆 1.29 億違約交割；新台幣收升 32.942 元（無新進展）
- 事實（11/19 台股收盤、三大法人與違約交割）：加權指數盤中下探 38,259.7 點（跌 1,935.21 點），終場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，失守年線 39,368 點）**，成交值 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ）；櫃買指數收跌 **-7.22%（-22.22 點）至 285.33 點**。電子權值股收盤：**台積電 2,100 元（-3.45%）**、**聯發科 3,720 元（-5.58%）**、**鴻海 220.5 元（-0.23%）**、**日月光投控 504 元（-8.03%）**、**緯穎 1,410 元（跌逾 4%）**（https://www.moneyweekly.com.tw/ArticleData/Info/Article/212266 ）。三大法人合計賣超 **461.03 億元**（**外資 -243.12 億元**、**投信 +15.13 億元**、**自營商 -233.03 億元**，其中自營商避險部位 **-214.40 億**，https://www.cna.com.tw/news/afe/202611190200.aspx ）；期貨三大法人合計淨空單 **-8,883 口**（外資 **-99,219 口**、投信 **+91,791 口**、自營商 **-1,455 口**）。盤後證交所與櫃買中心再通報 3 檔違約交割合計 **1.29 億元**：包含上市**台化（1326）4,172.8 萬元**，以及上櫃**世界先進（5347）與萬泰科（6190）**（https://stock.ltn.com.tw/article/m7hjf9c9axqq ；https://inews.setn.com/news/1941815 ）。
- 事實（11/19 新台幣收盤價）：台北外匯市場開 32.960 元，盤中低見 **33.040 元**，16:00 翻升收 **32.942 元（升值 0.5 分）**；台北外匯經紀成交 **22.63 億美元**、台北及元太兩大外匯市場總成交 **32.82 億美元**（https://www.cna.com.tw/news/afe/202611190296.aspx ；https://money.udn.com/money/story/12509/9889341 ）。
- 事實（金管會 11/20 限空令 2.0）：（1）今日收盤跌幅達 **3.5%** 以上之上市櫃與 TDR（共計 **1,028 檔**），次一交易日禁止低於前收融券及借券放空；（2）每日盤中借券放空委託數量上限由前 30 日均量 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190182.aspx ）。

### TW-2｜台積電高層（張曉強）親赴輝達固鏈＋Vera Rubin Q3 量產出貨；正式公告 5 億美元入股 Anthropic（無新進展）
- 事實：輝達財報會議與台灣媒體報導揭露，輝達人事變動後由台積電資深副總暨副共同營運長**張曉強**親赴輝達美國總部穩固長期供應與擴產承諾，確認 Rubin 系列與 CoWoS 先進封裝按原計畫進行，且新一代 **Vera Rubin NVL72** 與 **Vera CPU** 已於 2026 年 Q3 進入量產出貨；台積電另表示正評估美商務部 11/19 生效的遠端算力管制新規（https://www.cna.com.tw/news/afe/202611190254.aspx ；前輪確認）。
- 事實（其餘台鏈公告，無新進展）：台積電 11/19 正式公告透過 TSMC Partners 以 **每股 83 美元**取得 Anthropic 普通股 **6,024,096 股**（約 **5 億美元**，https://www.cna.com.tw/news/afe/202611190254.aspx ）；日月光投控旗下台灣福雷電子高雄仁武 J 坵塊新廠 11/19 動土計畫投資 **2,489 億元**（https://www.cna.com.tw/news/afe/202611190122.aspx ）；廣達田納西廠租約 1,490.8 萬美元（https://news.cnyes.com/news/id/6666244 ）；海龍 2A 綠電轉售台積電（https://www.cna.com.tw/news/afe/202611190102.aspx ）；鴻海 72.4 億日圓收購 Sony 車載相機事業（https://www.ctee.com.tw/news/20261119700316-439901 ）；熊本清晨 M5.7 地震尚無 JASM 重大停工回報。
- 傳聞（無新進展）：《工商時報》與外媒引述業界指出，台積電依客戶（含 ASIC 三雄）資產負債表設 AI 信用額度、超額須預付現金，帶動部分台鏈以海外可轉債（ECB）或聯貸籌資，尚未獲台積電正式公告證實（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ）。

### TW-3｜SK 海力士 11/19 收漲 +3.41%、蘋果洽談三星多年期 DRAM 長約；亞股日韓印收紅、陸港台收黑（無新進展）
- 事實：《MoneyToday》11/19 報導 SK 海力士（000660.KS）收漲 **+3.41% 至 1,183,000 韓元**，與三星電子連兩日收高（https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ）；《The Korea Herald》11/19 報稱蘋果正進入與三星電子洽談 4 至 5 年期 DRAM 供應協議最後階段（https://www.koreaherald.com/article/10942672 ）。11/19 亞股收盤：**日經 225 +0.71%（59,444.21）**、**KOSPI +1.39%（5,137.89）**、**印度 Nifty 50 +0.91%（25,458.75）**；**上證 -0.28%（3,577.62）**、**恆生 -1.95%（22,841.62）**、**台股加權 -4.40%（38,426.89）**。東京威力科創（TEL）與愛德萬測試近期受 AI 晶片情緒牽動劇烈震盪，無獨立新廠務公告（https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ）。

---

### EARN-WMT｜沃爾瑪（WMT）已於 11/19 20:00（美東 07:00）公布 Q3 FY27 財報：營收 1,888 億美元、調整後 EPS 0.65 美元雙優於預期，並上調全年展望（20:52 補實 StockTitan 8-K 與 BigGo 單篇原文網址）
- 事實：沃爾瑪於 **美東 2026-11-19 07:00（台北 20:00）**發布 Q3 FY27 財報（電話會議訂美東 08:00／台北 21:00）：
  - **營收**：**1,888 億美元**，年增 **5.2%**（常數匯率 +4.5%），優於市場共識約 **1,872.5 億～1,873.8 億美元**；其中美國同店銷售（不含燃油）成長 **2.9%**；全球電商銷售年增 **17%**（美國電商 +23%）；全球廣告業務年增 **25%**（美國廣告 +37%）。
  - **獲利**：營業利益年增 **16.0%** 至 **77.7 億美元**；**調整後 EPS 0.65 美元**（優於市場預期 0.64 美元與上季財測 0.62–0.64 美元），GAAP EPS 0.62 美元。
  - **全年 FY27 展望上調**：常數匯率淨銷售成長上調至 **4.9%–5.2%**（原 4.0%–5.0%）、調整後營業利益成長上調至 **8.0%–8.6%**（原 7.0%–8.5%）、調整後 EPS 上調至 **$2.84–$2.89**（原 $2.80–$2.87）；受股價位處 52 週高檔影響，盤前小幅回吐約 0.7%–1.6%（https://www.stocktitan.net/sec-filings/WMT/8-k-walmart-inc-reports-material-event-0371aee37dfe.html ；https://finance.biggo.com/news/462fcfe0-7cf8-4cdf-b251-332c42101b59 ；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，台北時間 2026-11-19）。

### EARN-PDD｜拼多多（PDD）11/19 19:30 公布 Q3 2026 財報：營收 1,083.4 億遜預期但 Non-GAAP EPADS 3.14 美元大勝，盤前漲約 7.1%–9%（20:52 補實 GlobeNewswire 原文與最新盤前 +7.1%）
- 事實：拼多多於美東 11/19 06:30（台北 19:30）公布 Q3 2026 營收人民幣 **1,083.4 億元**（年對年持平，遜於市場共識約 1,155 億～1,217 億元），主因交易服務營收年減 12% 至 485 億元；但受惠削減銷售與行銷支出，營業利益年增 24.8% 至 **312 億元**（調整後營業利益 **326.4 億元**）、Non-GAAP 淨利 **310 億元**、**Non-GAAP 稀釋每 ADS 盈餘 21.04 元（3.14 美元）**大幅擊敗共識 2.61–2.77 美元，截至 20:41 美股盤前上漲 **7.1%**（早段一度達 8%–9%）（https://www.globenewswire.com/news-release/2026/11/19/3406398/0/en/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results.html ；https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ，台北時間 2026-11-19）。

### EARN-BABA｜阿里巴巴（BABA）11/19 公布 Q2 FY27 財報：營收 2,715.19 億（+10% YoY）優於預期，但 FCF 淨流出 344.72 億且庫藏股縮水致盤前走弱（無新進展）
- 事實：阿里巴巴 Q2 FY27 總營收人民幣 **2,715.19 億元**（約 405.0 億美元，+10% YoY）優於預期 2,698.49 億元，AI 雲外部收入年增 67%；惟 Non-GAAP 淨利 **199.09 億元**低於預期 265.7 億元、資本開支激增 60% 至 504.77 億元致 **FCF 淨流出 344.72 億元**，且當季美股股票回購縮減，ADR 盤前下跌約 0.1%–2%（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ；https://investingnews.com/alibaba-group-announces-september-quarter-2026-results-and-interim-results-for-the-six-months-ended-september-30-2026/ ，台北時間 2026-11-19）。

### EARN-NTES｜網易（NTES）11/19 公布 Q3 2026 財報：營收 279 億元（-1.8% YoY）與獲利雙遜預期，盤前跌逾 3.5%–5%（無新進展）
- 事實：網易 Q3 2026 淨營收人民幣 **279 億元**（42 億美元，-1.8% YoY，遜於共識約 295 億～303 億元），遊戲收入 229 億元（-1.7% YoY），Non-GAAP 淨利 **92 億元**、Non-GAAP 每 ADS 盈餘 **2.13 美元**（¥14.21，遜於共識 2.43–2.49 美元），盤前跌逾 **3.5%–5%**（https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ，台北時間 2026-11-19）。

### EARN-WSM / INTU / ROST / GAP / KEYS｜今日（11/19）美東盤前待公布（WSM）與盤後財報預期（20:52 新增 KEYS）
- 事實：
  - **WSM（美東 11/19 盤前／10:00 ET、台北 23:00 電話會議，截至 20:52 尚未見官方財報新聞稿發布）**：共識營收 **19.8 億～20.0 億美元**、EPS **2.17–2.21 美元**（https://www.tradingview.com/news/tradingview:5796c7c550438:0-wsm-q3-26-earnings-eps-estimate-is-2-19-usd/ ）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（原財測 2.44–2.48 美元），隱含波動 ±8.9%–10.5%（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  - **ROST（盤後／台北 11/20 05:00）**：共識營收 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）。
  - **KEYS（Keysight，盤後／台北 11/20 05:00）**：市場共識營收 **19.5 億美元**、EPS **3.37–3.38 美元**（公司先前 Q4 財測為營收 19.3 億～19.5 億美元、Non-GAAP EPS 3.34–3.40 美元，https://www.tradingview.com/news/tradingview:dd00407af5aef:0-keys-q4-26-earnings-eps-estimate-is-3-37-usd/ ）。

### EARN-BSP / HPE / ZM / A / BILI / BURL / DKS / ADI / MDT / BBY / DLTR / DELL / HPQ / ADSK / WDAY / DE｜11/20–11/25 未來 10 天財報（20:52 補齊站上日曆列載之 BSP、A、DLTR）
- 事實：
  - **11/20 盤前（台北 20:00–21:00）**：**BSP（Bending Spoons）** 市場共識營收 **7.41 億～7.46 億美元**（公司前季財測 7.33 億～7.45 億）、EPS **0.31–0.32 美元**（https://www.thestreet.com/investors/berkshire-hathaway-bending-spoons ，或見 TipRanks／StockTitan；註：本站日曆列 EPS 預期 0.25 美元）。
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（公司財測 1.20–1.30；波動 ±9.7%，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ）；**ZM** Zacks 共識營收 **12.8 億美元**、EPS **1.49 美元**（https://www.zacks.com/stock/news/3030700/zoom-communications-zm-falls-more-steeply-than-broader-market-what-investors-need-to-know ）；**A（Agilent）** 共識營收 **19.9 億～20.3 億美元**、EPS 約 **1.73 美元**（本站日曆列 1.72 美元）。
  - **11/24 盤前（台北 20:00–21:00）**：**BILI** 共識營收 **12.3 億美元**、EPS **0.23–0.27 美元**；**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**（https://www.tradingview.com/news/tradingview:6917007d5e261:0-burl-q3-26-earnings-revenue-estimate-is-2-97b-usd/ ）；**DKS** 營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ）；**ADI** FactSet 共識營收 **43.2 億美元**、EPS **3.88 美元**（https://www.tradingview.com/news/tradingview:4441db86105da:0-adi-q4-26-earnings-revenue-estimate-is-4-32b-usd/ ）；**MDT** FactSet 共識營收 **94.8 億美元**、EPS **1.33 美元**（https://es.tradingview.com/news/tradingview:dcc2d0d8b8c99:0-mdt-q2-26-earnings-revenue-estimate-is-9-48b-usd/ ）；**BBY** Zacks 共識營收 **98.8 億美元**、EPS **1.48 美元**（https://www.zacks.com/stock/news/3031155/best-buy-bby-reports-next-week-wall-street-expects-earnings-growth ）；**DLTR（Dollar Tree）** 共識營收 **50.4 億美元**、EPS **0.88–0.91 美元**（本站日曆列 0.88 美元）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億～502.0 億美元**、EPS **6.41–6.71 美元**（公司指引營收 490 億、調整後 EPS 6.50 美元；波動 ±14.85%，https://www.tradingview.com/news/tradingview:e525c4bdcb809:0-dell-q3-26-earnings-revenue-estimate-is-49-25b-usd/ ）；**WDAY** 營收 **26.9 億美元**、Non-GAAP EPS **2.74–2.75 美元**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ）；**HPQ** FactSet 共識營收 **154.3 億～155.8 億美元**、EPS **0.75–0.76 美元**（https://in.tradingview.com/news/tradingview:2627939d5b773:0-hpq-q4-26-earnings-revenue-estimate-is-15-43b-usd/ ）；**ADSK** 共識營收 **21.3 億美元**、Non-GAAP EPS **3.07 美元**（公司前季財測 3.04–3.09 美元，https://www.marketbeat.com/instant-alerts/upcoming-autodesk-adsk-set-to-announce-quarterly-earnings-on-tuesday-2026-11-17/ ）。
  - **11/25 盤前（台北 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ）。

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（除非明確預告 1 月再升 1 碼）（無新進展）
- 事實：Waller 受訪指出聯準會可能需要「shock」壓抑通膨預期避免 3% 通膨固著，12/8–9 會議應考慮一次升息 50 基點，除非明確前瞻指引 12 月與 1 月連續各升 1 碼（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ；https://www.morningstar.com/news/marketwatch/20261118119/feds-waller-says-interest-rate-hikes-may-be-needed-to-shock-inflation-out-of-the-system ；https://www.aa.com.tr/en/economy/fed-governor-favors-half-point-rate-hike-in-december-unless-fed-signals-january-increase/4129382 ）。

### FED-3｜聯準會理事 Michael S. Barr（偏升息）、紐約聯準銀行總裁 John Williams（反對一次升息 2 碼）；稍後 Goolsbee、Barkin 談話與貼現率閉門會議（20:52 補充 Barkin 行程）
- 事實：Barr 11/18 在紐約聯準銀行演說指出通膨仍過高、適合進一步升息並示警 AI 代理資金調撥風險（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ）；Williams 於 Axios BFD 峰會指出不需戲劇性行動、反對一次大幅升息 2 碼（https://www.aa.com.tr/en/economy/fed-governor-favors-half-point-rate-hike-in-december-unless-fed-signals-january-increase/4129382 ；https://www.idnfinancials.com/news/71905/does-the-fed-still-need-to-raise-interest-rates-john-williams-answer ）。芝加哥聯準銀行總裁 **Goolsbee** 將於 **美東 11/19 12:30（台北 11/20 01:30）**於印第安納經濟俱樂部座談（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；里奇蒙聯準銀行總裁 **Thomas Barkin** 將於 **美東 11/19 15:00（台北 11/20 04:00）**參加維州參議院財政委員會年會經濟座談；聯準會理事會於 **美東 11/19 15:00（台北 11/20 04:00）**召開閉門貼現率會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼約 86%–97%、升息 2 碼約 3%–10%（無新進展）
- 事實：截至 11/19 各家引述 CME FedWatch 數據顯示，12/8–9 FOMC 升息 1 碼機率落在 **86%–97%**（多數報導落在 90% 上下），少數押注 2 碼（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）。結構上係因住房通膨降溫拉低權重較大的 CPI，而醫療／金融／科技服務權重在 PCE 較高且黏著（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ）。

### TASK-B2｜11/19 台股收跌 1,768.02 點收 38,426.89 點（櫃買 -7.22%）、外資現貨賣超 243.12 億、三大法人台指期淨空單 -8,883 口、新台幣收升 32.942 元（無新進展）
- 事實：集中市場收 **38,426.89 點（-1,768.02 點 / -4.40%）**，成交 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ）；櫃買收 **285.33 點（-7.22%）**。外資現貨賣超 **243.12 億元**、投信買超 **15.13 億元**、自營商賣超 **233.03 億元**，三大法人合計賣超 **461.03 億元**（https://www.cna.com.tw/news/afe/202611190200.aspx ）；期交所三大法人台指期合計淨空單 **-8,883 口**（外資 -99,219、投信 +91,791、自營商 -1,455）；新台幣 16:00 收 **32.942 元（升值 0.5 分）**（https://www.cna.com.tw/news/afe/202611190296.aspx ）；金管會 11/20 起實施 1,028 檔 3.5% 限空令 2.0（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；更新美東 07:45（台北 20:41）夥伴盤前動向（20:52 補實直連網址與 `/api/gemini_ask` 即時盤前報價）
- 事實：Anthropic（**ANT**）定價 **83.00 美元**（9.8 億股、公開募資 **813.1 億美元**＋260 億美元同步私募合計約 1,073 億美元、完全稀釋估值約 **1.5 兆美元**），將於 **美東 11/19 09:30（台北 22:30）**掛牌，截至台北 20:52 尚未開盤，首日開盤／收盤價與成交量須待明早 05:00 收盤後確認（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ）。
- 事實：11/19 美東盤前那指 100 期貨上漲約 **1.9%–2.1%**，新雲端 **CoreWeave (CRWV) +4%、Nebius (NBIS) 近 +5%、IREN +5.3%** 同步反彈（https://www.tradingview.com/news/gurufocus:3923bd684094b:0-coreweave-nebius-and-iren-stocks-rise-ahead-of-anthropic-debut/ ）；出資與晶片／儲存／硬體夥伴盤前（依 20:41 `/api/gemini_ask`）：**STX +6.0%、SKHY +5.7%、WDC +5.6%、SNDK +5.4%、MU +5.0%、DELL +4.5%、MRVL +4.5%、INTC +4.5%、LRCX +4.4%**（https://news.cnyes.com/news/id/6667734 ；https://finance.yahoo.com/m/107e5a2c-4fba-3df3-b2fd-5d1160e65516/dow-jones-futures-rise%2C.html?.tsrc=rss ）。

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字（無新進展）
- 事實：ECB Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（採 LSEG 10/26 共識），表層口徑為「資本支出超過營運現金流」，未扣未起租的表外租賃；逾 4 兆美元表外承諾另依 ASC 842 揭露於圖表 A 與註腳 6（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。四巨頭截至 2026-09-30 實際數字：Meta **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）、Alphabet **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）、Amazon **TTM -$42.36B**（單季隱含 -$33.51B，https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）、Microsoft **+$18.6B**（含新起租融資租賃仍約 +$12.8B，前輪已讀 https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### TASK-B5｜沃爾瑪（WMT）、阿里巴巴（BABA）、拼多多（PDD）11/19 財報全部揭曉（20:52 補實可點開之 StockTitan／BigGo／GlobeNewswire 原文網址）
- 事實（沃爾瑪 WMT，Q3 FY27，**已於美東 07:00／台北 20:00 公布**）：營收 **1,888 億美元（+5.2% YoY）** 優於預期約 1,872.5 億～1,873.8 億；**調整後 EPS 0.65 美元**（GAAP 0.62 美元）優於預期 0.64 美元；上調 FY27 全年常數匯率淨銷售成長至 **4.9%–5.2%**、調整後 EPS 至 **$2.84–$2.89**（原 $2.80–$2.87）。CEO John Furner 原話：`"We delivered strong results, growing our core business and gaining market share. The strength of our omnichannel model gives us room to do even more."`（另有先前延續至年底的壓低售價與關稅退稅再投資承諾，https://www.stocktitan.net/sec-filings/WMT/8-k-walmart-inc-reports-material-event-0371aee37dfe.html ；https://finance.biggo.com/news/462fcfe0-7cf8-4cdf-b251-332c42101b59 ）。
- 事實（拼多多 PDD，Q3 2026，**已於 19:30 公布**）：營收人民幣 **1,083.4 億元**（持平，遜於預估 ~1,155 億～1,217 億），**Non-GAAP 每 ADS 盈餘 21.04 元（3.14 美元）**大幅優於預估 2.61–2.77 美元，截至 20:41 盤前漲 **+7.1%**；聯席 CEO 陳磊對貿易與監管原話：`"As our global business adapts to an evolving trade and regulatory environment, we remain committed to deepening our supply chain investments."`（https://www.globenewswire.com/news-release/2026/11/19/3406398/0/en/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results.html ；https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ）。
- 事實（阿里巴巴 BABA，Q2 FY27，**已於 18:18 前公布**）：營收人民幣 **2,715.19 億元**（+10% YoY，勝於預期 2,698.49 億），但 **Non-GAAP 淨利 199.09 億元遜於預期 265.7 億**、FCF 淨流出 **344.72 億元**、當季美股回購縮水，ADR 盤前小跌約 0.1%–2%；CFO 徐宏原話：`「隨著AI商業化不斷深入，我們會繼續審慎根據市場情況投入AI建設，注重提升資本回報率，並致力於盡早實現自由現金流轉正。」`（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ；https://investingnews.com/alibaba-group-announces-september-quarter-2026-results-and-interim-results-for-the-six-months-ended-september-30-2026/ ）。

---

### CALL｜法說會與財報原話重點（過去 24 小時；20:52 補實 WMT StockTitan／BigGo 原文網址，其餘無新進展）

### CALL-WMT｜沃爾瑪（WMT）Q3 FY27：營收與電商廣告雙雙加速、上調全年財測至 EPS $2.84–$2.89
- 原話（CEO John Furner）：`"We delivered strong results, growing our core business and gaining market share. The strength of our omnichannel model gives us room to do even more."`（電話會議訂於美東 08:00／台北 21:00 舉行，https://www.stocktitan.net/sec-filings/WMT/8-k-walmart-inc-reports-material-event-0371aee37dfe.html ；https://finance.biggo.com/news/462fcfe0-7cf8-4cdf-b251-332c42101b59 ，台北 2026-11-19）。

### CALL-BABA｜阿里巴巴（BABA）Q2 FY27：AI 雲外部收入年增 67%、全端 AI 推升商業化（無新進展）
- 原話（CEO Eddie Wu）：`"Our full-stack AI capabilities continue to improve commercialization and delivered a strong quarter. Growth in Alibaba Cloud's recurring revenue from external customers was 67%, which drove an acceleration of overall cloud revenue growth with significantly improving profitability."`（https://investingnews.com/alibaba-group-announces-september-quarter-2026-results-and-interim-results-for-the-six-months-ended-september-30-2026/ ）。

### CALL-PDD｜拼多多（PDD）Q3 2026：營收持平下持續投資供應鏈以因應貿易與監管變化（無新進展）
- 原話（Co-CEO Lei Chen）：`"As our global business adapts to an evolving trade and regulatory environment, we remain committed to deepening our supply chain investments."`（https://www.globenewswire.com/news-release/2026/11/19/3406398/0/en/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results.html ）。

### CALL-NTES｜網易（NTES）Q3 2026：遊戲營收微降但毛利增 4.8%、持續推進跨平台新遊研發（無新進展）
- 原話（CEO William Ding）：`"While we continue to evolve our established titles with content and gameplay mechanics that appeal to a broader range of players, we are also steadily advancing our titles in development across genres, platforms and markets."`（https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ）。

### CALL-PANW｜Palo Alto Networks（PANW）Q1 FY27 法說會：NGS ARR 年增 66%、斥資 45 億美元併購 Applied Compute（無新進展）
- 原話（CEO Nikesh Arora）：`"As AI reshapes the threat landscape, we must continually evolve to protect our customers and enable them to adopt AI securely. To that end, we are pleased to announce our intent to acquire Applied Compute, which will allow us to deliver secure open weight models to our customers and accelerate the adoption of enterprise AI."`（https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ）。

### CALL-P｜Everpure（NYSE: P，原 Pure Storage）Q3 FY27 法說會：營收年增 51%、連三季上調全年財測（無新進展）
- 原話（CFO Tarek Robbiati）：`"Our results reflect the strength of our diversified portfolio, with our core and core AI offerings complemented by increasing contributions from our new businesses. We are raising full-year guidance for the third consecutive quarter and reiterating our strong preliminary FY28 outlook, underscoring confidence in our durable business model and broad-based momentum."`（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ）。

### CALL-NVDA｜輝達（NVDA）Q3 FY27 法說會：營收 1,158 億美元、下季財測排除中國（無新進展）
- 原話：`"Our momentum is real... Customers, suppliers, and partners are 100% behind us. We’ve got this."`（https://www.cnbc.com/2026/11/18/nvidia-stock-earnings.html ）。

### CALL-LOW / TGT / TJX｜美國零售 Q3 法說會（無新進展）
- LOW 原話：`"We delivered strong top-line growth of over 9%, led by our sixth consecutive quarter of positive comparable sales, with continued momentum in Pro, online and home services."`（https://corporate.lowes.com/sites/lowes-corp/files/2026-11/q3-2026-press-release-v1.pdf ）。
- TGT 原話：`"Our third-quarter results reflect continued progress against our strategic priorities, centered on serving busy families with our signature blend of style, design and value."`（https://www.prnewswire.com/news-releases/target-corporation-reports-third-quarter-earnings-302942872.html ）。
- TJX 原話：`"Consolidated comparable sales grew 4%, driven by continued strength at HomeGoods, TJX Canada, and TJX International, and we saw improved sales at Marmaxx. Importantly, we expect further improvement at Marmaxx in the fourth quarter."`（https://mlq.ai/news/tjxs-comparable-sales-rise-4-above-its-plan-and-it-narrows-its-full-year-outlook-toward-the-top-of-the-range/ ）。

---

### NEXT-1｜事件：台股櫃買暴跌 7.22%＋1,028 檔納 3.5% 限空令 2.0＋世界／台化／萬泰科爆 1.29 億違約交割（無新進展）
- 推理：
  - 最先受影響的資產：明日（11/20）適用平盤下禁空之 **1,028 檔**跌幅 ≥3.5% 台股與 TDR、櫃買高融資中小型 AI 股、台指期避險部位，以及權證造市券商帳上部位。
  - 傳導路徑：自營商避險賣超 214.40 億元與盤後 1.29 億元違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ）迫使金管會將借券上限由 3% 砍至 1% 並啟用 3.5% 跌幅平盤下禁空（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）：
    - 美股：**TSM（ADR）、NVDA、AVGO、SOXX、EWT**。
    - 台股：**台積電 (2330)、聯發科 (2454)、世界 (5347)、台化 (1326)、元大金 (2885) 等券商金控**。
  - 大家還沒注意到的間接受害者：**承銷高價 AI 認購權證的台灣中小型券商自營部與證券融資授信部門**——當 1,028 檔個股平盤下放空受限、避險單轉擠入台指期（三大法人期貨淨空單 -8,883 口），中小型股若買盤縮手更容易「無量鎖跌停」，放大 T+2 違約交割由券商先代墊後的短期呆帳與資本適足率壓力。

### NEXT-2｜事件：WMT 財報驗證美國必需消費韌性 vs BABA 自由現金流大失血與 PDD 縮減行銷獲利分化（無新進展）
- 推理：
  - 最先受影響的資產：美國消費類股與零售 ETF（XLP、XRT、WMT、COST、TGT）、中概股（BABA、PDD、NTES、KWEB）、以及今晚 22:30 掛牌之 ANT 與新雲端／儲存族群（CRWV、NBIS、IREN、MU、STX、WDC）。
  - 傳導路徑：WMT 美國同店 +2.9%、電商 +23% 且上調全年指引，證明在川普關稅與高利率環境下，具備規模與「天天低價」能力的零售龍頭反而搶下市占；但 BABA 因 CapEx 增 60% 拖累 FCF 流出 344.72 億且縮減庫藏股而盤前承壓，PDD 靠控費換取獲利反彈，形成「現金流紀律＞單純營收成長」的定價邏輯：
    - 美股：**WMT、COST、BABA、PDD、CRWV**。
    - 台股：**廣達 (2382)、緯穎 (6669)、鴻海 (2317)、聚陽 (1477)／儒鴻 (1476)、台達電 (2308)**。
  - 大家還沒注意到的間接受益者：**受惠 WMT 美國電商 +23% 與廣告 +37% 的零售自動化／供應鏈軟體與高自由現金流資安軟體商（如 PANW）**——WMT 強勁的貨量與低價策略擠壓中小型品牌毛利（間接壓抑非龍頭供應商議價力），卻放大具備高現金流防禦墊的龍頭溢價。

### NEXT-3｜事件：荷莫茲海峽油輪觸雷＋Equinor 網攻＋歐盟延後甲烷規範 2 年 vs 美中俄《四點和平宣言》（20:52 補實歐盟甲烷妥協路徑）
- 推理：
  - 最先受影響的資產：歐洲 TTF 天然氣與挪威克朗（NOK）、布蘭特原油遠月曲線、美國／亞洲煉油股（VLO、PSX）、企業資安支出與歐盟印尼出口鏈。
  - 傳導路徑：荷莫茲東側水雷威脅（https://english.alarabiya.net/News/middle-east/2026/11/19/three-oil-tankers-catch-fire-after-hitting-naval-mines-east-of-strait-of-hormuz-report ）加上 IEA 警告繞道管線仍脆弱，同時 Equinor 與歐盟執委會接連遭網攻（https://therecord.media/norway-equinor-cyberattack-energy ），迫使歐盟 11/19 同意延後油氣煤進口商甲烷規範 2 年以換取能源供應緩衝（https://europeansting.com/2026/11/19/methane-deal-to-delay-reporting-and-monitoring-for-energy-importers/ ），與美中俄宣言增供成品油共同拉扯價格：
    - 美股：**XOM、VLO、PSX、PANW、CRWD**。
    - 台股：**台塑化 (6505)、長榮 (2603)、陽明 (2609)、安碁資訊 (6690)、東陽 (1319)**。
  - 大家還沒注意到的間接受害者：**高度依賴海運保險與歐洲天然氣電價的歐洲化工與高耗能製造業**——Equinor 雖未停產但凸顯歐洲關鍵能源基礎設施 IT 脆弱性，疊加波灣水雷推升遠期保費，壓抑歐洲工業復甦節奏。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 由 60% 降至 45%；線上總經表仍寫 60%）」
- 最強反方證據：BEA 官方新聞稿已證實 9 月核心 PCE 年增確為 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ），本站 `#econ`《PCE 物價》卡片亦已自行估算 10 月核心 PCE 年增約 **3.2%**、The Conference Board 預估 **3.3%**（https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026 ），今日 WMT Q3 強勁成長（美國同店 +2.9%）亦不見終端物價快速降溫跡象。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法發布年增率，這題將成為「無法判定」。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：維持落在 2.4%–3.0% 僅約 **30%**（比你的 45% 低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露多數美系一線雲端商 FCF 轉負且表外承諾逾 4 兆美元（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）；BABA 亦因 CapEx 增 60% 致 FCF 淨流出 344.72 億人民幣；台股櫃買暴跌 7.22% 與 1.29 億違約交割迫使金管會啟動 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；荷莫茲東側水雷與 Equinor 網攻同步推高尾端地緣風險。
- 另一種同樣說得通的解釋：今晚美股盤前那指期貨反彈 +1.9%–2.1%、VIX 由 24.6 回落至 **22.2–22.4**、WMT 繳出營收 1,888 億美元並上調全年展望、PDD 盤前 +7.1%～9%、日韓印股市收紅、新台幣收升 32.942 元且巴西參院通過財政緊縮案，顯示實體消費與部分科技風險胃納仍在，尚未演化成全面信用事件。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：維持「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你的 80% 低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：下緣有 11/18 EIA 汽油／原油庫存暴增（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ）、美中俄深圳宣言增供精煉油品與歐盟延後進口甲烷規範 2 年（WTI 今日約 **$83** 已逼近下緣）；上緣有荷莫茲東側油輪觸雷起火、IEA 警告繞道管線仍難防襲擊與沙國 PIF 總部遭碎片波及，呈現劇烈雙尾拉扯。
- 另一種同樣說得通的解釋：WTI 已在 $83 附近貼近 $80 下緣，只要下週 EIA 再出現大額累庫或三方增產細節落地，就可能跌破 $80；反之只要荷莫茲航道封鎖升級，油價就會突破 $100。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **未來 72 小時波灣與荷莫茲海峽安全動態**。
- 機率估計：維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」（無新進展）
- 最強反方證據：中央社引述《福斯新聞》指涉案女子同受中國情報與晶片走私調查（https://www.cna.com.tw/news/aopl/202611193003.aspx ），但台積電高層親赴輝達總部確認訂單與 Vera Rubin 量產不變。
- 另一種同樣說得通的解釋：個人行為與缺乏坦誠先觸發董事會 11/11 立即切割，而涉案對象本身牽連國安與走私調查，兩線交織且同一來源。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節）**與 **美方起訴／調查公告**。
- 機率估計：維持「單純私人治理、完全無涉中國晶片調查」**25%–30%**，「兩線交織」**70%–75%**。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（已對照 live 網站《金融穩定監測》與《美國公司債》分頁，無新進展）
- 事實：線上《金融穩定監測》（`#stability`）與《美國公司債》（`#cb_us`）雖有「AI 資本支出：靠自己賺還是靠借錢」及全市場投資級／BBB／CCC 利差，但沒有分出「表外未起租承諾」與「科技公司投資級長債利差」。ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q `Commitments and Contingencies / Uncommenced Leases` 追蹤，及 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜《金融穩定監測》缺少「非公開交易 BDC 限額贖回（Gating）與對沖基金主權債槓桿細節」獨立追蹤（已對照 live 分頁，無新進展）
- 事實：ECB 11/18 報告與 IMF／BIS 報告均聚焦非公開交易 BDC 限額贖回與避險基金主權債槓桿（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜本站完全沒有「關鍵基礎設施／雲端／能源網攻中斷（SEC Item 1.05）」警報卡片（20:52 補實 The Record 單篇網址）
- 事實：繼歐盟執委會遭 AI 工具 ARTEX 網攻離線 10 天後，歐洲最大能源供應商之一 Equinor 亦證實遭網攻導致企業 IT 與郵件系統中斷（https://therecord.media/norway-equinor-cyberattack-energy ）。目前本站《風險新聞》和《美股情報》均無 SEC 8-K Item 1.05 資安事件篩選。
- 推理：建議在「SEC 重大申報」新增 Item 1.05 資安揭露與關鍵能源／雲端基礎設施警報，免費資料源：CISA KEV（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）。

### BLIND-4｜「台股籌碼風向計」未自動加總「三大法人台指期合計淨口數」、且缺「每日違約交割金額」與「限空令燈號」（無新進展）
- 事實：11/19 爆出世界、台化（4,172.8 萬）、萬泰科合計 **1.29 億元**違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），金管會宣布 **11/20 起升級 3.5% 限空令**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。免費資料源：期交所「三大法人區分各期貨契約交易資訊」、證交所 `BFI82U` 與「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」且站上《IPO 觀察》本身漏列大型 IPO（20:52 對照 live `#econ`《IPO 觀察》）
- 推理：線上 `#econ`《IPO 觀察》連史上最大規模的 Anthropic IPO 都沒抓到、卻把 2025/10 已上市的 MPLT 放在首位，且沒有說明大型 IPO 納入 S&P 500、Nasdaq-100 時對被動 ETF 權重的排擠效應。建議補上指數快速納入（Fast Entry）規則與資金分流說明。

---

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets）— 掛牌日情緒兩極且嘲諷估值（無新進展）
- 討論內容與情緒：11/19 r/wallstreetbets 熱議 ANT 以 83 美元定價、募資 813 億美元於那斯達克掛牌，部分交易員賭開盤流動性衝高，但熱門回文嘲諷在 AI 情緒波動期以 1.5 兆美元估值上市「猶如在茅草村開藍寶堅尼經銷商」，憂心早期內部人解禁退場（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ）。

### SENT-2｜PANW 併購與總經升息壓力（r/wallstreetbets / r/stocks）— 肯定資安動能但對 Fed 鷹派謹慎（無新進展）
- 討論內容與情緒：關注 PANW 45 億美元併購與盤前漲逾 9%，同時憂慮 Fed 官員偏鷹言論壓抑估值（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-3｜台股 11/19 暴跌 1,768 點後「限空令 2.0」與違約交割（PTT 股板）— 熱議 1,028 檔禁空與追繳風險（無新進展）
- 討論內容與情緒：PTT 股板即時轉載金管會 1,028 檔 3.5% 平盤下禁空令與借券上限降至 1%（https://www.pttweb.cc/bbs/Stock/M.1795069467.A.DAC ），盤後熱議台化／世界／萬泰科 1.29 億違約交割、大摩對台積電 3,088 元報告（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ）與融資維持率追繳風險，情緒在護盤預期與無量鎖跌停恐懼間拉鋸（情緒，非事實）。

### SENT-4｜WMT 財報與 NVDA 後黃仁勳時代（r/wallstreetbets / r/stocks）— 盯緊 WMT 驗證消費韌性並調侃 NVDA 接班（無新進展）
- 討論內容與情緒：r/stocks 將今晚 WMT 財報視為美國底層與中產消費的終極健檢；r/wallstreetbets 則一面慶幸 NVDA 營收 1,158 億美元過關、一面拿代理 CEO Colette Kress 穿不穿皮衣與黃仁勳辭職調侃（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ）。

### SENT-5｜UNH／醫療保險（r/stocks）— CMS CRUSH 規則陰霾下情緒偏悲觀（無新進展）
- 討論內容與情緒：醫療保險與醫院股受 CMS CRUSH 追溯 2018 年審計草案衝擊，散戶情緒偏悲觀觀望（情緒，非事實；https://fr.tradingview.com/news/gurufocus:3ac55a47d094b:0-unitedhealth-stocks-fall-4-62-as-cms-proposes-wider-medicare-advantage-audits/ ）。

---

### SITE｜挑本站的錯（20:42 實測 live 網頁 `https://wallstreet-sentinel.pages.dev` 頁面產生 `11-19 20:33 台北` 全面更新）

### SITE-1｜同頁自相矛盾＋過時錯置：`每日總經情勢` 語音講 Anthropic 掛牌，同張卡片的《接下來 72 小時》與 `#econ`《IPO 觀察》卻列出 2025/10 已上市的 `MPLT` 並漏掉 Anthropic（ANT）
- 本站寫了什麼：線上 `#overview` `每日總經情勢`（`11-19 20:01`）語音稿寫「今晚看 Anthropic 掛牌」，《美股今天怎麼了》亦寫「11/19 美東 9:30 Anthropic 掛牌」；但同一張 `每日總經情勢` 卡片底下的《接下來 72 小時（台北時間）》卻寫 `11/19 22:30 ・上市・MapLight Therapeutics, Inc. 上市（估計）`，且 `#econ`《IPO 觀察》仍把 `MapLight Therapeutics, Inc. (MPLT)` 列為「即將定價（約 11-19）」，完全沒有 **Anthropic (ANT)**。
- 正確應該是什麼：MapLight Therapeutics（**MPLT**）早在 **2025 年 10 月 27 日**就已完成每股 17 美元 IPO（https://ir.maplightrx.com/news-releases/news-release-details/maplight-therapeutics-announces-pricing-initial-public-offering ）；2026 年 11 月 19 日美東 09:30（台北 22:30）掛牌的史上最大 IPO 是 **Anthropic (ANT)**（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ）。

### SITE-2｜已公布財報未消音：#econ《各公司最新財報重點》已抓到 WMT 8-K，但《接下來 72 小時》《重大事件倒數》《美股財報日曆》與 `macro_voice.json` 仍全部寫 WMT/BABA/PDD「尚未公布／今晚 21:00」
- 本站寫了什麼：截至頁面產生時間 `11-19 20:33`（及 `20:42` live 畫面），`#econ`《各公司最新財報重點》已出現 `WMT 2026-11-19 SEC 8-K（營收 US$188.80B）`、即時新聞也在報 WMT 盤前下跌，但同一時刻的《接下來 72 小時》仍列 `11/19 21:00 WMT/BABA/PDD 財報（盤前）》、`重大事件倒數` 仍在倒數 `0 天 0 小時 16 分`、`#econ`《美股財報日曆》仍將 WMT/BABA/PDD/NTES 列在「即將公布」，`macro_voice.json`（`20:01`）亦仍寫「今晚九點，沃爾瑪、阿里巴巴、拼多多先公布財報」。
- 正確應該是什麼：BABA（<18:18）、PDD（19:30）、WMT（20:00／美東 07:00）與 NTES 於 20:01 前皆已公布 Q3/Q2 財報（台北 21:00 是 WMT 電話會議而非公布財報，https://www.stocktitan.net/sec-filings/WMT/8-k-walmart-inc-reports-material-event-0371aee37dfe.html ；https://www.globenewswire.com/news-release/2026/11/19/3406398/0/en/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results.html ）。

### SITE-3｜API 錯誤：`GET https://wallstreet-sentinel.pages.dev/api/etf` 回傳 HTTP 502
- 本站寫了什麼：瀏覽器載入首頁 `https://wallstreet-sentinel.pages.dev/` 時，網路請求 `GET https://wallstreet-sentinel.pages.dev/api/etf` 直接回傳 **HTTP 502** 錯誤。
- 正確應該是什麼：需檢查 Cloudflare Pages Function `functions/api/etf.js` 上游來源或快取狀態，避免 ETF 相關資料載入失敗。

### SITE-4｜`#econ`《本週重要經濟數據》重複列示「零售銷售」兩次（11-16 與 11-17）
- 本站寫了什麼：線上 `#econ`《本週重要經濟數據》中，在 `11-16 週一`（`台北 11/16 21:30`）與 `11-17 週二`（`台北 11/17 21:30`）連續兩天出現完全相同的項目：`零售銷售（公布 0.2% 預期 0.1% 前值 0.8%）`。
- 正確應該是什麼：美國 10 月零售銷售於 11 月 17 日公布（該日僅一筆），應去重避免跨來源日曆重複列示（待開發者檢查日曆去重邏輯）。

### SITE-5｜`#econ`《美股財報日曆》多檔下週科技股 EPS 預期與市場 Non-GAAP 共識及公司財測嚴重不符，且漏列今晚盤後 `GAP`
- 本站寫了什麼：線上 `#econ`《美股財報日曆》（`11-19 20:33`）列出：**ADSK** EPS 預期 `2.27`、**WDAY** `1.28`、**ZM** `1.00`、**HPE** `1.17`、**KEYS** `3.09`、**BSP** `0.25`，且 11-19 盤後漏列 **GAP**。
- 正確應該是什麼：對照公開來源，公司財測與 Non-GAAP 共識分別為 **ADSK $3.07**（公司指引 $3.04–$3.09，https://www.marketbeat.com/instant-alerts/upcoming-autodesk-adsk-set-to-announce-quarterly-earnings-on-tuesday-2026-11-17/ ）、**WDAY $2.74–$2.75**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ）、**ZM $1.49**（https://www.zacks.com/stock/news/3030700/zoom-communications-zm-falls-more-steeply-than-broader-market-what-investors-need-to-know ）、**HPE $1.27–$1.29**（公司指引 $1.20–$1.30，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ）、**KEYS $3.37–$3.38**（公司指引 $3.34–$3.40，https://www.tradingview.com/news/tradingview:dd00407af5aef:0-keys-q4-26-earnings-eps-estimate-is-3-37-usd/ ）、**BSP $0.31–$0.32**；且 **GAP** 於 11/19 盤後公布（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）。應標註 Nasdaq 來源可能為 GAAP 口徑以免新手誤判。

### SITE-6｜`#overview`《一個月後的總經》PCE 機率與 `forecast.json` 過時未同步，且與 `#econ`《PCE 物價》卡片互相打架
- 本站寫了什麼：線上 `#overview`《一個月後的總經》（`11-19 07:03`）仍顯示 `10 月核心 PCE 年增率會在 2.4% 到 3.0% 之間` 機率 **60%**（本地 `forecast.json` 第 130 行仍寫 `9 月核心 PCE 數字：查無`），但同站 `#news`《Gemini 第二意見》（`20:34`）寫 Claude 已降至 45%，而 `#econ`《PCE 物價》（`13:12`）更已自行算出 10 月核心 PCE 年增約 **3.2%**。
- 正確應該是什麼：BEA 已於 10/29 公布 9 月核心 PCE 年增 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ），應將 9 月實際值寫入 `forecast.json` 並更新頁面機率與前值。

### SITE-7｜《重大事件倒數》標頭停在 5 天前、`即時通知` VIX 警報與即時報價矛盾、`macro_voice` 油價／台股說法滯後
- 本站寫了什麼：線上《重大事件倒數》卡片底部顯示 `最後更新 11-14 22:26・資料日 11-18`（5 天前）；即時報價條在 `20:27–20:43` 顯示 **VIX 已回落至 `22.19–22.42（-8.7%～-9.6%）`**，但頂部《即時通知》仍持續亮紅燈 `🔴 有預警力的規則觸發：VIX 升破 25`；`macro_voice.json`（`20:01`）仍說台股大跌「我手上沒有時間對得上的單一消息」且布蘭特原油「大約八十九美元」（Yahoo 即時條顯示 `89.94–90.12`，主力期貨報價約 `$91.5–$92.2`）。
- 正確應該是什麼：11/19 台股大跌有自營商避險賣超 214.40 億、1.29 億違約交割與金管會宣布 1,028 檔 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；另 VIX 警報與《重大事件倒數》時間戳記應與最新即時報價同步。

### SITE-8｜`#news`《Gemini 第二意見》卡片摘要寫「查了 0 家公司」與 `/api/gemini_ask` 脫鉤；《未來 14 天事件》漏標「TIPS」及多項重大日程
- 本站寫了什麼：`#news`《Gemini 第二意見》摘要顯示 `查了本站找不到原因的 0 家公司`（且頁面內容為前輪 D-1～D-3 討論，未涵蓋 `/api/gemini_ask` 的 12 檔盤前異動股）；《未來 14 天事件》（`11-19 20:28`）仍寫 `11-19 美債 10 年期標售（增額） $19B` 而未標明「TIPS」。
- 正確應該是什麼：該筆 $19B 標售為 **10 年期 TIPS 增額**（CUSIP `91282CRE3`，票面 2.375%、2036/07/15 到期，https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ）；且《未來 14 天事件》漏列 11/20 台股限空令／台灣 10 月外銷訂單／SNDK 拆股、11/25 褐皮書、11/26 感恩節休市與韓銀決策、11/28 台灣九合一選舉及 11/29 OPEC+ 會議。

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆（20:52 對照 live `#news` 與 `#econ` 核對）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳川習會與美中俄三方峰會（已結束）；BABA、NTES、PDD、WMT 財報（均已公布）；台北 21:00 **WMT 電話會議**；美東 09:30（台北 22:30）**Anthropic (ANT)** 那斯達克掛牌（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ）；美東 12:30（台北 11/20 01:30）芝加哥聯準銀行總裁 Goolsbee 座談（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；美東 13:00（台北 11/20 02:00）**美債 10 年期 TIPS 增額標售 $19B（CUSIP 91282CRE3）**（https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ）；美東 15:00（台北 11/20 04:00）里奇蒙聯準銀行總裁 **Barkin** 經濟座談與聯準會理事會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP、KEYS** 財報（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  2. **11/20（五）**：**台股金管會 3.5% 有條件限空令與盤中借券上限 1% 上路**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；**印度強氣旋「阿克萬」中午登陸奧里薩邦**；**台灣經濟部 10 月外銷訂單**（台北 16:00，https://money.udn.com/money/story/10869/9879179 ）；美東盤前 **BSP** 財報；**美股月選擇權到期（OPEX）**；**密大消費者信心指數終值**（美東 10:00／台北 23:00）；**SanDisk (SNDK) 1 拆 8 拆股後首日交易**（https://www.fool.com/investing/2026/11/16/sandisk-splits-its-stock-8-for-1-on-nov-19-flash-memory-prices-still-matter-more-than-the-share-count/ ）。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM、A** 財報。
  5. **11/24（二）**：美東盤前（台北 20:00–21:00）**ADI、MDT、BBY、DLTR、BURL、DKS、BILI**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY**。
  6. **11/25（三）**：美東盤前（台北 21:00）**DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與提前公布之週初領失業金；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**；台北 11/26 **宏于電機（7869，台股上櫃）掛牌**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/28（六）**：**台灣 2026 九合一地方選舉投票日**。
  10. **11/29（日）**：**OPEC+ 部長級／JMMC 會議**（討論 2027 年產量配額）。
  11. **11/30（一）**：**MSCI 季度調整台股收盤生效（台北 13:30）與月底資產再平衡**。
  12. **12/01（二）**：美東 10:00（台北 23:00）**ISM 製造業 PMI 與 10 月 JOLTS 職位空缺**；**CRWD、MRVL、OKTA、NTAP** 盤後財報；**韓國 11 月出口初值**；台股 **騰勢（7889）掛牌**。
  13. **12/02（三）**：美東盤後（台北 12/03 05:00）**CRM、SNOW、ZS** 財報（https://www.tradingview.com/news/tradingview:c28752bb00e6f:0-zscaler-hosts-2026-investor-day-reaffirms-q1-and-fiscal-2027-guidance/ ）。
  14. **12/03（四）**：美東 10:00（台北 23:00）ISM 服務業 PMI；美國參議院銀行委員會就先進晶片出口與資料中心基礎設施舉行聽證會。
- 對照本站（live `#news`《未來 14 天事件》與 `#econ`《美國經濟日曆》《IPO 觀察》《美股財報日曆》）：
  - **漏列項目**：11/20 金管會限空令 2.0、SNDK 拆股與台灣 10 月外銷訂單；11/21 韓國 20 日出口；11/25 聯準會褐皮書；11/26 韓國央行；11/26 感恩節休市與 11/27 半天交易（《未來 14 天事件》未列，僅 `#econ` 另有休市卡）；11/28 台灣九合一選舉；11/29 OPEC+ 會議；`ANT`（Anthropic IPO）未列入《IPO 觀察》或《未來 14 天事件》；`GAP` 未列入《美股財報日曆》。
  - **錯置／未更新項目**：11/19《未來 14 天事件》`美債 10 年期標售（增額）$19B` 漏標「TIPS」；《IPO 觀察》與《接下來 72 小時》誤列早已於 2025/10 上市的 `MPLT`；《美股財報日曆》多檔 EPS 預期（ADSK、WDAY、ZM、HPE、KEYS）疑為 GAAP／舊值且低於共識。

---

### CODE-1｜wsb/data/valhist.py：第 143、162 與 169 行在盤中空資料時把 `today` 標為永久 `empty` 並寫入 `latest_day`，鎖死當日收盤後及月底更新（無新進展）
- 檔案路徑與行號：`wsb/data/valhist.py` 第 143、150–170 行（`refresh_tw()`），連動第 85–93 行（`_tw_day()`）。
- 那一行在做什麼：`refresh_tw()` 先抓取 `"latest"`（傳入 `today`），再補抓過去 60 個月底的台股本益比／股價淨值比／殖利率快照（`BWIBBU_d`＋`peQryDate`）；當某天抓不到資料時，將該日寫入 `tried[day] = "empty"` 以避免未來重複查詢休假日。
- 為什麼有問題：若在台北時間盤中或收盤前（證交所尚未發布當日 `BWIBBU_d`，約 16:00 前）執行 `refresh_tw()`，`back = 0`（即 `today`）向證交所查詢時，證交所會回傳 `{"stat": "很抱歉，沒有符合條件的資料!"}`，此時 `_tw_day(today)` 第 89–92 行回傳 `{}`（非 `None`）；第 158 行 `if rows:` 為假，導致第 169 行直接寫入 `tried[today] = "empty"`。接著 `back = 1` 抓到昨天資料，第 160 行把 `d["latest"]` 設成昨天的資料，但第 162 行卻把 `d["latest_day"]` 寫成 **`today.isoformat()`**！這會同時造成兩個後果：（1）當天收盤後重跑時，第 143 行 `if key == "latest" and d.get("latest_day") == today.isoformat(): continue` 直接跳過更新，讓 `latest` 整天卡在昨天；（2）若 `today` 恰好是該月最後一個交易日，`tried[today] = "empty"` 會使該月底快照永久被第 147 行跳過，改存成前一個交易日的數字。
- 建議怎麼改：（1）只有當 `day < today` 時才允許把空結果寫入 `tried[day] = "empty"`（`today` 盤前尚無資料屬正常，不該標成休市空日）；（2）第 162 行將 `d["latest_day"]` 改設為實際抓到的交易日 `day.isoformat()`（或僅在 `day == today` 時設為 `today`），否則盤後重跑時應允許再嘗試 `today`。
- 確定度：高。

### CODE-2｜tools/site_events.py：第 76 行允許無 `mcap` 的 AI 供應鏈股通過篩選，但第 85 行直接 `float(r["mcap"])` 未防呆導致崩潰（無新進展）
- 檔案路徑與行號：`tools/site_events.py` 第 76 與 85 行（`earn_events()`），連動第 179 行（`_earn_tile()`）與第 237 行（`upcoming()`）。
- 那一行在做什麼：第 76 行篩選未來 `days` 天內財報公司，若市值低於門檻 `floor` 但屬於 `ai_syms()`（AI 供應鏈）仍予以保留，並於第 85 行打包字典回傳。
- 為什麼有問題：第 76 行特地寫成 `float(r.get("mcap") or 0) < floor and r.get("sym") not in ai`，代表開發者已知 `earn_days.json` 裡的 `r["mcap"]` 可能缺漏或為 `None`。然而一旦某家 `ai_syms()` 名單內的公司（如近期新增的 `CRWV`、`NBIS`）在 `earn_days.json` 中沒有填市值（`mcap` 為 `None` 或缺鍵），第 76 行放行後，第 85 行直接執行 `float(r["mcap"])` 就會拋出 `TypeError` 或 `KeyError`，使整個 `earn_events()` 中斷，連帶讓總覽頁倒數卡片的財報區塊與 `upcoming.json` 的所有財報列表一起失效；同列 `cap_txt(r["mcap"])`（第 179 行）與 `round(r["mcap"] / 1e12, 2)`（第 237 行）亦假設 `mcap` 必為非空數字。
- 建議怎麼改：第 85 行改為 `mcap = float(r.get("mcap") or 0)`，並在第 179 行僅於 `r.get("mcap")` 大於 0 時顯示市值文字、無市值時略過該前綴文字。
- 確定度：高。

（備註：本小時台北 20 時批次 `i % 24 == 20` 共 12 檔：`tools/site_bondread.py`、`tools/site_events.py`、`tools/site_observer.py`、`tools/site_twlive.py`、`wsb/analytics/capex_link.py`、`wsb/analytics/fund_trend.py`、`wsb/analytics/real_economy.py`、`wsb/analytics/twmacro.py`、`wsb/data/crypto.py`、`wsb/data/fred.py`、`wsb/data/private_credit.py`、`wsb/data/valhist.py` 皆已逐行重讀完畢。其餘 10 檔經核對單位換算、時區、授權序列遮罩與過期處理均無問題。）

---

其他今天的大事：
- 沃爾瑪（WMT）於台北 11/19 20:00（美東 07:00）公布 Q3 FY27 財報，營收 **1,888 億美元（+5.2% YoY）**、調整後 EPS **0.65 美元**雙雙優於預期，並上調全年常數匯率淨銷售成長至 4.9%–5.2% 及調整後 EPS 至 $2.84–$2.89，但受股價高檔影響盤前小跌約 0.7%–1.6%（https://www.stocktitan.net/sec-filings/WMT/8-k-walmart-inc-reports-material-event-0371aee37dfe.html ；https://finance.biggo.com/news/462fcfe0-7cf8-4cdf-b251-332c42101b59 ，台北 2026-11-19）。
- 拼多多（PDD）Q3 2026 營收持平（1,083.4 億元）遜預期，但因縮減行銷開支使 Non-GAAP 每 ADS 盈餘達 **3.14 美元**大勝預期，截至 20:41 盤前上漲 **7.1%**；網易（NTES）營收與獲利雙遜預期盤前跌逾 **3.5%–5%**；阿里巴巴（BABA）因 CapEx 增 60% 致 FCF 淨流出 344.72 億人民幣且庫藏股縮水，盤前小跌約 0.1%–2%（https://www.globenewswire.com/news-release/2026/11/19/3406398/0/en/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results.html ；https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ；https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ）。
- 挪威國營能源巨頭 **Equinor** 證實遭持續性網攻導致部分企業 IT 與郵件中斷並通報挪威 NSM（油氣生產與出口暫未受影響），同時荷莫茲海峽東側接連傳出油輪觸及水雷起火；歐盟議會與理事會 11/19 同意將油氣煤進口商甲烷申報規定延後兩年至 2029–2030 年以緩解能源供應壓力（https://therecord.media/norway-equinor-cyberattack-energy ；https://english.alarabiya.net/News/middle-east/2026/11/19/three-oil-tankers-catch-fire-after-hitting-naval-mines-east-of-strait-of-hormuz-report ；https://europeansting.com/2026/11/19/methane-deal-to-delay-reporting-and-monitoring-for-energy-importers/ ）。
- 巴西參議院完成 500–600 億雷亞爾財政緊縮包裹案（PLP 299/2026）表決移送眾院，財政部長 Dario Durigan 強調三權均須遵守支出紀律；美國 11/19 刊登生效的 BIS 遠端算力管制新規（`2026-23529`）亦將巴西列入高轉運風險國（https://www.poder360.com.br/poder-congresso/nao-ha-licenca-para-gasto-indiscriminado-dos-3-poderes-diz-durigan/ ；https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors ）。
- 台股 11/19 重挫 1,768.02 點收 38,426.89 點、櫃買跌 7.22%，盤後爆 1.29 億元違約交割且金管會宣布 11/20 起 1,028 檔個股納 3.5% 平盤下禁空令；另台積電資深副總張曉強親赴輝達固鏈，Vera Rubin 平台已於 Q3 進入量產出貨，台積電並正式公告 5 億美元入股 Anthropic（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190254.aspx ）。

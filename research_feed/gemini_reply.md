台北時間 2026-11-19 17:38

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）、整體 PCE 年增率為 **3.6%**（月增 **0.5%**），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，台北時間 2026-10-29，HTTP 200 確認）。
- 事實：之所以 9 月核心 PCE（3.1%）反過來高於核心 CPI（2.6%），根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 高於核心 CPI 的倒掛現象（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。
- 事實：本地 `research_feed/forecast.json` 第 130 行仍寫 `9 月核心 PCE 數字：查無。`（17:30 重讀確認仍未更新），與 BEA 官方新聞稿及線上《財經日曆》PCE 卡片顯示的前值不符。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照（無新進展）
- 事實：歐洲央行（ECB）2026 年 11 月《金融穩定評估》Box 3（"The debt financing of AI and its implications for financial stability"）明確列出美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 共識（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，台北時間 2026-11-18，HTTP 200 確認）。
- 事實：ECB Box 3 正文對自由現金流的口徑為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（僅以**資本支出超過營運現金流**作為表層口徑，未把尚未起租的表外租賃算進單季現金流）；同時於圖表 A 與註腳 6 依美國會計準則 **ASC 842** 單獨指出，已簽約但資產尚未投入使用的租賃與算力承諾在起租前不計入資產負債表負債，這類表外承諾合計已逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200 確認）。
- 事實：四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與租賃口徑落差如下：
  - Meta（Q3 2026）：營運現金流 **$32.79B**，資本支出（含融資租賃本金償還）**$34.91B**，自報自由現金流為 **-$2.12B（轉負）**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）。
  - Alphabet（Q3 2026）：營運現金流 **$42.29B**（$42,290M），現金 PP&E 購置（不含融資租賃）**$51.36B**（$51,355M），自報自由現金流為 **-$9.07B（-$9,065M，轉負，含 52 億美元歐盟罰款支付）**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）。
  - Amazon（Q3 2026／TTM）：單季營運現金流 **$42.42B**、單季淨 PP&E 購置 **$75.93B**（隱含單季 **-$33.51B**），公司自報 **TTM 自由現金流 -$42.36B（-$42,357M，轉負）**，該口徑僅扣現金淨 PP&E、未扣額外揭露之新簽融資租賃資產（Q3 單季 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）。
  - Microsoft（Q1 FY27）：營運現金流 **$58.02B**，現金 PP&E 資本支出 **$39.37B**，自報自由現金流為 **+$18.6B（仍為正值，年減 27%）**；若計入新起租之融資租賃，總資本支出達 **$45.2B**，扣除後仍餘約 +$12.8B，印證 ECB 精準寫 `"most"` 而非全部（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（補充 16:34 最新語音稿對能源下跌「原因還不知道」之實例）
- 推理：檢視 `research_feed/claude_notes.md`、`research_feed/forecast.json`、`research_feed/sessions.json` 與 `research_feed/macro_voice.json`（`2026-11-19 16:34 台北` 加班版），最常「下太快」的是以下兩種思考捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：例如 `claude_notes.md` 第 14 行在還沒核對 `bea.gov` 或本站日曆卡片前值的情況下，因為「核心 PCE 通常比核心 CPI 低」，就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推 10 月區間；以及 `forecast.json` 第 65–73 行先前曾用單一 `BAMLH0A0HYM2`（3.43%）得出「信用市場還沒出現壓力」（第 3 輪你已修正）。
  2. **把「自己的新聞關鍵字只抓到標題或沒對上時間」直接當作「沒有原因」**：例如 `sessions.json` 第 30 行寫「油價與黃金是今天最大的謎…沒有找到時間對得上的消息」，最新 `macro_voice.json`（`2026-11-19 16:34 台北` 加班版）第 7 行仍寫著「能源這邊，我找不到時間對得上的原因…埃克森美孚和雪佛龍各跌約四趴。原因還不知道」，但其實 11/18 當天正是（1）EIA 每週三固定美東 10:30 公布原油庫存大增 340 萬桶、汽油大增 520 萬桶，（2）雪佛龍每股 1.78 美元除息日（佔其 -4.74% 未還原跌幅約 0.8 個百分點），以及（3）50 億美元併購談判。先前 `macro_voice.json` 14:15 午班亦曾把 11/18 新台幣收盤 32.947 元當成 11/19 當日表現（而 11/19 盤中曾急貶破 33 見 33.040、16:00 才收升 32.942 元）。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標（補充台積電 11/19 正式公告入股 602.4 萬股）
- 事實：中央社 11/19 引述 Anthropic 公開說明書指出，Anthropic 至 2045 年算力合約承諾高達 **9,009 億美元**（2030 年底前到期約 4,520 億美元），其中涵蓋博通 1,612 億美元、Alphabet 1,213 億美元、SpaceX 1,205 億美元、AWS 1,100 億美元與 Azure 449 億美元（https://www.cna.com.tw/news/afe/202611190156.aspx ，台北時間 2026-11-19，HTTP 200 確認）。11/19 台積電並正式公告透過子公司 TSMC Partners 以 **每股 83 美元**取得 Anthropic N 類普通股 **6,024,096 股**（總金額 499,999,968 美元，約合新台幣 164 億元，持股約 0.03%；搜尋來源：中央社／鉅亨網 11/19，受無頭環境限制無法開啟外部重導向）。
- 推理：若今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，傳導先後順序如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：負債比高、高度仰賴大模型算力長約抵押融資，且 Anthropic 轉向透過博通租賃 3.5 GW Google TPU 機櫃自建資料中心，直接稀釋第三方租賃溢價。隔天（11/20）可驗證指標：`CRWV`、`NBIS` 相對 `QQQ` 的開盤超額跌幅，及新雲端無擔保債二級殖利率走勢。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸**：ANT 公開發行募資 813.1 億美元（含 260 億美元同步私募合計約 1,073 億美元）、完全稀釋估值約 1.5 兆美元，若破發將壓縮 OpenAI 與晚期 AI 獨角獸 IPO 窗口。隔天可驗證指標：`ARCC`、`BIZD`、`BX`、`APO` 股價與承銷商是否啟動護盤機制（stabilizing bid）之報導。
  3. **最後且分化：晶片與機櫃合作夥伴（NVDA、AVGO、GOOGL、AMZN、MSFT、MU、台積電等同步私募出資方）**：主要承受公允價值重估回吐，但 Anthropic 轉向自建反而讓博通與 TPU 機櫃組裝廠（英業達、廣達、鴻海）受關注。隔天可驗證指標：`AVGO`／`NVDA` 相對 `^SOX` 強弱與次日選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態（17:38 補充：IEA 11/19《2026 世界能源展望》最新警告、台積電公告入股與櫃買 285.33 收盤）
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意**，ECB Box 3 佐證多家一線雲端商 FCF 轉負、表外承諾逾 4 兆美元，且 Oracle 據報單是未起租資料中心承諾達 2,880 億美元、標普信評已降至 BBB-；台積電 11/19 亦正式公告參與 Anthropic 4.9999 億美元私募，顯示供應鏈與客戶資金進一步綁定，但尚未演變為連鎖違約；美國 9 月 TIC 外資淨流入仍達 2,610 億美元（https://home.treasury.gov/news/press-releases/sb0693/ ）。
  2. **主線 2（輝達治理風波 vs 出口調查）— 部分同意，兩條線已證實交織**：中央社 11/19 引述川普接受《福斯新聞》專訪指出，與黃仁勳有染的一名女子正受到美國政府調查是否為中國情報機構工作、以及是否協助走私晶片（https://www.cna.com.tw/news/aopl/202611193003.aspx ，HTTP 200 確認）。個人治理風波與國安／晶片出口調查不是二選一，而是**同一人物同時觸發公司治理與國安調查**，建議下一輪整併重估。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，補充亞歐股匯分化**：今日台股集中市場收跌 **1,768.02 點（-4.40%）至 38,426.89 點**、櫃買指數收跌 **-7.22%（-22.22 點）至 285.33 點**、上市櫃逾 **280 檔跌停**，金管會盤後宣布 **11/20 起升級 3.5% 限空令**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；但 **新台幣 16:00 反轉收升至 32.942 元**、日經 +0.71%、KOSPI +1.39%、印度 Nifty 50 收漲 +0.91%、歐股盤中小紅（DAX +0.5%～0.6%），顯示殺盤高度集中在台港 AI 槓桿籌碼與高利率折現修正。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意，補充 IEA 11/19 最新警告**：**國際能源總署（IEA）11/19 發布《2026 世界能源展望（World Energy Outlook 2026）》**，執行長 Fatih Birol 公開警告美以伊衝突與荷莫茲海峽封鎖已造成「**史上最大的能源安全威脅**」，衝擊規模「讓 1970 年代石油危機相形見絀」；而今日盤面受昨日 EIA 累庫與庫爾德／阿曼轉運壓抑，布蘭特約 $92.0–92.16、WTI 約 $83.0–83.6，基本面過剩與歷史級地緣封鎖風險互相撕扯，仍維持 **55%**。
  5. **主線 5（「風險升級」劇本 33% vs 40%）— 同意方向一致**，差距 7 個百分點；ECB 拒絕為法國公債利差撐盤、德國 IG Metall 罷工擴大，加上台股櫃買單日重挫 7.22% 引發限空令 2.0，顯示高槓桿市場的流動性裂縫正在累積。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題（更新 16:34 語音稿與 11/19 收盤細節）
- 1. `research_feed/macro_voice.json` 最新版本（`2026-11-19 16:34 台北` 加班版）與 `research_feed/sessions.json`（11/18 盤後）仍寫著「能源這邊，我找不到時間對得上的原因…埃克森美孚和雪佛龍各跌約四趴。原因還不知道」。事實上 11/18 是雪佛龍每股 1.78 美元除息日，同日美東 10:30 EIA 原油庫存大增 340 萬桶、汽油大增 520 萬桶。你的語音腳本管線要如何同時接入「個股除息日曆」與「EIA 每週三固定發布時點」？
- 2. 11/19 下午中央社報導與黃仁勳有染女子涉中國情報與晶片走私調查（https://www.cna.com.tw/news/aopl/202611193003.aspx ），IEA 同日發布《2026 世界能源展望》警告荷莫茲海峽構成「史上最大能源安全威脅」，且台股櫃買跌 7.22% 後金管會升級 3.5% 限空令——第 4 輪你打算如何調整「輝達事件定性」與「油價／風險升級」的機率？
- 3. 本地 `research_feed/forecast.json` 第 130 行截至 17:30 仍寫「9 月核心 PCE 數字：查無」，但 BEA 新聞稿（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）與線上《財經日曆》早已載明 9 月核心 PCE 為 3.1%。為什麼預測 JSON 沒有同步更新這項前值？

---

### WIDE-1｜IEA 11/19《2026 世界能源展望》警告荷莫茲危機為「史上最大能源安全威脅（超越 1970 年代）」，UKMTO 證實 ADNOC 遇襲（更新）
- 事實：國際能源總署（IEA）於 **2026 年 11 月 19 日**正式發布年度《2026 世界能源展望（World Energy Outlook 2026）》，執行長 Fatih Birol 指出，2026 年 2 月爆發的美以伊衝突與伊朗對荷莫茲海峽的封鎖及油輪襲擊，已構成「**史上最大的能源安全威脅（largest threat to energy security in history）**」，其斷供風險「**讓 1970 年代石油危機相形見絀**」，能源世界「再也回不去從前」（Channel NewsAsia / Times of Israel / Argus Media 2026-11-19 搜尋摘要；受無頭環境無瀏覽器視窗限制，單篇重導向直連網址未開啟驗證）。同日 UKMTO 證實 11/18 ADNOC 船隻在荷莫茲海峽遇襲（11 傷、1 失蹤），伊朗軍方另宣稱 3 艘油輪觸水雷起火（未公布船名，待獨立查證，https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ）；11/19 布蘭特原油在 EIA 原油累庫 340 萬桶與阿曼船對船轉運恢復下暫報 **$92.0–92.16／桶**、WTI 約 **$83.0–83.6／桶**（WAM / Trading Economics 搜尋摘要）。
- 推理：美股盤面只看 EIA 週庫存累庫與川習會口頭保通航，將油價壓在 83 美元附近；但 IEA 直接定調緩衝庫存耗盡、中長期供給結構受創，一旦水雷或保險拒絕承保擴大，遠月原油曲線與成品油裂解價差會比近月期貨更早反映緊縮。
- 先影響資產：布蘭特原油遠月價差、航空與海運燃油成本、油輪與能源基礎設施債券。

### WIDE-2｜APEC 深圳「川習會（30 對 30 協議）」與史上首次美中俄三方領袖峰會登場（無新進展）
- 事實：11/19 中午美中元首「川習會」在深圳麒麟山莊登場，川普稱美中就「**30 對 30 協議（30 for 30 deal）**」同意各自對價值 **300 億美元**商品削減關稅；稍早川普與普丁會談約 40 分鐘，下午接續舉行**美中俄首次三方領袖峰會**聚焦核武軍控、烏克蘭與伊朗局勢，惟學者評估休戰仍脆弱且難產出具體條約（https://www.cna.com.tw/news/aopl/202611193005.aspx ；https://www.cna.com.tw/news/acn/202611190062.aspx ；https://www.voachinese.com/a/trump-meets-putin-in-shenzhen-as-trade-disputes-loom-over-talks-with-xi-20261119/8225437.html ，HTTP 200 確認）。同日中國上證指數小跌 **-0.28%** 收 **3,577.62 點**、恆生指數收跌 **-1.95%** 至 **22,841.62 點**（失守 23,000 點，鉅亨網／群益搜尋摘要）。
- 推理：貿易端微幅降稅與同日生效的 BIS 遠端算力封鎖並行，顯示美中正從全面脫鉤轉向「一般商品減壓、先進算力與金融國安持續加壓」的長期分化。
- 先影響資產：USD/CNH、中概股（KWEB）、美國農產品期貨、歐洲天然氣。

### WIDE-3｜日本央行總裁植田和男 11/19 國會重申升息決心；熊本 M5.7 地震（7 月 M7.1 餘震）尚無 JASM 重大停工回報（更新）
- 事實：路透社／Channel NewsAsia 於 11/19 報導，日本央行（BOJ）總裁植田和男在國會表示金融環境仍寬鬆，警告潛在通膨有突破 2% 上行風險，強化 12/17–18 升息至 **1.50%** 預期（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ，HTTP 200 確認）。同日清晨 02:22（台北 01:22）熊本發生規模 **5.7 地震**（深度 10 公里、水俁市震度 5 弱、至少 2 傷、九州新幹線部分暫停），日本氣象廳研判為 **7 月 28 日熊本規模 7.1 強震**之相關餘震並提醒未來一週防範類似餘震；截至目前無台積電熊本 JASM 廠重大結構損壞或停工回報（https://www.chinadailyasia.com/hk/article/642914 ，HTTP 200；Japan Times / 新華社搜尋摘要）。日經 225 指數 11/19 收漲 **+0.71%** 至 **59,444.21 點**。
- 推理：美股定價聯準會 12/9 升息，卻未充分定價 BOJ 12/17–18 跟進升至 1.50% 的美日雙重抽水；若未來一週熊本再出現強餘震，將疊加供應鏈心理壓力。
- 先影響資產：USD/JPY、日本 10 年期公債、全球高槓桿科技股。

### WIDE-4｜歐洲通膨黏著＋ECB 拒替法國債市撐盤＋德國 IG Metall 罷工潮；南非央行 11/19 利率維持 7.25% 不變（更新）
- 事實：英國 10 月 CPI 升至 **3.6%**（https://www.mufgresearch.com/macro/european-macro-18-november-2026/ ）、歐盟執委會估 2026 歐盟通膨 **3.3%**（https://www.eunews.it/en/2026/11/17/eurozone-and-eu-growth-to-top-forecasts-in-2026-though-inflation-remains-a-drag/ ）；ECB《金融穩定評估》點名法國政局與赤字推升法德利差且「無意出手買債撐盤」，今日法國 10 年期 OAT 殖利率維持 **約 4.87%** 高檔，歐股盤中微漲（DAX 約 +0.5%～0.6%、CAC 40 約 +0.4%～0.8%、FTSE 100 近持平；Investing.com／Trading Economics 搜尋摘要）。勞動端則有德國最大工會 **IG Metall** 涵蓋 370 萬勞工（含 Mercedes-Benz 與 Audi 廠區）本月持續發動警告與 24 小時罷工要求加薪 5%，疊加法國港口 24 小時罷工（Al Jazeera 搜尋摘要；https://www.hillebrandgori.com/port-updates ）。此外，**南非央行（SARB）11/19 宣布基準附買回利率維持 7.25% 不變**（基本放款利率 10.75%），儘管 10 月通膨升至 5.2%，仍因景氣趨緩選擇暫停（Channel Africa / IOL 搜尋摘要）。
- 推理：歐洲面臨「通膨未退、財政利差央行不救、製造業工運升溫」三重擠壓，與拉美（巴西因應美關稅、墨西哥對非 FTA 國調高關稅、阿根廷連兩季萎縮陷入技術性衰退）共同壓抑全球實質製造與新興市場風險胃納。
- 先影響資產：法德 10 年期公債利差、EUR/USD、歐洲汽車製造商與銀行股、南非蘭特（USD/ZAR）。

### WIDE-5｜印度 Nifty 50 11/19 逆勢反彈收漲 +0.91%，強氣旋「阿克萬」預計 11/20 中午登陸奧里薩邦（撤離逾 10 萬人）（更新）
- 事實：印度 10 月 CPI 升至 **6.09%** 突破央行 6% 上限（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ），但今日（11/19）印股在汽車與銀行股帶動下低接反彈，**Nifty 50 收漲 +230.80 點（+0.91%）至 25,458.75 點**、**BSE Sensex 收漲 +783.83 點（+0.96%）至 82,815.64 點**（Business Standard 2026-11-19 搜尋摘要；受無頭環境限制未開啟重導向直連網址）。氣象端，印度氣象局（IMD）追蹤強烈氣旋 **「阿克萬（Akvan）」** 持續北移，預計於 **2026 年 11 月 20 日中午**在奧里薩邦（Odisha）Gopalpur 附近登陸（最大陣風可達 110 km/h），當地已緊急撤離 **逾 10 萬人**（https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ，HTTP 200；Hindustan Times 搜尋摘要）。
- 推理：外資 11 月大舉轉進印度逾 100 億美元做為 AI 避風港，但國內通膨已破 6% 上限，明日中午氣旋登陸若衝擊東岸農產、港口與電力供給，恐進一步推高食物通膨並限制 RBI 政策空間。
- 先影響資產：印度 Nifty 50、USD/INR、新興市場資金流（INDA）。

---

### A｜今天的大動（美東 11/19 04:38 盤前，美股尚未開盤；沿用 15:31 題目單並補全驗證）
- 說明：本輪 `browser` 子代理因非 Hub 視窗會話無法開啟（`conversation is not open in any Hub window`），且遵守禁止執行額外程式規範，無法即時重連 `https://wallstreet-sentinel.pages.dev/api/gemini_ask` 檢查 15:31 後是否新增題目；以下保留 15:31 題目單之四檔標的（美股正規盤將於台北時間今晚 22:30 開盤）。

### PANW｜Palo Alto Networks（PANW）11/18 正規盤先漲 +9.90%，盤後 Q1 FY27 財報全面優於預期並宣布 45 億美元併購 Applied Compute 再漲 +9.1%（無新進展）
- 事實：美東 11 月 18 日正規盤 PANW 先漲 **+9.90%**（$309.29→**$339.92**）；盤後公布 Q1 FY27 財報，營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億美元）、Non-GAAP EPS **1.05 美元**（優於預期 0.97 美元）、NGS ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**（FactSet 共識 141.7 億美元）、調整後 EPS 指引至 **4.26～4.30 美元**（FactSet 共識 4.18 美元），並宣布以 **45 億美元**全股票收購開源權重 AI 模型平台 **Applied Compute**，帶動盤後／盤前再漲 **+9.1%（一度 +11%）**（https://www.prnewswire.com/news-releases/palo-alto-networks-reports-fiscal-first-quarter-2027-financial-results-302944393.html ，HTTP 200；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ，HTTP 200；https://www.tradingview.com/news/stocktwits:77181b970094b:0-panw-stock-soars-11-after-hours-on-q1-earnings-beat-4-5b-acquisition-announcement/ ，HTTP 200）。
- 本站漏掉的：15:31 即時題目單仍標「本站沒有找到對得上的新聞」。同日盤後 **Everpure（NYSE: P，原 Pure Storage）** Q3 FY27 營收年增 **51%** 至約 **14.6 億美元**（新聞稿約 $1.5B）、調整後 EPS **0.86 美元**並連三季上調全年指引至 **52.0 億～52.1 億美元**（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ，HTTP 200）。

### CRWD｜CrowdStrike（CRWD）11/18 正規盤漲 +7.95% 收 $237.03，盤後／盤前受 PANW 財報驗證 AI 資安需求外溢續漲 +6.0%（無新進展）
- 事實：CRWD 美東 11 月 18 日正規盤由 $219.58 漲 **+7.95%** 至 **$237.03**，盤後／盤前再漲 **+6.0%**，主因同業 PANW 財報驗證企業 AI 資安需求強勁而出現板塊連動（https://www.globalbankingandfinance.com/crowdstrike-holdings-crwd-rises-2026-11-18/ ，HTTP 200；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，HTTP 200）。近期 Cantor Fitzgerald 維持 **Overweight** 並調高對 CRWD 的看法至 **$275**（https://www.tikr.com/zh/blog/cantor-fitzgerald-raises-its-crowdstrike-target-to-275-is-it-still-too-low ）。
- 本站漏掉的：CRWD 預計 **12 月 1 日盤後**才公布財報，目前無單獨公司公告（找不到來源），屬同業財報帶動的板塊外溢。

### CVX｜雪佛龍（CVX）受 11/18 除息每股 1.78 美元、EIA 原油與汽油庫存大增壓低油價，以及 50 億美元併購談判影響，未還原跌 4.74%、還原息後跌 3.95%（無新進展）
- 事實：CVX 美東 11 月 18 日正規盤收 **$205.88**（較 11/17 收盤 $216.13 **未還原跌 4.74%**，扣除當日季股息 **每股 $1.78** 除息調整後約 **-3.95% / -4.0%**），主因三事疊加：（1）11/18 為每股 $1.78 季股息除息日；（2）EIA 公布上週美國原油庫存大增 **340 萬桶**、汽油大增 **520 萬桶**，壓低油價並使能源股集體下挫（XOM、CNQ 同步走弱）；（3）市場消化其接近以 **50 億美元**收購墨西哥灣深水油商 **Beacon Offshore Energy** 的談判消息（https://www.globalbankingandfinance.com/chevron-cvx-falls-2026-11-18/ ，HTTP 200；https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ，HTTP 200；https://www.nationthailand.com/news/world/40073656 ，HTTP 200；https://www.bicmagazine.com/industry/investment-banking/chevron-closes-in-on-5b-beacon-deal/ ，HTTP 200）。

### CNQ｜Canadian Natural Resources（CNQ）11/18 正規盤隨油價重挫跌 4.63%（$45.53），盤前 +3.2% 無單獨公告或報告（無新進展，找不到來源）
- 事實：CNQ 美東 11 月 18 日正規盤隨北美能源股重挫收跌 **4.63%**（由 $47.74 跌至 **$45.53**，多倫多跌 4.06% 至 C$65.52），市場亦消化其宣布以 **25.3 億加元**收購 **Advantage Energy** 之支出（https://www.nationthailand.com/news/world/40073656 ，HTTP 200；https://www.newsfilecorp.com/release/324091/Canadian-Natural-Resources-Limited-Enters-into-Agreement-to-Acquire-Advantage-Energy-Ltd ）。
- 事實（盤前 +3.2%）：美東 11/18 盤後至今日凌晨無任何 CNQ 新聞、財報或分析師調評（找不到來源）。

---

### AN｜AN-1：最近 3 小時內（台北 14:38–17:38）無新增美股分析師調評；補上高盛調降 AVGO 看法與 Delta Analyst 降評 ORCL 細節
- 事實：檢索最近 3 小時（台北 14:38–17:38／美東 11/19 01:38–04:38 盤前早段），AI 供應鏈與美國市值前 20 大公司未見新發布的美股券商評等調整（找不到來源）。
- 事實（近期已確認報告與搜尋補強細節）：
  1. **摩根士丹利（11/19 亞太高峰會後報告）**：維持 **台積電（2330）** `Overweight` 評等與產業「有吸引力」看法，將估值看法調高至 **3,088 元**，預估 2027 年 2 奈米產能翻倍以上，2026／2027／2028 年 EPS 估 **112.10／148.64／189.81 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，台北時間 2026-11-19，HTTP 200 確認）。
  2. **高盛 Goldman Sachs（AVGO）**：分析師 James Schneider 維持 **AVGO** `Buy` 評等，但因同業估值倍數壓縮（評估倍數由 30 倍下調至 25 倍），將價格看法由 $540 調降至 **$460**，同時提醒關注聯發科競爭（TipRanks / TokenPost 搜尋摘要；受無頭環境限制無法開啟重導向取得直連網址）。
  3. **Rothschild & Co Redburn（AVGO）**：分析師 Mike Harrison 將 **AVGO** 由 Buy 調降至 **Hold / Neutral**，價格看法由 $595 調降至 **$398**，理由為依賴高舉債 AI 實驗室之獲利品質風險（TipRanks 搜尋摘要；單篇直連網址先前亦受 403 阻擋）。
  4. **Delta Analyst（ORCL）**：將 **Oracle（ORCL）** 由 **Buy 調降至 Hold**，點名高達 **2,880 億美元**未承諾／未起租資料中心租賃與龐大資本需求（TradingView 搜尋摘要；近期標普全球評等亦將 Oracle 長期信評調降至 **BBB-**）。
  5. **Summit Insights Group（11/18）與華爾街對 NVDA 調整**：Summit Insights 將 **NVDA** 由 Buy 調降至 **Hold**（https://www.tikr.com/fr/blog/is-summit-insights-wrong-to-give-up-on-nvidia-wall-street-still-sees-251 ，HTTP 200）；HSBC 分析師 Frank Lee 將 **NVDA** 由 Buy 調降至 **Hold**（看法 $365→**$170**，https://www.tradingview.com/news/binance_news:d94dcaa1f094b:0-hsbc-downgrades-nvidia-says-stock-may-struggle-until-new-ceo-is-named/ ，HTTP 200）；Benzinga 統計共 10 家機構下調 NVDA（含 Evercore ISI Outperform→In-Line 看法 $186、Bernstein $400→$200、Baird Outperform→Neutral，https://www.tradingview.com/news/benzinga:3bce7f47b094b:0-nvidia-gets-10-bank-downgrades-after-huang-exit-what-to-expect-ahead-of-q3-results/ ，HTTP 200）。另有搜尋摘要顯示 William Blair 將 NVDA 降至 Market Perform、將 AMD 升至 Outperform；KeyBanc 將 NVDA 降至 Sector Weight；Melius（看法 $185）與 GF Securities 降至 Hold；Oppenheimer 降至 Market Perform；RBC 維持 Outperform 但看法 $330→$230（直連網址於無頭環境未開啟）。
  6. **Moody's Ratings（11/18）**：維持 **NVDA** Aa1 債信評等，展望由 **Positive 調降至 Stable**（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ，HTTP 200）。
  7. **KeyBanc（PANW）**：分析師 Eric Heath 將 **PANW** 由 Sector Weight 調升至 **Overweight**、看法調高至 **$380**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，HTTP 200）。
  8. **Piper Sandler（MDT）**：將 **Medtronic（MDT）** 由 Neutral 調升至 **Overweight**、看法 $85→**$120**（https://www.tradingview.com/news/tradingview:5b080eae6cc49:0-piper-sandler-upgrades-medtronic-to-overweight-from-neutral-raises-price-target-to-120-from-85/ ，HTTP 200）。
  9. **YR Research（11/18）**：將 **AAPL** 由 **Sell 調升至 Hold**，理由為客戶黏著度與現金流漸具防禦性（https://www.tradingview.com/news/seekingalpha:d985f509f094b:0-sa-analyst-upgrades-downgrades-nvda-aapl-smci-tsla/ ，HTTP 200）。
  10. **Raymond James（SMCI）**：維持 **SMCI** 偏多評等與 **$65** 看法（https://247wallst.com/investing/2026/11/18/super-micro-computers-40-3-month-downturn-a-great-entry-point-says-this-wall-street-pro-who-predicts-165-returns/ ，HTTP 200）。

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）刊登聯邦公報生效，同日 HHS HIPAA 隱私權修正案（2026-23429）排定刊登（更新文件編號）
- 事實：美國商務部工業安全局（BIS）暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢至 2027-01-19）。新規增訂 § 744.24 遠端存取終端用途管制，限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則（https://public-inspection.federalregister.gov/2026-23529.pdf ，HTTP 200；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ，HTTP 200；https://www.milbank.com/en/news/bis-issues-new-rule-restricting-remote-access-to-advanced-chips.html ，HTTP 200）。新加坡與美國已就「受信任用戶」展開協商，馬來西亞亦尋求釐清規範（https://www.channelnewsasia.com/singapore/singapore-us-semiconductor-mddi-josephine-teo-6560761 ；https://www.cna.com.tw/news/afe/202611190022.aspx ，HTTP 200）。
- 事實（同日聯邦公報新增確認編號）：美國衛生及公共服務部（HHS）《HIPAA Privacy Rule: Changes to Support Coordinated Care and Individual Engagement and Reduce Regulatory Burdens》（**RIN `0945-AA00`**、聯邦公報文件 **`2026-23429`**）排定於 **2026 年 11 月 19 日**刊登聯邦公報（Federal Register 搜尋摘要；受無頭環境限制，單篇重導向直連網址未開啟驗證）。

### POL-2｜美國財政部 FinCEN 發布強化 CDD 提案、9 月 TIC 淨流入 2,610 億美元、OFAC 制裁與白宮 Quad 超級智慧宣言（無新進展）
- 事實：美國財政部 FinCEN 發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，落實 EO 14406，60 天公眾意見徵詢，https://home.treasury.gov/news/press-releases/sb0691 ，HTTP 200）；9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ，HTTP 200）；OFAC 宣布「Operation Economic Outcast」制裁真主黨與伊朗聖城軍黃金及現金網路（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 重申美國優先供應鏈韌性（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）；白宮發布亞洲經濟協議事實清單（https://www.whitehouse.gov/fact-sheets/2026/11/fact-sheet-president-donald-j-trump-secures-historic-economic-deals-for-american-workers-and-strengthens-americas-leadership-in-asia/ ）；CMS CRUSH 反詐欺提案（`2026-23461`）11/19 刊登聯邦公報（https://public-inspection.federalregister.gov/2026-23461.pdf ，HTTP 200）。

---

### TW-1｜11/19 台股跌 1,768 點收 38,426.89 點、櫃買暴跌 7.22% 收 285.33 點（上市櫃逾 280 檔跌停）；新台幣收升 32.942 元；金管會升級 3.5% 限空令（17:38 補充櫃買收盤點位與跌停家數）
- 事實（11/19 台股與權值股收盤）：加權指數盤中一度重挫 **1,935.21 點**下探 **38,259.7 點**，終場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，破年線）**，成交值 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190149.aspx ，HTTP 200）；**櫃買指數（OTC）重挫 -7.22%（-22.22 點）收 285.33 點**（盤中最低 284.96 點，通信網路、半導體與電子零組件上櫃類股跌逾 8%，上市櫃合計逾 **280 檔股票跌停**，Pocket／Goodinfo／非凡新聞搜尋摘要）。權值股中，**台積電（2330）**收 **2,100 元（-75 元 / -3.45%，破年線）**、**聯發科（2454）**收 **3,720 元（-220 元 / -5.58%）**、**鴻海（2317）**收 **220.5 元（-0.5 元 / -0.23%）**、**緯穎（6669）**收約 **1,410 元（跌逾 4%）**（聯合報／工商時報搜尋摘要）。
- 事實（11/19 三大法人現貨與期貨）：證交所公布三大法人合計賣超 **461.03 億元**（**外資 -243.12 億元**、**投信 +15.13 億元**、**自營商 -233.03 億元**，其中自營商避險部位 -214.40 億）（https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200）。期交所 `futContractsDate` 公布臺股期貨三大法人未平倉淨額合計為 **-8,883 口**（外資 **-99,219 口**、投信 **+91,791 口**、自營商 **-1,455 口**）。
- 事實（11/19 新台幣 16:00 收盤價）：開 32.960 元，盤中最低貶破 33 元見 **33.040 元**、最高 **32.920 元**，午盤暫收 32.988 元（https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200），**16:00 尾盤在央行調節與出口商拋匯下翻升收 32.942 元（升值 0.5 分）**，全日成交額 **22.63 億美元**（聯合報／鉅亨網／工商時報搜尋摘要；單篇直連網址於無頭環境未開啟）。
- 事實（金管會限空令 2.0）：金管會盤後宣布自 **11 月 20 日**起實施升級措施：（1）當日收盤價跌幅達 **3.5%** 以上之上市櫃及 TDR，次一交易日禁止低於前一日收盤價進行融券及借券放空（現券當沖未回補低於前收者亦不得改為融券／借券放空）；（2）每日盤中借券放空委託上限由前 30 日均量 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190182.aspx ，HTTP 200）。

### TW-2｜台積電 11/19 正式公告約 5 億美元入股 Anthropic 602.4 萬股；鴻海沙國 Ceer Motors 獲 6.93 億美元融資；熊本地震 JASM 無重大異狀（17:38 更新）
- 事實（台積電正式入股 Anthropic）：台積電於 **2026-11-19** 正式代子公司 **TSMC Partners** 公告，以每股 **83 美元**取得 Anthropic N 類普通股 **6,024,096 股**，總交易金額 **499,999,968 美元（約新台幣 164 億元，持股比例約 0.03%）**（鉅亨網／中央社／風傳媒 2026-11-19 搜尋摘要）。另中央社 11/19 引述智璞產業趨勢研究所分析，Anthropic 至 2045 年算力需求換算晶圓約 40–70 萬片，占台積電 CoWoS 年產出 1–2 成、前段晶圓 3%–6%，其直接向博通租賃 3.5 GW Google TPU 機櫃自建資料中心亦帶動**英業達、廣達、鴻海**受關注（https://www.cna.com.tw/news/afe/202611190156.aspx ，HTTP 200）。
- 事實（鴻海 Ceer Motors 融資）：鴻海與沙烏地主權基金（PIF）合資之電動車品牌 **Ceer Motors** 獲阿拉伯國民銀行及利雅德銀行等當地銀行團 **6.93 億美元（約新台幣 220 億元／26 億沙烏地里亞爾）** 融資，推進阿卜杜拉國王經濟城產線建置（CMoney / Yahoo 奇摩 2026-11-19 搜尋摘要）。
- 事實（其餘台鏈公告與熊本地震）：廣達田納西廠租約 1,490.8 萬美元（https://news.cnyes.com/news/id/6666244 ）、日月光仁武 2,489 億元動土（https://www.cna.com.tw/news/afe/202611190122.aspx ）、海龍 2A 綠電轉售台積電（https://www.cna.com.tw/news/afe/202611190102.aspx ）、鴻海 72.4 億日圓收購 Sony 車載相機事業（https://www.ctee.com.tw/news/20261119700316-439901 ）、偉詮電明年初漲價（https://www.cna.com.tw/news/afe/202611190036.aspx ）、元太資安公告（https://www.cna.com.tw/news/afe/202611180336.aspx ）均已確認；今日清晨熊本 M5.7 地震為 7/28 M7.1 強震之餘震，目前無台積電 JASM 廠重大停工或結構損壞回報（Japan Times / 新華社搜尋摘要）。
- 傳聞：外媒轉述《工商時報》稱台積電依客戶資產負債表設 AI 信用額度、超額須預付現金，尚未獲官方證實（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ）。

### TW-3｜蘋果洽談鎖定三星多年期 DRAM 長約；11/19 亞股收盤：日韓印收紅、陸港台收黑（17:38 補齊上證收盤）
- 事實：《The Korea Herald》11/19 報導指出，繼與 SK 海力士達成類似安排後，蘋果正進入與**三星電子**洽談多年期 DRAM 供應協議的最後階段（https://www.koreaherald.com/article/10942672 ，HTTP 200，原文為付費訂閱摘要）。11 月 19 日亞股收盤明顯分化：**日經 225 收漲 +0.71%（+419.93 點）至 59,444.21 點**、**韓國 KOSPI 收漲 +1.39%（+70.45 點）至 5,137.89 點**、**印度 Nifty 50 收漲 +0.91% 至 25,458.75 點**；**上證指數收跌 -0.28%（-10.21 點）至 3,577.62 點**、**香港恆生指數收跌 -1.95%（-453.13 點）至 22,841.62 點**（群益期貨／鉅亨網／Business Standard 搜尋摘要；單篇直連網址於無頭環境未開啟）。愛德萬 V93000 EXA Scale QX 測試系統與台韓出口數據保留（無新進展，https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ）。

---

### EARN-NTES｜網易（NTES）11/19 美股盤前公布 Q3 2026 財報，營收人民幣 279 億元（-1.8% YoY）低於預期，今晚 20:00 舉行法說（補充預期對照）
- 事實：網易（NTES）於 **2026-11-19 美股盤前**發布 Q3 2026 財報，淨營收人民幣 **279 億元**（約 42 億美元，年減 **1.8%**），**低於**華爾街共識預估約 **人民幣 295 億～303 億元**（約 45.2 億美元）；遊戲及相關增值服務淨營收人民幣 **229 億元**（-1.7% YoY）、有道人民幣 **14 億元**（-12.3% YoY）、網易雲音樂人民幣 **19 億元**（-0.9% YoY）、創新業務人民幣 **15 億元**（+7.1% YoY）；整體毛利人民幣 **190 億元**（+4.8% YoY）、Non-GAAP 淨利人民幣 **92 億元**（Non-GAAP 每 ADS 盈餘 **2.13 美元**亦低於共識），季股息調高至每 ADS **0.585 美元**；管理層提及《燕雲十六聲（Where Winds Meet）》玩家破 1 億人、新作《無限大（Ananta）》將於 2027-01-15 全球上線；電話會議訂於 **美東 11/19 07:00（台北 20:00）**（PR Newswire / 24/7 Wall St. / StreetInsider 搜尋摘要；受無頭環境限制，單篇重導向直連網址未開啟）。

### EARN-WMT｜沃爾瑪（WMT）Q3 FY27 財報（今晚美東 11/19 07:00／台北 20:00，無新進展）
- 事實：美東 **2026-11-19 07:00 財報、08:00 電話會議**（台北 **11/19 20:00／21:00**）；TradingView 彙整市場共識營收約 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售成長 3.0%–3.75%）；選擇權隱含波動 **±5.78%～±6.4%**（https://corporate.walmart.com/news/2026/11/Walmart-To-Host-Q3-Earnings-Call-Nov-19-2026 ，HTTP 200；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，HTTP 200）。

### EARN-BABA｜阿里巴巴（BABA）Q2 FY27 財報（今晚美東 11/19 盤前／台北 20:00 電話會議，無新進展）
- 事實：美東 **2026-11-19 盤前**公布（電話會議美東 07:00／台北 **20:00**，https://www.nasdaq.com/press-release/alibaba-group-will-announce-september-quarter-2026-results-november-19-2026-2026-11 ，HTTP 200）；Barchart 彙整預期營收約 **404.1 億～405.0 億美元**（年增約 8.9%–16%）、調整後 EPS 約 **1.56～1.71 美元**（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ，HTTP 200）。

### EARN-PDD｜拼多多（PDD）Q3 2026 財報（今晚美東 11/19 盤前／台北 20:30 電話會議，無新進展）
- 事實：美東 **2026-11-19 盤前**（電話會議 07:30 ET／台北 20:30）；TradingView 彙整共識營收約人民幣 **1,155 億～1,217 億元**（約 **171.7 億美元**）、EPS 約人民幣 **18.72～19.02 元**（約 **2.61～2.77 美元**）（https://www.tradingview.com/news/tradingview:8174655fed662:0-weekly-recap-pdd-q3-results-date-and-lower-analyst-price-target/ ，HTTP 200）。

### EARN-INTU / ROST / GAP / WSM｜今日（11/19）美東盤前與盤後其餘財報（無新進展）
- 事實：
  - **WSM（盤前／台北 11/19 20:00）**：共識營收 **19.8 億～20.0 億美元**、EPS **2.19 美元**（https://www.tradingview.com/news/tradingview:5796c7c550438:0-wsm-q3-26-earnings-eps-estimate-is-2-19-usd/ ，HTTP 200）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（原財測 2.44–2.48 美元），隱含波動 ±8.9%–10.5%（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ，HTTP 200）。
  - **ROST（盤後／台北 11/20 05:00）**：共識營收 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ，HTTP 200）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ，HTTP 200）。

### EARN-HPE / ZM / BBY / BURL / DKS / ADI / MDT / DELL / HPQ / ADSK / WDAY / BILI / DE｜11/23–11/25 財報（補充 BILI 共識）
- 事實：
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（公司財測 1.20–1.30；波動 ±9.7%，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ，HTTP 200）；**ZM** Zacks 共識營收 **12.8 億美元**、EPS **1.49 美元**（https://www.zacks.com/stock/news/3030700/zoom-communications-zm-falls-more-steeply-than-broader-market-what-investors-need-to-know ，HTTP 200）。
  - **11/24 盤前（台北 20:00–21:00）**：**BILI（嗶哩嗶哩）**（電話會議 07:00 ET／台北 20:00）MarketBeat 共識營收 **12.3 億美元**、EPS **0.23–0.27 美元**（Nasdaq / MarketBeat 搜尋摘要）；**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**（https://www.tradingview.com/news/tradingview:6917007d5e261:0-burl-q3-26-earnings-revenue-estimate-is-2-97b-usd/ ）；**DKS** 營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ）；**ADI** FactSet 共識營收 **43.2 億美元**、EPS **3.88 美元**（https://www.tradingview.com/news/tradingview:4441db86105da:0-adi-q4-26-earnings-revenue-estimate-is-4-32b-usd/ ）；**MDT** FactSet 共識營收 **94.8 億美元**、EPS **1.33 美元**（https://es.tradingview.com/news/tradingview:dcc2d0d8b8c99:0-mdt-q2-26-earnings-revenue-estimate-is-9-48b-usd/ ）；**BBY** Zacks 共識營收 **98.8 億美元**、EPS **1.48 美元**（https://www.zacks.com/stock/news/3031155/best-buy-bby-reports-next-week-wall-street-expects-earnings-growth ）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億～492.5 億美元**、EPS **6.41–6.60 美元**（波動 ±14.85%，https://www.tradingview.com/news/tradingview:e525c4bdcb809:0-dell-q3-26-earnings-revenue-estimate-is-49-25b-usd/ ）；**WDAY** 營收 **26.9 億美元**、EPS **2.75 美元**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ）；**HPQ** FactSet 共識營收 **154.3 億美元**、EPS **0.75 美元**（https://in.tradingview.com/news/tradingview:2627939d5b773:0-hpq-q4-26-earnings-revenue-estimate-is-15-43b-usd/ ）；**ADSK** MarketBeat 共識營收 **21.3 億美元**、EPS **3.07 美元**（https://www.marketbeat.com/instant-alerts/upcoming-autodesk-adsk-set-to-announce-quarterly-earnings-on-tuesday-2026-11-17/ ）。
  - **11/25 盤前（台北 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ）。
  - （備註：11/26–11/29 感恩節週暫無其他市值逾百億美元美股財報；12/01 盤後 **MRVL** 共識營收 **31.5 億～31.6 億美元**、Non-GAAP EPS **1.10 美元**，**OKTA** Zacks 共識營收 **8.155 億～8.162 億美元**、Non-GAAP EPS **0.93 美元**；12/02 盤後 **CRM** MarketBeat 共識營收 **114.6 億美元**、EPS **3.45 美元**，**SNOW** Zacks 共識營收 **16.5 億美元**、EPS **0.60 美元**；相關來源為 MarketBeat / Zacks / Okta / Salesforce 搜尋摘要，受無頭環境限制未開啟重導向直連網址。）

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ，HTTP 200）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（強烈偏升息，無新進展）
- 事實：Waller 於 11/18 受訪指出聯準會可能需要「shock people」壓抑 3% 通膨預期固著，12/8–9 會議應考慮一次升息 50 基點（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ，HTTP 200）。

### FED-3｜聯準會理事 Michael S. Barr（偏升息）、紐約聯準銀行總裁 John Williams（反對一次升息 2 碼）；今晚 Goolsbee 問答與理事會閉門貼現率會議（17:38 確認行程時間與地點）
- 事實：Barr 11/18 在紐約聯準銀行演說指出通膨仍過高、若經濟按預期演進適合進一步升息，並示警 AI 代理在市場壓力下自動調撥客戶資金之金融穩定風險（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ，HTTP 200）；Williams 舞台對談明確反對 12 月一次升息 0.50%（`"I don't see a need for dramatic action right now"`，偏漸進升息，https://www.chosun.com/english/market-money-en/20261119/3ZAB4T3MGVF4HLNUXPSHRHLNCI/ ，HTTP 200）。監管副主席 Bowman 與 Logan、Musalem 亦重申抑制通膨仍有工作要做（偏升息）。
- 事實（今日稍後行程確認）：芝加哥聯準銀行總裁 Austan Goolsbee 預計 **美東 2026-11-19 12:30（美中 11:30／台北 11/20 01:30）** 於印第安納經濟俱樂部（Economic Club of Indiana）參與座談問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ，HTTP 200）；聯準會理事會（不含地區總裁）於 **美東 2026-11-19 15:00（台北 11/20 04:00）** 召開閉門會議審議貼現率（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ，HTTP 200）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼達 90%–95%、升息 2 碼約 5%–10%（無新進展）
- 事實：聯邦基金期貨幾乎完全定價 12/9 升息 1 碼（各報導引述 CME FedWatch 介於 **90%–97%**），升息 2 碼約 **3%–10%**，暫停升息已完全被排除（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ，HTTP 200）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，HTTP 200 確認）。
- 事實：核心 PCE（3.1%）高於核心 CPI（2.6%）之結構主因，係 2026 年住房／房租通膨降溫拉低權重較大的 CPI，而醫療服務、金融與軟體科技服務權重在 PCE 籃子較高且價格較黏著（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，HTTP 200 確認）。

### TASK-B2｜11/19 台股收跌 1,768.02 點收 38,426.89 點（櫃買收 285.33 點、跌 7.22%）、外資現貨賣超 243.12 億、三大法人台指期合計淨空單 -8,883 口、新台幣收升至 32.942 元（17:38 補齊櫃買收盤點位與跌停數）
- 事實（11/19 收盤與三大法人現貨）：集中市場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，破年線）**，成交金額 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190149.aspx ，HTTP 200）；**櫃買指數收 285.33 點（-22.22 點 / -7.22%）**，上市櫃合計逾 **280 檔股票跌停**（Pocket / Goodinfo / 非凡新聞搜尋摘要）。證交所 `BFI82U` 與中央社公布：三大法人合計賣超 **461.03 億元**，其中 **外資及陸資賣超 243.12 億元**、**投信買超 15.13 億元**、**自營商合計賣超 233.03 億元**（https://www.cna.com.tw/news/afe/202611190200.aspx ，HTTP 200）。
- 事實（11/19 期交所三大法人台指期未平倉）：期交所 `futContractsDate` 公布 **臺股期貨三大法人合計淨空單為 -8,883 口**（外資淨空單 **-99,219 口**、投信淨多單 **+91,791 口**、自營商淨空單 **-1,455 口**）。
- 事實（11/19 新台幣 16:00 收盤價）：台北外匯市場開盤 32.960 元，盤中最高 32.920 元、最低貶破 33 元見 **33.040 元**（午盤暫收 32.988 元，https://www.cna.com.tw/news/afe/202611190098.aspx ，HTTP 200），**16:00 終場翻升收 32.942 元，較前日（32.947 元）升值 0.5 分**，成交 **22.63 億美元**（聯合報／鉅亨網搜尋摘要；單篇直連網址於無頭環境未開啟）。金管會並宣布 **11/20 起升級 3.5% 限空令**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ，HTTP 200）。

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；補充台積電 11/19 正式公告入股 602.4 萬股
- 事實：Anthropic（代號 **ANT**）定價 **每股 83.00 美元**（發行 9.8 億股、IPO 募資 **813.1 億美元**、加上晶片與雲端夥伴 260 億美元同步私募合計約 1,073 億美元、完全稀釋估值約 **1.5 兆美元**），將於 **美東 2026-11-19 09:30（台北 11/19 22:30）** 掛牌；截至台北時間 17:38（美東 04:38）美股尚未開盤，首日開盤價、收盤價與成交量將於明早 05:00 收盤後產生（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，HTTP 200；https://w.media/anthropic-ipo-priced-at-us-83-per-share-valuation-increases-to-us-1-5-trillion/ ，HTTP 200）。
- 事實：台積電 11/19 正式公告透過 TSMC Partners 以 **每股 83 美元**取得 Anthropic N 類普通股 **6,024,096 股**（499,999,968 美元，鉅亨網／中央社搜尋摘要）。掛牌前夕美東 11/18 收盤，**CoreWeave（CRWV）跌 4.13%、IREN 跌 3.61%、Nebius（NBIS）小漲 0.87%、Oracle（ORCL）大致持平**；同日 **NVDA 收跌約 2.9%**，**AVGO、AMD 上漲約 4%–5%**（https://247wallst.com/investing/2026/11/18/coreweave-falls-5-despite-nvidia-sticking-to-its-financing-commitments-nebius-dips-oracle-holds-steady/ ，HTTP 200）。

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字（無新進展）
- 事實：ECB 11/18《金融穩定評估》Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（基於 LSEG 10/26 共識），指多數美國超大規模雲端業者 2026 年自由現金流因 AI 資本支出大於營運現金流而轉負（表層 FCF 口徑未納入未起租的表外租賃；表外承諾逾 4 兆美元係於圖表 A 與註腳 6 依 ASC 842 單獨揭露）（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，HTTP 200）。
- 事實：四巨頭截至 2026-09-30 最新一季自報實際數字如下：Meta（Q3 2026）OCF $32.79B − CapEx（含融資租賃本金）$34.91B = **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）；Alphabet（Q3 2026）OCF $42.29B − 現金 PP&E $51.36B = **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）；Amazon（Q3 2026／TTM）Q3 單季 OCF $42.42B、淨現金 PP&E $75.93B（單季隱含 -$33.51B）、自報 **TTM FCF -$42.36B**（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）；Microsoft（Q1 FY27）OCF $58.02B − 現金 PP&E $39.37B = **+$18.6B（仍為正；計入新起租融資租賃總資本支出 $45.2B 後仍約 +$12.8B）**（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### TASK-B5｜WMT、BABA、PDD 今晚 20:00–21:00 才公布 11/19 財報；附上最新共識（含來源名稱）、上季指引與關稅／消費原話（無新進展）
- 事實：三家均為 **美東 11/19 盤前（台北時間今晚 11/19 20:00–21:00）** 公布，截至台北 17:38（美東 04:38）尚未發布實際財報。
- 事實（沃爾瑪 WMT，Q3 FY27）：TradingView 彙整市場共識營收 **1,872.5 億～1,873.8 億美元**、調整後 EPS **0.64 美元**（公司上季財測 EPS 0.62–0.64 美元、常數匯率淨銷售 +3.0%–3.75%）；執行長 John Furner 對關稅退稅與消費者壓力的原話為 `"Customers are feeling some pressure, so we're proud of our investments... We'll do everything we can to keep prices as low as we can for customers throughout the rest of the year."`（https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ；https://www.businessinsider.com/walmart-using-tariff-refund-price-cuts-customer-experience-sales-2026-8 ）。
- 事實（阿里巴巴 BABA，Q2 FY27）：Barchart 彙整共識營收約 **404.1 億～405.0 億美元**（年增約 8.9%–16%）、調整後 EPS **1.56～1.71 美元**，市場聚焦阿里雲 AI 資本支出與中國消費補貼戰（https://www.barchart.com/story/news/8897870/dear-alibaba-stock-fans-mark-your-calendars-for-november-19 ）。
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

### NEXT-1｜事件：台股櫃買暴跌 7.22% 收 285.33 點（逾 280 檔跌停）＋金管會 11/20 升級 3.5% 限空令＋自營商避險大砍 214 億＋台積電入股 Anthropic（更新）
- 推理：
  - 最先受影響的資產：今日上市櫃逾 280 檔跌停股與櫃買高融資中小型 AI 股（OTC -7.22% 遠重於集中市場 -4.40%）、台指期避險工具，以及明日跌幅 ≥3.5% 個股的平盤下流動性。
  - 傳導路徑：今日自營商賣超 233.03 億元中避險部位占 -214.40 億元，幾乎與外資（-243.12 億）並列最大賣壓，顯示權證與結構型產品在跌破年線時觸發系統性動態避險砍倉；而新台幣盤中雖貶破 33 元見 33.040 元，16:00 卻翻升收 32.942 元。金管會 11/20 起禁止當日跌 ≥3.5% 個股次日平盤下放空、並將盤中借券上限降至 1%（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ），同時 Anthropic 宣布以 83 美元掛牌、台積電正式入股 602.4 萬股且 Anthropic 轉向博通租賃 3.5 GW TPU 機櫃（https://www.cna.com.tw/news/afe/202611190156.aspx ）：
    - 美股：**AVGO、GOOGL、CRWV、NBIS、EQIX**。
    - 台股：**廣達 (2382)、英業達 (2356)、鴻海 (2317)、台積電 (2330)、聯發科 (2454)**。
  - 大家還沒注意到的間接受害者：**發行高價 AI 股認購權證的台灣中小型券商造市部門，以及面臨高維持率追繳的中小型電子股融資戶**——個股借券與平盤下放空受限後，券商自營避險只能擠向台指期（三大法人期貨淨空單已擴至 -8,883 口）或早盤直接砍現貨多單；且櫃買中小型股跌深若無買盤接手，反而容易因限空抽乾造市流動性而出現「無量鎖跌停」，放大違約交割後的券商呆帳風險（https://www.storm.mg/article/11182992 ）。

### NEXT-2｜事件：IEA 11/19 警告荷莫茲成「史上最大能源安全威脅」vs APEC 深圳「30 對 30 協議」＋川普「Blackwell 等 2 至 3 年＆黃仁勳關聯女子遭調查」（更新）
- 推理：
  - 最先受影響的資產：布蘭特原油遠月曲線與海運戰爭險費率、離岸人民幣（USD/CNH）、以及全球半導體設備／合規供應鏈股價。
  - 傳導路徑：IEA 11/19《2026 世界能源展望》警告荷莫茲海峽危機「讓 1970 年代石油危機相形見絀」，直接衝撞美中在深圳口頭宣示「確保能源通暢」的樂觀定價（https://www.cna.com.tw/news/aopl/202611193005.aspx ；https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ）；而川普同時點出 Blackwell 短期不放行且美國政府正在調查與黃仁勳有染女子是否涉及中國情報與晶片走私（https://www.cna.com.tw/news/aopl/202611193003.aspx ），代表貿易降稅不會換來先進算力鬆綁：
    - 美股：**NVDA、AMD、AVGO、FRO（Frontline）、STNG**。
    - 台股：**台積電 (2330)、聯發科 (2454)、長榮 (2603)、陽明 (2609)、台塑化 (6505)**。
  - 大家還沒注意到的間接受害者：**高度仰賴中國或東南亞中轉客戶、但缺乏「可信賴用戶」合規追蹤系統的二線 AI 伺服器與網通模組廠**——一旦美國調查延燒至實際走私節點，海關與出口稽核周期拉長將直接卡住營運資金週轉。

### NEXT-3｜事件：BOJ 植田鷹派談話＋ECB 拒替法國債市撐盤＋德國 IG Metall 罷工＋南非央行按兵不動＋印度氣旋 Akvan 明午登陸（更新）
- 推理：
  - 最先受影響的資產：USD/JPY、日本 10 年期公債、法德 10 年期公債利差、印度盧比（USD/INR）與歐洲汽車／銀行股。
  - 傳導路徑：植田和男今日在國會重申升息決心（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ），疊加 ECB 拒絕介入法國公債利差、德國 IG Metall 370 萬勞工系統罷工升溫、英國 CPI 3.6%、南非央行在 5.2% 通膨下仍被迫因景氣趨緩暫停於 7.25%，以及印度 CPI 6.09% 遇上明日中午登陸奧里薩邦的強氣旋「阿克萬」（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ；https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ），非美經濟體同步面臨「停滯性通膨＋政策兜底消失」雙重擠壓：
    - 美股：**EWJ、DXJ、INDA、EWQ（法國 ETF）、FDX**。
    - 台股：**華城 (1519)、中興電 (1513)、巨大 (9921)、豐泰 (9910)、中信金 (2891)**（受歐洲／印度消費與金融外幣債券波動影響）。
  - 大家還沒注意到的間接受益者：**美元貨幣市場基金與短天期美債（SGOV / BIL）**——當歐洲高負債國家失去央行兜底、日本準備升至 1.50%、南非與印度同受通膨與實體衝擊時，跨國資金最終只能回到無匯兌與長債利率風險的美元短端現金。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 已由 60% 降至 45%）」
- 最強反方證據：BEA 官方新聞稿已證實 9 月核心 PCE 年增確為 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ），The Conference Board 預估 10 月將升至 **3.3%**（https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026 ），且本站線上《財經日曆》卡片亦已載明 9 月為 `3.1%` 並自估 10 月為 `3.2%`。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法發布年增率，這題將成為「無法判定」；但只要有公布年增率，低於 3.0% 的空間極小。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：我維持落在 2.4%–3.0% 僅約 **30%**（比你修正後的 45% 低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露多數一線雲端商 FCF 轉負且表外承諾逾 4 兆美元、Oracle 據報未起租資料中心承諾達 2,880 億美元且信評降至 BBB-、ECB 點名法國公債利差走寬與避險基金槓桿平倉放大債市跌勢，IEA 11/19 警告荷莫茲構成史上最大能源安全威脅，加上台股櫃買跌 7.22%（285.33 點、逾 280 檔跌停）迫使金管會升級 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。
- 另一種同樣說得通的解釋：今日新台幣翻升收 32.942 元、日經（+0.71%）、韓股（+1.39%）、印度（+0.91%）收紅、歐股盤中微彈，顯示全球並非無差別拋售，壓力集中在高槓桿 AI 籌碼與高赤字歐洲主權債；就算美國垃圾債指數暫未破 4%，非美緊縮＋投資級科技債利差走寬仍足以構成「風險升級」。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：我維持「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你的 80% 低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：11/18 美國 EIA 原油庫存暴增 340 萬桶（至 4.178 億桶）、汽油暴增 520 萬桶，壓低 WTI 貼近 83 美元下緣；另一端 **IEA 11/19《2026 世界能源展望》**警告荷莫茲封鎖是「史上最大能源安全威脅（超越 1970 年代）」，UKMTO 證實 ADNOC 遇襲且伊朗稱 3 油輪觸雷（https://houseofsaud.com/iran-3-tankers-mines-hormuz-nov18/ ），使油價同時承受供給過剩向下拉扯與斷航向上跳空的雙尾風險。
- 另一種同樣說得通的解釋：庫存過剩與強美元容易把 WTI 壓破 80 美元，而實質水雷與封鎖升級則可能瞬間衝破 100 美元——也就是油價**突破 80–100 美元區間外的雙尾機率高於市場預期**。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **未來 72 小時荷莫茲海峽通航／掃雷動態**。
- 機率估計：我維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」（無新進展）
- 最強反方證據：中央社 11/19 引述《福斯新聞》報導川普親口指出，與黃仁勳有染的一名女子正遭美國政府調查是否為中國情報機構工作、以及是否協助走私晶片（https://www.cna.com.tw/news/aopl/202611193003.aspx ）；同日輝達董事長瓊斯對員工重申「黃仁勳個人行為及缺乏坦誠」是董事會接受辭呈且永不回鍋的原因（https://www.cna.com.tw/news/aopl/202611190029.aspx ）。
- 另一種同樣說得通的解釋：最初的確是「個人行為／缺乏坦誠」引發董事會 11/11 立即切割，但因牽涉對象本身被美方列為中國情報與晶片走私調查標的，**兩件事並非互斥，而是同一人物同時觸發公司治理與國安出口調查**；且台積電副總張曉強公開為輝達新團隊「站台」、輝達採購承諾增至 3,900 億美元，顯示公司本身目前尚未被列為制裁對象。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節，11 月下旬～12 月初）**與 **美國政府對該涉案女子／走私網絡之起訴或調查公告**。
- 機率估計：維持「單純私人治理、完全無涉中國晶片調查」**25%–30%**，「個人行為與中國晶片／情報調查兩線交織」**70%–75%**（建議 `dots_read.json` 把兩種說法從對立改成因果交織）。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（無新進展）
- 事實：ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**（已超過帳上負債），且投資級科技長債利差已相對於同評級企業債走寬（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q `Commitments and Contingencies / Uncommenced Leases` 追蹤，及 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜缺少「非公開交易 BDC 限額贖回（Gating）、私募信貸 SaaS 曝險與對沖基金主權債槓桿」監測（無新進展）
- 事實：金融穩定委員會（FSB）秘書長 John Schindler 演說（https://www.fsb.org/2026/10/innovation-and-resilience-managing-the-risks-of-a-changing-financial-system/ ，HTTP 200）、聯準會 FEDS Notes（2026-10-14）以及 IMF／BIS／ECB 2026 年最新金融穩定報告皆聚焦三大隱憂：（1）半流動性零售／非公開交易 BDC 在贖回潮下面臨限額贖回（gating）與實物付息（PIK）上升；（2）私募信貸高度集中於受 AI 衝擊的 SaaS 軟體借款人；（3）避險基金在歐洲主權債（特別是法國）與美債基差交易的高槓桿平倉風險。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜缺少「高集中度雲端／金融基建中斷與 SEC Item 1.05 資安事件」警報（無新進展）
- 推理：監測 SEC 8-K Item 1.05 是否涉及高集中度第三方基建（AWS、Azure、GCP、Cloudflare、DTCC），可比股價更早捕捉系統性中斷。免費資料源：CISA KEV JSON（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）＋ SEC EDGAR。

### BLIND-4｜「台股籌碼風向計」未自動加總「三大法人台指期合計淨口數」、且缺「每日違約交割金額」與「限空令燈號」（更新）
- 事實：前輪線上版確認頁面雖已列外資／投信／自營明細，但尚未加總 **「三大法人合計淨空單（11/18 -7,322 口 → 11/19 -8,883 口）」**，亦缺證交所／櫃買每日違約交割金額統計（11/18 爆 9 檔達標 4.269 億元）及今日盤後金管會升級 **3.5% 限空令** 狀態（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。免費資料源：期交所「三大法人區分各期貨契約交易資訊」、證交所 `BFI82U` 與「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」（無新進展）
- 推理：建議在「IPO 觀察」補上大型 IPO 納入 S&P 500、Nasdaq-100 指數時程與被動 ETF 權重排擠效應說明。

---

### SITE｜挑本站的錯（本地檔案 17:31 已重讀確認；線上網頁沿用 15:07／15:14／15:31 確認基準，本輪非 Hub 視窗環境無法開啟 `webview_browser`）

### SITE-1｜`research_feed/forecast.json` 仍寫「9 月核心 PCE 數字：查無」，但本站線上《財經日曆》PCE 卡片其實已顯示「核心 PCE 年增 3.1%」（17:31 重讀本地確認仍在）
- 本站寫了什麼：`research_feed/forecast.json` 第 130 行仍寫著 `9 月核心 PCE 數字：查無。`。
- 正確應該是什麼：本站線上《財經日曆》分頁之 `PCE 物價（聯準會最重視的通膨）` 卡片（15:07 版）已顯示 `核心 PCE 年增 3.1%` 與 `前值 0.3%`，完全符合 BEA 官網新聞稿（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）。建議將日曆卡片的前值管線串接至預測腳本。

### SITE-2｜`research_feed/macro_voice.json`（`2026-11-19 16:34 台北` 加班版）與 `research_feed/sessions.json`（11/18 盤後）仍寫 11/18 能源股與油價下跌「找不到原因」（17:31 重讀確認）
- 本站寫了什麼：`research_feed/macro_voice.json`（`2026-11-19 16:34 台北`）第 7 行寫道：`「能源這邊，我找不到時間對得上的原因。… 埃克森美孚和雪佛龍各跌約四趴。原因還不知道。」`（`research_feed/sessions.json` 第 30 行亦寫「結論：沒有找到時間對得上的消息」）。
- 正確應該是什麼：11/18 能源股與油價下挫有明確且時間對得上的公開事件：（1）美東 11/18 10:30（週三例行發布）美國 EIA 公布原油庫存大增 340 萬桶、汽油大增 520 萬桶，壓抑原油與能源板塊；（2）11/18 當天正是雪佛龍（CVX）**每股 1.78 美元季股息除息日**（https://www.moomoo.com/news/post/1004808924/chevron-to-go-ex-dividend-on-november-18th-2026-with ），除息即貢獻約 0.8 個百分點跌幅，還原息後實跌約 3.95%；（3）市場同步消化 CVX 近 50 億美元收購 Beacon Offshore Energy 之談判（https://www.bicmagazine.com/industry/investment-banking/chevron-closes-in-on-5b-beacon-deal/ ）。（另前期 `14:15 午班` 誤將 11/18 台幣收盤 32.947 當作 11/19 盤中狀態，目前已由 `16:34 加班版` 覆蓋。）

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

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆（更新：南非央行 11/19 已宣布維持 7.25% 不變，補充 11/20 印度氣旋登陸與 12/01–02 財報確認）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳峰會（川習會＋美中俄三方峰會）；**南非央行（SARB）已宣布基準利率維持 7.25% 不變**（Channel Africa 搜尋摘要）；美東盤前（台北 20:00–21:00）**WMT、BABA、PDD、WSM** 財報與 **NTES** 電話會議（20:00）；美東 09:30（台北 22:30）**Anthropic (ANT)、MapLight (MPLT)** 掛牌；美東 12:30（台北 11/20 01:30）芝加哥聯準銀行總裁 Goolsbee 於印第安納經濟俱樂部問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；美東 13:00（台北 11/20 02:00）**美債 10 年期 TIPS 增額標售 $19B**；美東 15:00（台北 11/20 04:00）聯準會理事會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP** 財報（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  2. **11/20（五）**：**台股金管會 3.5% 有條件限空令與盤中借券上限 1% 正式上路**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；**印度強氣旋「阿克萬」預計中午登陸奧里薩邦**；**台灣經濟部 10 月外銷訂單**（台北 16:00，預估 1,125–1,159 億美元，https://money.udn.com/money/story/10869/9879179 ）；**美股月選擇權到期（OPEX）**；**密大消費者信心指數終值**（美東 10:00／台北 23:00）；**SanDisk (SNDK) 1 拆 8 分割**。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM** 財報。
  5. **11/24（二）**：美東盤前（台北 20:00–21:00）**ADI、MDT、BBY、BURL、DKS、BILI**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY**。
  6. **11/25（三）**：美東盤前（台北 21:00）**DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與 10 月耐久財訂單；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**；台北 11/26 **宏于電機（台股）掛牌**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/28（六）**：**台灣 2026 九合一地方選舉投票日**。
  10. **11/29（日）**：**OPEC+ 聯合部長級監督委員會（JMMC）會議**。
  11. **11/30（一）**：**MSCI 季度調整台股收盤生效（台北 13:30）與月底資產再平衡**。
  12. **12/01（二）**：美東 10:00（台北 23:00）**ISM 製造業 PMI 與 10 月 JOLTS 職位空缺**；**CRWD、MRVL、OKTA、NTAP** 盤後財報（Okta / Earnings Watcher 搜尋摘要確認 12/01 盤後，受無頭環境限制未開啟重導向）；**韓國 11 月出口初值**。
  13. **12/02（三）**：美東盤後（台北 12/03 05:00）**CRM（Salesforce）、SNOW（Snowflake）、ZS（Zscaler）** 財報（ZS：https://www.tradingview.com/news/tradingview:c28752bb00e6f:0-zscaler-hosts-2026-investor-day-reaffirms-q1-and-fiscal-2027-guidance/ ，HTTP 200；CRM／SNOW 由 Salesforce / Snowflake 搜尋摘要確認 12/02 盤後）。
  14. **12/03（四）**：美國參議院資料中心聽證。
- 對照本站 11/19 15:07／15:14 線上版核對基準：
  - **正確部分**：已列出 WMT/BABA/PDD、ANT/MPLT、HPE、ADI、MDT、DELL、HPQ、DE、11/19 美債 10Y 增額 $19B、H.4.1、11/20 OPEX、11/25 GDP 與 PCE、11/30 月底再平衡、12/01 JOLTS，以及 11/26 休市與 11/27 半天交易。
  - **漏掉部分**：`upcoming.json` 漏掉 **INTU、ROST、GAP、ZM、BBY、BURL、DKS、ADSK、WDAY、BILI、MRVL、OKTA、CRM、SNOW**；`未來 14 天事件` 漏掉 **11/19 南非央行、11/20 台灣 10 月外銷訂單、11/21 韓國 20 日出口、11/25 聯準會褐皮書、11/26 韓國央行、11/28 台灣九合一選舉、11/29 OPEC+ JMMC 會議**，且未併註 **11/26–27 感恩節休市與半天交易**。

---

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets）— 掛牌前夕兩極拉鋸，擔憂內部人早期解禁賣壓與「茅草屋村開藍寶堅尼」（更新）
- 討論內容與情緒：r/wallstreetbets 今日（11/19）持續熱議 ANT 定價 83 美元、估值 1.5 兆美元，部分交易員押注掛牌初期流動性推升，但大量反方警告內部人早期解禁條款與「like opening up a Lambo dealership in a hut village」風險，多空情緒極度分歧（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ，HTTP 200；https://www.reddit.com/r/wallstreetbets/comments/1xtuclv/nasdaq_confirms_anthropics_shares_will_begin/ ，HTTP 200）。

### SENT-2｜NVDA 與沃爾瑪（WMT）財報（r/wallstreetbets）— 熱議 NVDA 是逢低接還是接刀，並盯緊今晚 WMT 消費風向（更新）
- 討論內容與情緒：r/wallstreetbets 今日串與本週財報總串熱議 NVDA 黃仁勳離任、多家機構下修看法（如 Melius 看法 $185）後的選擇權 BanBets，並將焦點轉向今晚盤前公布的 WMT 財報是否揭示美國底層消費真實健康度（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ，HTTP 200）。

### SENT-3｜PANW／科技股財報（r/stocks）— 肯定資安與 AI 儲存動能但對軟體股估值審慎（無新進展）
- 討論內容與情緒：r/stocks 討論串肯定 PANW 平台化與 NGS ARR 成長，但整體對升息與 AI 高資本支出下的軟體股本益比仍偏審慎（熱度自 11/18 升溫；情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-4｜UNH／管理式醫療（r/stocks）— CMS CRUSH 規則衝擊下偏悲觀觀望（無新進展）
- 討論內容與情緒：UNH 等醫療保險股受 CMS CRUSH 反詐欺規則影響連日承壓，散戶偏悲觀（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-5｜台股 11/19 跌 1,768 點與盤後「限空令 2.0」（PTT 股板）— 熱議逾 280 檔跌停、大摩台積電 3,088 元看法與《FX 戰士久留美》迷因（17:38 更新）
- 討論內容與情緒：今日台股收跌 1,768.02 點（櫃買跌 7.22% 收 285.33 點）、上市櫃逾 280 檔跌停，盤後金管會緊急宣布 11/20 起實施 3.5% 有條件限空令與借券上限降至 1%；PTT 股板盤中對斷頭與違約交割恐慌，並以動畫《FX 戰士久留美》播出日暴跌自嘲，盤後兩極爭論限空令 2.0 是止血訊號還是反而抽乾中小型股流動性，同步討論大摩對台積電 3,088 元看法與台幣尾盤逆轉收升 32.942 元（情緒，非事實；https://www.pttweb.cc/bbs/Stock/M.1795048218.A.865 ，HTTP 200；https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ，HTTP 200；https://www.pttweb.cc/bbs/Stock/M.1795058772.A.5C2 ，HTTP 200）。

---

### CODE-1｜wsb/analytics/breaking.py：第 52 與 80 行 `str(x.get("asof", "")) < cut` 遇 `asof` 為 `None` 時會把 `"None"` 當成最新報價通過過期檢查
- 檔案路徑與行號：`wsb/analytics/breaking.py` 第 52 與 80 行（`hits()` 與 `events()` 函式），連動 `wsb/data/market.py` 第 376–387 行（`q()` 函式）。
- 那一行在做什麼：檢查即時報價的日期 `asof` 是否早於 `cut`（2 天前），避免拿過期行情觸發「緊急加班車」口播。
- 為什麼有問題：如果 `x` 這個 dict 裡 `"asof"` 鍵存在但值為 `None`，`x.get("asof", "")` 會回傳 `None` 而非 `""`，`str(None)` 變成字串 `"None"`。在 Python 字串比較中，`'N'` 的字碼大於 `'2'`，所以 `"None" < "2026-11-17"` 結果為 **`False`**，反而通過了過期檢查（同時 `wsb/data/market.py` 第 383 行 `str(qt.get("asof", ""))[:10] < last_d` 亦因 `"None" < "2026-..."` 為 `False` 而未用歷史收盤補齊）。結果可能讓缺日期的異常報價被當成最新異動發車。
- 建議怎麼改：在 `breaking.py` 第 52、80 行與 `market.py` 第 383、387 行改為 `str(x.get("asof") or "") < cut`（以及明確過濾 `not x.get("asof")` 時略過）。
- 確定度：高。

### CODE-2｜wsb/analytics/tw_etf.py：第 136 與 181 行在 UTC 建置環境用 `date.today()` 過濾台灣除息日，台北 00:00–07:59 建置會把昨日已除息 ETF 留在「未來 45 天」
- 檔案路徑與行號：`wsb/analytics/tw_etf.py` 第 136 與 181 行（`build()` 函式），對照第 20–27 行（`_day_zh()` 函式）。
- 那一行在做什麼：決定 `today` 基準日，並從證交所除息預告表 `d.get("exdiv")` 篩出未來 45 天內除息的台灣 ETF。
- 為什麼有問題：第 26 行 `_day_zh()` 正確使用 `datetime.now(ZoneInfo("Asia/Taipei")).date()` 取台北日期，但 `build()` 第 136 行未傳入 `today`（`tools/site_tw_etf.py` 呼叫 `E.build(eng)` 時無參數）而退回系統 `date.today()`。在 UTC 時區的 GitHub Actions 建置主機上，台北時間每天 00:00–07:59（即 UTC 前一日 16:00–23:59）`date.today()` 會慢台北一天，導致第 181 行 `today.isoformat() <= x["date"]` 把「台灣昨天已經除息」的 ETF 繼續列在未來 45 天清單裡。
- 建議怎麼改：將第 136 行預設日期改為 `today = today or datetime.now(ZoneInfo("Asia/Taipei")).date()`（第 23–24 行的 `datetime` 與 `ZoneInfo` 可移到模組頂層共用）。
- 確定度：高。

### CODE-3｜tools/site_after.py：第 127 與 176 行對「美股與台港股涵蓋範圍」說明互相矛盾
- 檔案路徑與行號：`tools/site_after.py` 第 126–127 行（`_card()`）與第 176 行（`sec_earn_all()`）。
- 那一行在做什麼：向網站使用者說明「財報後白話解讀」與「財報解讀總表」兩張卡片分別涵蓋哪些公司。
- 為什麼有問題：第 127 行寫範圍是「美股市值 **200 億美元**以上、台股市值**前 150 大**、港股成交額**前 100 大**」，但同一檔案第 176 行寫「範圍是美股市值 **20 億美元**以上，以及台股、港股**全部上市公司**，還在陸續補寫」。新手看到同一分頁上兩張相鄰卡片寫出相差 10 倍的門檻（200 億 vs 20 億；前 150 大 vs 全部上市），會搞不清楚到底哪些公司有收錄。
- 建議怎麼改：第 176 行改為明確區分每日清單與回補清單，例如「每日解讀為美股 200 億美元以上、台股前 150 大、港股前 100 大；總表正陸續回補至美股 20 億美元以上及台股、港股其餘公司」。
- 確定度：中（屬說明文字落差，不影響數值運算）。

（備註：本小時批次 `i % 24 == 17` 共 12 檔：`tools/site_after.py`、`tools/site_etf_flows.py`、`tools/site_macro_dash.py`、`tools/site_tw_etf.py`、`wsb/analytics/breaking.py`、`wsb/analytics/focus.py`、`wsb/analytics/private_credit.py`、`wsb/analytics/tw_etf.py`、`wsb/data/china_watch.py`、`wsb/data/finra.py`、`wsb/data/nowcast.py`、`wsb/data/tw_futures.py` 皆已逐行讀完；其中 `wsb/data/nowcast.py` 第 44 行確認由 `wsb/data/freshness.py` `due()` 預先初始化，無 `KeyError` 風險；`tools/site_macro_dash.py` 第 39 行 `len(s) > 6` 取 `iloc[-6]` 僅少算 1 天極端樣本不濫報。）

---

其他今天的大事：
- 台股 11/19 收盤重挫 **1,768.02 點（-4.40%）至 38,426.89 點**、櫃買指數收跌 **-7.22% 至 285.33 點**（上市櫃逾 280 檔跌停），三大法人賣超 **461.03 億元（外資 -243.12 億、自營商 -233.03 億、投信 +15.13 億）**，期貨合計淨空單 **-8,883 口**；金管會盤後宣布自 **11/20 起升級 3.5% 限空令**；新台幣 16:00 翻升收 **32.942 元（升值 0.5 分）**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190200.aspx ；https://www.cna.com.tw/news/afe/202611190149.aspx ；櫃買與匯市收盤見 Pocket / 聯合報搜尋摘要）。
- 台積電 11/19 正式公告透過子公司 TSMC Partners 以 **每股 83 美元**取得 Anthropic N 類普通股 **6,024,096 股**（約 **5 億美元**）；鴻海沙烏地合資電動車品牌 Ceer Motors 獲當地銀行團 **6.93 億美元（約新台幣 220 億元）** 融資（鉅亨網／CMoney 搜尋摘要）。
- **國際能源總署（IEA）11/19 發布《2026 世界能源展望》**，警告美以伊衝突與荷莫茲海峽封鎖造成「史上最大能源安全威脅（超越 1970 年代）」；同日**南非央行（SARB）維持基準利率 7.25% 不變**（Channel NewsAsia / Channel Africa 搜尋摘要）。
- 亞歐股市 11/19 分化：日經 +0.71%（59,444.21）、KOSPI +1.39%（5,137.89）、印度 Nifty 50 +0.91%（25,458.75）；上證 -0.28%（3,577.62）、恆生 -1.95%（22,841.62）；歐股盤中微彈（DAX +0.5%～0.6%、CAC 40 +0.4%～0.8%），但德國 IG Metall 罷工持續且法國 10Y OAT 殖利率維持約 4.87%（搜尋摘要）。
- 網易（NTES）11/19 盤前公布 Q3 2026 營收人民幣 279 億元（-1.8% YoY）低於預期、Non-GAAP 每 ADS 盈餘 2.13 美元；今晚 20:00–22:30 沃爾瑪（WMT）、阿里巴巴（BABA）、拼多多（PDD）將陸續公布財報，且 Anthropic（ANT，定價 83 美元）於美東 09:30（台北 22:30）納斯達克掛牌（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://www.nasdaq.com/press-release/alibaba-group-will-announce-september-quarter-2026-results-november-19-2026-2026-11 ）。

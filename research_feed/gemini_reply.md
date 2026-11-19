台北時間 2026-11-19 20:37

### D-1｜回應 Q1：BEA 9 月核心 PCE 年增率確為 3.1%（附 bea.gov 原文那一句），以及為何高於核心 CPI 的 2.6%（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出（Personal Income and Outlays, September 2026）》官方新聞稿（2026 年 10 月 29 日發布）明確寫道核心 PCE 年增率確為 **3.1%**（月增 **0.3%**）、整體 PCE 年增率為 **3.6%**（月增 **0.5%**），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ，台北時間 2026-10-29，前輪確認）。
- 事實：之所以 9 月核心 PCE（3.1%）反過來高於核心 CPI（2.6%），根據 KBC Economics 對美國 CPI 與 PCE 分歧結構之研究報告，當「居住／房租（Shelter）」通膨降溫、而「醫療照護服務、金融服務與軟體／科技相關服務」價格較黏著時，因 **居住成本在 CPI 籃子權重遠高於 PCE**、且 **PCE 涵蓋雇主與政府代付的醫療支出且醫療／金融服務權重遠高於 CPI**，就會出現核心 PCE 高於核心 CPI 的倒掛現象（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ，前輪確認）。
- 事實：本地 `research_feed/forecast.json` 第 130 行截至 20:30 重讀仍寫 `9 月核心 PCE 數字：查無。`，與 BEA 官方新聞稿及線上《財經日曆》PCE 卡片顯示的前值不符。
- 推理：在 9 月實際值已達 **3.1%**、且本站模型與 The Conference Board（估 10 月核心 PCE 年增 **3.3%**）都落在 **3.2%–3.3%** 的情況下，10 月核心 PCE 跌回 2.4%–3.0% 的唯一合理路徑只剩「2025 年 10 月政府停擺導致 BEA 出現資料缺口或基期異常」。因此我維持對 `2.4%–3.0%` 約 **30%** 機率的評估，比你下修後的 **45%** 低 15 個百分點，等 11/25 21:30 揭曉。

### D-2｜回應 Q2：ECB 11/18 報告點名的科技巨頭、租賃口徑，與 MSFT／GOOGL／AMZN／META 最新一季 FCF 實算對照（無新進展）
- 事實：歐洲央行（ECB）2026 年 11 月《金融穩定評估》Box 3（"The debt financing of AI and its implications for financial stability"）明確列出美國大型科技／雲端與 AI 樣本公司為 **Alphabet (GOOG)、Amazon (AMZN)、Meta (META)、Microsoft (MSFT)、Oracle (ORCL)**（外加 NVDA、AVGO 與 Anthropic），資本支出預估採用 2026 年 10 月 26 日 LSEG Data & Analytics 共識（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，台北時間 2026-11-18，前輪確認）。
- 事實：ECB Box 3 正文對自由現金流的口徑為 `"free cash flows turned negative for most US hyperscalers in 2026, as capital expenditure on AI infrastructure exceeded operating cash flows"`（僅以**資本支出超過營運現金流**作為表層口徑，未把尚未起租的表外租賃算進單季現金流）；同時於圖表 A 與註腳 6 依美國會計準則 **ASC 842** 單獨指出，已簽約但資產尚未投入使用的租賃與算力承諾在起租前不計入資產負債表負債，這類表外承諾合計已逾 **4 兆美元**（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ，前輪確認）。
- 事實：四家雲端巨頭截至 2026 年 9 月 30 日止最新一季自報數據與租賃口徑落差如下：
  - Meta（Q3 2026）：營運現金流 **$32.79B**，資本支出（含融資租賃本金償還）**$34.91B**，自報自由現金流為 **-$2.12B（轉負）**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ，前輪已讀）。
  - Alphabet（Q3 2026）：營運現金流 **$42.29B**（$42,290M），現金 PP&E 購置（不含融資租賃）**$51.36B**（$51,355M），自報自由現金流為 **-$9.07B（-$9,065M，轉負，含 52 億美元歐盟罰款支付）**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ，前輪已讀）。
  - Amazon（Q3 2026／TTM）：單季營運現金流 **$42.42B**、單季淨 PP&E 購置 **$75.93B**（隱含單季 **-$33.51B**），公司自報 **TTM 自由現金流 -$42.36B（-$42,357M，轉負）**，該口徑僅扣現金淨 PP&E、未扣額外揭露之新簽融資租賃資產（Q3 單季 $1.47B）（https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ，前輪已讀）。
  - Microsoft（Q1 FY27）：營運現金流 **$58.02B**，現金 PP&E 資本支出 **$39.37B**，自報自由現金流為 **+$18.6B（仍為正值，年減 27%）**；若計入新起租之融資租賃，總資本支出達 **$45.2B**，扣除後仍餘約 +$12.8B，印證 ECB 精準寫 `"most"` 而非全部（https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ，伺服器回傳 HTTP 403，維持前輪已讀數字）。

### D-3｜回應 Q3：除了逐字稿與共識外，Claude 這三輪最常「下太快」的兩類判斷（20:37 補實 `macro_voice.json` 20:01 晚班實例與 WMT 已公布時間差）
- 推理：檢視 `research_feed/claude_notes.md`、`research_feed/forecast.json`、`tools/site_events.py`，以及剛於 **`2026-11-19 20:01 台北` 更新的 `research_feed/macro_voice.json`（晚班版）**，最常「下太快」的是以下兩種思考捷徑：
  1. **用「單一經驗法則或單一指標」直接否決或替換缺值**：例如 `claude_notes.md` 第 14 行在還沒核對 `bea.gov` 或本站日曆卡片前值的情況下，因為「核心 PCE 通常比核心 CPI 低」，就直接對 `9 月核心 PCE 3.1%` 存疑並拿 `核心 CPI 2.6%` 去推 10 月區間；以及 `forecast.json` 第 65–73 行先前曾用單一 `BAMLH0A0HYM2`（3.43%）得出「信用市場還沒出現壓力」（第 3 輪你已修正）。
  2. **把「預估時間表／關鍵字比對不到」直接當成「還沒公布／找不到原因」**：最新 `macro_voice.json`（`2026-11-19 20:01 台北 晚班`）仍有三處時間與數據落差——（a）仍寫台股跌 4.4%「我手上沒有時間對得上的單一消息」，忽略盤後已公開的自營商避險大賣 **214.40 億元**、世界／台化／萬泰科合計 **1.29 億元**違約交割與金管會 **1,028 檔 3.5% 限空令 2.0**；（b）於 `20:01` 仍播報「今晚九點，沃爾瑪、阿里巴巴、拼多多先公布財報」，主因 `tools/site_events.py` 第 48 行把所有盤前財報一律寫死成美東 `08:00`（台北 `21:00`），但實際上 **BABA（18:18 前）、PDD（19:30）、WMT（20:00／美東 07:00）在晚班語音更新前皆已公布**；（c）晚班稿稱「布蘭特原油今天只小跌，大約八十九美元」，但 11/19 市場報價 Brent 實為 **$91.52–$91.89**（WTI 約 **$82.70–$83.42**），疑似把 WTI／舊價與 Brent 混用或來源延遲。

### D-4｜回應 Q4：若 Anthropic（ANT）今晚收在發行價 83 美元以下，受影響先後順序與隔天可驗證指標（20:37 補充 BABA／PDD／NTES／WMT 盤前分化實例）
- 事實：中央社 11/19 16:46 報導，台積電正式代子公司 TSMC Partners 公告以 **每股 83 美元**取得 Anthropic 普通股 **6,024,096 股**，總金額約 **5 億美元**（持股約 0.03%，https://www.cna.com.tw/news/afe/202611190254.aspx ，前輪確認）。同日已公布的跨市場財報已呈現高度分化：**BABA** 因單季 CapEx 飆升 60% 至 504.77 億人民幣、FCF 淨流出 **344.72 億元**且庫藏股節奏明顯縮水，ADR 盤前小跌約 0.1%–2%；**NTES** 因遊戲與總營收雙遜預期盤前跌 **3.5%–5%**；反之 **PDD** 因縮減行銷費用使 Non-GAAP EPADS 達 **3.14 美元**（21.04 元人民幣）大幅優於預期，盤前大漲約 **8%–9%**；**WMT** 於 20:00 公布 Q3 FY27 營收 **1,888 億美元**、調整後 EPS **0.65 美元**雙雙優於預期且上調全年展望，但因股價位於 52 週高檔，盤前反而小跌約 **0.7%**（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEv5D9SHWgSJPD25VEcgTMjOkoM-E7Sl4DvydrU_hFxstnwdsog9PAHg-4N70oOmCu9hc3gDxeO73xjsWCRzNaJ7QxPH9V97qf4huNHPSsg7u5X5wAxAQdflOS3CpHQE1E4ZESHsZNONprBgNLYl8eDO2ovnMf1E_VS1hXruMoC-F4IJXCLn-ISJSu33PAzjjfXZ2aDSJ3bN67xMVxzt0J2r6E= ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGi9WbWnHfgovNAEvdidfhsjIYTHLk1VwYozA8O0_bIxp-h93Sv7GvQoDQruA2wDp57-QZnGBD7Gq4FJdg4BIQkKThGoIAoMM0UwzucTYuR3TWf7Kh_F2ZOlSGjZe3Xw4TMu-CbBzOdQP9B7OvA_t7-MWlkWwnMKBf4OSBrEOhyI0WUoqTUDvWGX1Na1OLlbSRV8Fe7cizO7qo0Vtgd ，搜尋跳轉原文，2026-11-19）。
- 推理：這印證市場同時極度檢視「CapEx 燒錢速度」與「高期望值下的定價是否透支」。若今晚（台北 11/19 22:30 開盤）ANT 首日收在 **83 美元以下（破發）**，傳導先後順序維持如下：
  1. **最先受重擊：新雲端（CRWV、NBIS、IREN）**：負債比高、高度仰賴大模型算力長約抵押融資，且 Anthropic 轉向透過博通租賃 3.5 GW Google TPU 機櫃自建資料中心（https://www.cna.com.tw/news/afe/202611190156.aspx ），直接稀釋第三方租賃溢價。隔天（11/20）可驗證指標：`CRWV`、`NBIS` 相對 `QQQ` 的開盤超額跌幅，及新雲端無擔保債二級殖利率走勢。
  2. **其次受傷：其他待上市 AI 公司與晚期創投／私募信貸**：ANT 公開發行募資約 813 億美元（含 260 億美元同步私募合計約 1,073 億美元）、完全稀釋估值約 1.5 兆美元，若破發將壓縮 OpenAI 與晚期 AI 獨角獸 IPO 窗口。隔天可驗證指標：`ARCC`、`BIZD`、`BX`、`APO` 股價與承銷商護盤（stabilizing bid）報導。
  3. **最後且分化：晶片與機櫃合作夥伴（NVDA、AVGO、GOOGL、AMZN、MSFT、MU、台積電等同步私募出資方）**：主要承受公允價值重估回吐，但 Anthropic 轉向自建反而讓博通與 TPU 機櫃組裝廠受關注。隔天可驗證指標：`AVGO`／`NVDA` 相對 `^SOX` 強弱與次日選擇權隱含波動率（IV）變化。

### D-5｜對 Claude 第 3 輪五條主線的逐一表態（20:37 更新 WMT 消費數據、荷莫茲油輪觸雷與 Equinor 網攻）
- 推理：
  1. **主線 1（AI 錢在集中，一線開始發債補缺口但未成信用事件）— 同意且續獲跨市場驗證**：ECB Box 3 佐證多家美系雲端商 FCF 轉負、表外承諾逾 4 兆美元；今日 **BABA** Q2 FY27 單季 CapEx 飆升 60% 至 504.77 億人民幣、FCF 淨流出 **344.72 億人民幣**且美股庫藏股急縮（Q2 約 2.21 億美元，見 https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGllO4TArmJg2Thc9zn8oymnfT4EoU1fxaq0Flcl3a5za3t4Rn-o7wb4mvwoTP0knvR4b5vrkkucD--iO846q_TwsK4yP6UHsnoW-eu7wACT7mjSLFHiJNM1atcotRZ6mmgNOpltcHciqhLDfRnSbK0e5het5MJu753DmOa06FMbHhxiSRCSxbvH7mCqLCQGHCkB8E7 ），同時 **PDD** 靠砍行銷費用達成獲利超預期但營收持平（1,083 億）。市場對「燒錢換成長」的容忍度明顯下降。
  2. **主線 2（輝達治理風波 vs 出口調查）— 部分同意，兩條線已證實交織且台積電高層赴美穩鏈**：中央社引述《福斯新聞》專訪指涉案女子同受中國情報與晶片走私調查（https://www.cna.com.tw/news/aopl/202611193003.aspx ），《工商時報》亦證實台積電資深副總張曉強親赴輝達美國總部固鏈、Vera Rubin NVL72 與 Vera CPU 已於 Q3 進入量產出貨（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGan4RU7Fxg92JH7sELWAiA8faXWxOV9fehZY2xB-1upXsCXxwxDndm-su7F8syV2plZ6gIptSrtYA_Zuuh63lIXyOn7_jP0nWrd-DgoiVYRvIKeCW6NWlfbGBHRe6cWRAb_KuQ3e4WFg== ）。建議第 4 輪整併為「個人治理與國安調查同源交織，但硬體供應鏈尚未鬆動」。
  3. **主線 3（利率是主壓力，11/25 PCE 是關鍵）— 部分同意，補充 WMT 消費韌性**：剛公布的 **WMT Q3 FY27** 營收 **1,888 億美元（+5.2% YoY）**、美國同店銷售 **+2.9%** 並上調全年 EPS 指引至 **$2.84–$2.89**，顯示美國必需消費與市占集中度仍強，並未出現衰退失速，反而讓聯準會更沒有理由在 12/9 放緩升息步調。
  4. **主線 4（WTI 80–100 美元 62% vs 55%）— 部分同意，荷莫茲油輪觸雷 vs 美中俄增供精煉油品**：最新報導顯示荷莫茲海峽東側接連傳出油輪觸及水雷受損／起火、IEA 警告波灣就算斥資 400 億美元建 700 萬桶/日繞道管線仍難免遭襲，Brent 維持在 **$91.52–$91.89**（WTI 約 **$82.70–$83.42**）；與美中俄深圳《四點和平宣言》增供精煉油品共識及 EIA 累庫雙向拉扯，維持 **55%**。
  5. **主線 5（「風險升級」劇本 33% vs 40%）— 同意方向一致**，差距 7 個百分點。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題（20:37 更新）
- 1. 最新 `research_feed/macro_voice.json`（`20:01 台北 晚班`）仍說「今晚九點，沃爾瑪、阿里巴巴、拼多多先公布財報」，但三家全在 20:00 前已公布（BABA <18:18、PDD 19:30、WMT 20:00），根因是 `tools/site_events.py` 第 48 行把盤前時間一律估成 `08:00 ET（21:00 台北）`；且晚班稿稱「布蘭特原油約 89 美元」（今日 Brent 實為 $91.5–$91.9）。請問要怎麼修 `site_events.py` 的預設時間提示與語音稿的盤前／油價對帳？
- 2. 我在外部查證發現 `MapLight (MPLT)` 其實已在 **2025 年 10 月 27 日**完成 IPO（$17／股），並非 2026 年 11 月 19 日掛牌；請問 `upcoming.json` 之前為什麼會出現 `MPLT`？是不是 `wsb/data/ipo_data.py` 的 SEC 申報過濾抓到了 2026 年的常規會議或後續申報？
- 3. 今日（11/19）**WMT** 營收與獲利雙雙優於預期並上調全年展望、**PDD** 靠砍行銷費用使獲利大勝預期（盤前 +8%～9%），但 **BABA** FCF 轉負大失血且 **NTES** 營收獲利雙遜（盤前 -3.5%～5%）。在「美國消費仍撐得住＋AI 燒錢大廠遭懲罰」下，第 4 輪你是否要調整 `forecast.json`「消費與進口商品轉弱」與「偏鷹沒出事（53%）」的權重？

---

### WIDE-1｜荷莫茲海峽東側接連傳出油輪觸水雷受損＋IEA 警告 400 億美元繞道管線仍難避地緣瓶頸＋胡塞碎片擊中沙國 PIF 總部（20:37 更新油輪觸雷與繞道管線報告）
- 事實：外電與伊朗媒體 11/19 報導，近期荷莫茲海峽東側接連發生多起商船／油輪疑似觸及水雷致失去動力或起火事件（含大型油輪，阿聯 ADNOC 亦通報旗下船隻遇襲致船員受傷失蹤）；美軍中央司令部（CENTCOM）則強調持續掃雷與護航（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGKcxschqLO_aBH1Y663AJw-8itcWBqmGG7dnJwML-tPK9WAwIE-ZrtOpHVociZdP4Mh8pnkzlIZ694izJCN1DCUEosYJYkPPs9cl_MoVwI6QCIvpIkeBFyog== ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGJRVjXNTqCPzupUpwQQXbtOA9arpzeWXrIFyW14NHaK2hJsFMIVwt6JB_m-xx7ydi0MLEDvFDE6jyN4PCDIEOAQLRmy8Vs8XuvRXW-ipM153YtiSkiL9ze8ec07waZPwk9jcscjfEy4TlMigXF3pMWRQkacUHeo8XqtNibdo2rKvrgdz2Reae_mf3sFaXqOjeU3IAA8yjY4nQAb9bULETOIVND6drtDzlc ，搜尋跳轉原文，2026-11-19）。同日 IEA 於《2026 世界能源展望》另警告荷莫茲已累計中斷 **28 億桶原油與 600 億立方公尺天然氣**，且就算波灣產油國斥資 **400 億美元**興建日運量 700 萬桶的繞道輸油管線，替代路線仍高度暴露於飛彈與無人機襲擊風險中（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHX9HFpMharw9rO0wyNfmWCuMhx-OyTB3wE2ax8SYUEv_De0K8vioMyxPnx9iBH8PIjpicQjRZLUUjD_m2QNBU48r6PUdcbEM3Ah7P__uIENpfwsd5Og3JGlE0q3luHd2SvIrWP0eml2HhYD4VOzWpXWu_60lBNC4iahZ5lA-ABXUxnyddAA-KGhM4lEQbCFAWT5XLC0RT0z74t-k2uLovMui0seSSF-fd9mVg0D29XzeI4lwIB0-FW ；https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ）。11/19 同日下午胡塞飛彈攔截碎片亦損及利雅德沙國主權基金（PIF）80 層總部大樓（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ）。
- 推理：美股焦點停在昨日 EIA 庫存增加，忽視了「海峽水雷化」與「繞道管線亦不安全」對遠期能源風險溢價與波灣金融中心的衝擊。
- 先影響資產：布蘭特原油（11/19 約 $91.52–$91.89）遠月價差、油輪運價與戰爭險保費、波灣主權債 CDS。

### WIDE-2｜挪威國營能源巨頭 Equinor 證實遭持續網攻（企業郵件／IT 系統中斷），疊加歐盟執委會遭 AI 工具 ARTEX 網攻 10 天（20:37 新增 Equinor 網攻）
- 事實：挪威國營油氣巨頭 **Equinor**（歐洲最大天然氣與原油供應商之一）證實內部 IT 系統與企業郵件服務正遭受持續性網路攻擊並通報挪威國家安全局（NSM）與海洋工業監管局（Havtil），目前油氣生產與對歐天然氣出口未受影響、亦未發現電腦病毒擴散或資料外洩，但全面復原仍需時間；此前 NSM 已於 10 月將挪威全國網安威脅等級調升至「高」（第 4 級／共 5 級）（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGHIVOHTVrQOSgyriBlDVJ3CZLWZ9JPBY47XFqwoSkiZ8ofWHJ6fsgUb4inWqk4kE9j9oGWap5_ed8apGkb1hgHbn8hYiIMfe8Zbj_xUHOYtHAaV28m4QCkpCJw8l9TXxqgyFIErvG63ugYyo5sBFFvwcI8Wq2OjwObCWkoWkP--y0t0XM6dVOeVcRQuA== ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEMD6cnk3-iPXxsQjM3yhP7R7t_7w8jvayVnjw0Xzo2f4EwcUHAfL6Q33eDeHO8yJljVOa8yctAseQr-HXrkfTGwqOBtMVhvnO4zK__XIjhIb6wps_aC_df-GyVto23WuqzaaHSjA8sNd3it7M7pGk= ，搜尋跳轉原文，2026-11-19）。同日歐盟執委會亦證實遭開源 AI 滲透工具 **ARTEX** 攻擊致內部人資 Sysper 與醫療報銷 MyPMO 系統離線約 10 天（https://mlq.ai/news/european-commission-says-hackers-targeted-some-of-its-systems-as-pay-and-leave-tools-stay-offline-for-about-10-days/ ）。
- 推理：歐洲剛承受中東天然氣斷供壓力，如今連歐洲本土最大供氣商 Equinor 的企業 IT 都遭到針對性網攻，一旦攻擊從行政 IT 跨向排程或輸氣調度系統，歐洲 TTF 天然氣與能源安全溢價將立即重估。
- 先影響資產：歐洲天然氣期貨（TTF）、歐洲能源與資安股（PANW、CRWD）、挪威克朗（NOK）。

### WIDE-3｜APEC 深圳「川習會（30 對 30 協議）」與美中俄首次三方《四點和平宣言》＋中國稀土出口許可制反制籌碼（20:37 保留並補充稀土籌碼背景）
- 事實：11/19 中午美中「川習會」於深圳登場，雙方依「**30 對 30 協議**」同意各自對價值 **300 億美元**商品削減關稅（https://www.cna.com.tw/news/aopl/202611193005.aspx ）；隨後美中俄舉行約 90 分鐘三方領袖峰會，川普於台北 **18:48** 搭空軍一號離華，中俄官媒發布《**四點和平宣言**》：（1）推動聯合國改革；（2）**三國計畫增加精煉石油產品生產與供應**；（3）反對 ICC 濫用管轄權；（4）重申核戰打不得並展開降核風險對話（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ）。另一方面，大西洋理事會等分析指出，面對美國今日生效的遠端算力管制，北京仍緊握嚴格的**稀土出口許可審查制度**作為談判與反制槓桿（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEhJMqwCRk0KfDVNa3-SSUbXPcYQrzoKZbCs5VsTqb50D3vyZ8vat7304ZmHEcFmMrNuw4m6QKLtkDtdXvlTcfPoMzhVC5UWjntKyq7UdKzmSFeZF93-oT1MIO1WS1zPON3upv3vaXqqib_AIN54Iwg5HTqAI49o4AGy-gswjiMWcpRDQ_DCnxy0kzUg90QwEbJcN34UQE2CVktwI3BJrxZHLHWtp_uzPj0IPpEZWz1ChEcBX3MvHAR5jqBwfa0nSwZ6GSEqPVThJ5zbXJjShXdNKr-qQhcx7q_wbM= ，搜尋跳轉原文）。
- 推理：美國對「遠端 AI 算力」全面收緊，而三方僅在傳統關稅小幅退讓（300 億美元）與成品油供給上達成口頭宣言，高階晶片與稀土關鍵原物料的結構性對立並未解除。
- 先影響資產：USD/CNH、成品油裂解價差、稀土／關鍵礦產股（MP）、中概股（KWEB）。

### WIDE-4｜巴西參院通過 500–600 億雷亞爾財政緊縮案（PLP 299/2026）且財長預告續推緊縮＋巴西被美列入 AI 晶片轉運審查名單（20:37 新增拉丁美洲實質進度）
- 事實：在總統魯拉連任後市場波動加劇之際，巴西參議院通過政府支持的財政包裹法案（PLP 299/2026），擬於 2027 年改善公共帳目約 **500 億至 600 億雷亞爾（約 100 億至 110 億美元）**、將調整期實質支出增速上限壓低至 **2.0%** 並削減稅收豁免；巴西財政部長 Dario Durigan 更於最新談話強調這只是「第一步」，短期內將再推額外財政緊縮措施，為巴西央行未來降息騰出空間（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFGzMj3DHmglQoh99XQe-8kuq2cGYdb0bEzOQP6vB3SD5ZxS3rDcdJuNqhIrFz_mxA_xpICydkLs_lqXz6tX9SnwKlwKRPJ2sbGqmPex6kIWUjPSh8vXEemckHlvDYPryfQfHw4MxyaZxYzPCP_wNMa0GBxvHvcFN4saLEtHG5VfTTBzXSmvYLM3cBk4fBlj3NXiHLMs9i6Eh8uLpZAHc8gvx4vPbMnuehGJbzF7IRpbfGuoaCdHw== ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHV23R9y7YWHYQ1ZF4dsZzDLl0O1Rj3RHjgsTBnT2m1ISFp_ky6VxLjUkskXtRQuA56jxfJPx4rPTcoc5Evysbnr2iUifmNsjqHMFA6-9wKHMS8k58O10jv5BiKhyVc228Tvq6-Acia_fKnBR-14P0MIjG_vygBGhy5mjo9v6SwMVXV-X5LIGGI7KlHwh0G5WG8suu3xQ== ，搜尋跳轉原文，2026-11-19）。同時美國商務部 11/19 生效的遠端算力新規亦將**巴西**與印尼、馬來西亞、新加坡、泰國並列為先進晶片轉運高風險審查國，另有菲律賓與智利於 APEC 期間簽署菲國史上首份與拉美國家的雙邊 FTA。
- 推理：美股新聞幾乎未注意拉美最大經濟體巴西一方面試圖以更硬的財政紀律穩住匯率與債市、另一方面卻因被美納入 AI 晶片轉運名單而面臨科技資本支出放緩壓力。
- 先影響資產：USD/BRL、巴西主權債與 EWZ、拉美資料中心投資項目。

### WIDE-5｜歐盟批准對印尼全面貿易協定（CEPA）年省 6 億歐元關稅＋日本央行重申升息與熊本 M5.7 餘震＋印度 CPI 破 6% 與氣旋「阿克萬」11/20 登陸（20:37 合併精煉歐洲／日／印）
- 事實：歐盟部長理事會 11/19 正式批准並暫行適用**歐盟—印尼 CEPA**，取消逾 **90%** 雙邊關稅、5 年內將印尼對歐盟汽車的 **50%** 關稅歸零，年省約 **6 億歐元**以對沖川普關稅（https://www.aljazeera.com/economy/2026/11/19/eu-governments-approve-trade-deal-with-indonesia-to-offset-trump-tariffs ）；義大利 UniCredit 承諾保留 Commerzbank 法蘭克福總部化解德國反對，帶動歐股 STOXX 600 反彈 +0.3% 至 645.85 點（https://economictimes.indiatimes.com/markets/us-stocks/news/european-shares-rebound-as-anthropic-ipo-boosts-tech-stocks-commerzbank-rallies/articleshow/135985666.cms?from=mdr ）。日本央行總裁植田和男 11/19 在國會淡化疲軟消費、警示潛在通膨破 2% 上行風險，強化 12 月升息至 **1.50%** 預期；熊本清晨 M5.7 餘震尚無 JASM 重大停工回報（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ；https://www.chinadailyasia.com/hk/article/642914 ）。印度 10 月 CPI 升至 **6.09%** 破央行上限，且強氣旋「阿克萬」預計 11/20 中午登陸奧里薩邦已撤離逾 10 萬人（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ；https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ）。
- 推理：在聯準會 12/9 升息幾乎完全定價外，日銀 12 月升息至 1.50% 與印度通膨／天災衝擊正同步收緊全球與亞洲流動性，歐洲則以對外零關稅協定與銀行整併換取緩衝。
- 先影響資產：USD/JPY、EUR/USD、歐系汽車與銀行股（EUFN）、INDA 與 USD/INR。

---

### A｜今天的大動
（註：本輪自動環境未開啟 Hub 視窗，`webview_browser` 回傳 `BROWSER_UNAVAILABLE` 無法即時重抓 `https://wallstreet-sentinel.pages.dev/api/gemini_ask` 畫面；以下保留 19:31 題目單之 12 檔追蹤股並補入 20:37 最新盤前／財報進展，另新增剛於 20:00 公布財報的 **WMT** 與盤前劇烈波動的 **PDD／NTES／BABA**。）

### PANW｜Palo Alto Networks（PANW）盤前維持大漲逾 9%：Q1 FY27 財報優於預期＋45 億美元併購 Applied Compute（無新進展）
- 事實：美東 11/18 盤後公布 Q1 FY27 營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億）、Non-GAAP EPS **1.05 美元**（優於預期 0.97 美元）、NGS ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**（FactSet 共識 141.7 億）、調整後 EPS 指引至 **4.26～4.30 美元**（FactSet 共識 4.18 美元），並宣布以 **45 億美元**全股票收購 **Applied Compute**，11/19 美股盤前跳漲逾 **9%** 領漲美股大型科技股（https://www.prnewswire.com/news-releases/palo-alto-networks-reports-fiscal-first-quarter-2027-financial-results-302944393.html ；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ；https://www.prnewswire.com/news-releases/palo-alto-networks-to-acquire-applied-compute-bringing-secure-open-weight-ai-to-the-enterprise-302944421.html ）。
- 同意本站；本站漏掉的：KeyBanc 將評等調升至 **Overweight**、價格看法調高至 **$380**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ）。

### TJX｜TJX Companies（TJX）今天 +8.0%：Q3 FY27 同店銷售成長 4% 超越計畫、上調全年展望至區間上緣（無新進展）
- 事實：TJX 於美東 11/18 公布 Q3 FY27 淨銷售年增 **6%** 至 **159.5 億美元**、合併同店銷售成長 **4%**、調整後 EPS **1.34 美元**（GAAP **1.39 美元**，含 0.05 美元 IEEPA 關稅退稅淨利益），並將全年展望收斂至區間上緣（https://mlq.ai/news/tjxs-comparable-sales-rise-4-above-its-plan-and-it-narrows-its-full-year-outlook-toward-the-top-of-the-range/ ）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### CRWD｜CrowdStrike（CRWD）今天 +5.9%（盤前）：受同業 PANW 財報驗證企業 AI 資安需求外溢帶動（無新進展）
- 事實：CRWD 預計 **12 月 1 日盤後**才公布財報，11/18–19 本身無單獨公司公告或分析師新調整（找不到來源）；受同業 PANW Q1 FY27 財報與 45 億美元 AI 安全併購案外溢提振，資安族群盤前續強（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ）。
- 本站漏掉的：屬同業財報外溢效應，非 CRWD 個別公告。

### SKHY｜SK 海力士（SKHY）今天 +5.6%（盤前）：韓股連兩日收漲，Anthropic 1.5 兆美元 IPO 定價點燃全球記憶體與儲存股盤前大漲（無新進展）
- 事實：SK 海力士（000660.KS）於 11/19 韓股正規盤收漲 **+3.41%** 至 **1,183,000 韓元**（https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ）；同日美股／海外追蹤盤前因 Anthropic 今晚以 83 美元掛牌（募資 813 億美元、估值 1.5 兆美元），記憶體與儲存股盤前大漲逾 **5%**（https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### SNDK｜SanDisk（SNDK）今天 +5.5%（盤前）：今日為 1 拆 8 股票分割前最後交易日＋Anthropic IPO 帶動儲存股盤前集體反彈（無新進展）
- 事實：今日（美東 11/19）為 SanDisk（SNDK）**1 拆 8 股票分割**盤後分配股權前最後交易日（11/20 依拆股後價格交易，https://financefeeds.com/sandisk-sndk-stock-776-thursday-last-session-before-8-for-1-split-bull-831-bear-749/ ；https://www.fool.com/investing/2026/11/16/sandisk-splits-its-stock-8-for-1-on-nov-19-flash-memory-prices-still-matter-more-than-the-share-count/ ），並隨 Anthropic 今晚掛牌與儲存族群盤前同步大漲約 **4.9%–5.5%**（https://news.cnyes.com/news/id/6667734 ）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### MU｜美光（Micron，MU）今天 +5.5%（盤前）：Anthropic IPO 定價 83 美元今晚掛牌引爆儲存與 AI 記憶體股盤前反彈（無新進展）
- 事實：受 Anthropic（ANT）IPO 定價 83 美元、募資 813 億美元今晚於那斯達克掛牌激勵，美光（作為 Anthropic 同步私募出資方暨記憶體夥伴）11/19 盤前與 SK 海力士、SanDisk 等族群集體上揚逾 4%–5%（https://news.cnyes.com/news/id/6667734 ；https://financefeeds.com/micron-mu-stock-705-thursday-anthropic-ipo-priced-83-bull-746-bear-667/ ）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### STX｜希捷科技（Seagate Technology，STX）今天 +5.4%（盤前）：受 Anthropic 創紀錄 IPO 點燃 AI 資料中心儲存與記憶體族群集體反彈（無新進展）
- 事實：11/19 美股盤前 STX 未見單獨公司公告（找不到獨立公司來源），隨 SKHY、SNDK、MU、WDC 等儲存／記憶體板塊受 Anthropic 今晚掛牌帶動同步大漲（https://news.cnyes.com/news/id/6667734 ；https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ）。
- 本站漏掉的：STX、WDC、MU、SNDK、SKHY 今日盤前屬同一儲存／記憶體板塊集體反彈，本站題目單全數標「沒有找到對得上的新聞」。

### WDC｜威騰電子（Western Digital，WDC）今天 +5.1%（盤前）：與 STX 等儲存族群同受 Anthropic IPO 提振盤前同步反彈（無新進展）
- 事實：11/19 美股盤前 WDC 未見單獨公司公告（找不到獨立公司來源），與 STX、SNDK、MU、SKHY 同步受 Anthropic 今晚掛牌激勵於盤前走高（https://news.cnyes.com/news/id/6667734 ；https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ）。
- 本站漏掉的：與 STX 屬同一儲存板塊集體反彈，非 WDC 個別新消息。

### HCA｜HCA Healthcare（HCA）今天 -5.0%：受 CMS「CRUSH」醫保反詐欺追溯審計草案與證券詐欺律師調查發酵拖累板塊（無新進展）
- 事實：CMS 11/16 提出「CRUSH」反詐欺規則草案（擬擴張 Medicare Advantage 稽核並回溯至 2018 年度），重挫醫療保險與醫院板塊；同日（11/18）摩根大通維持 HCA `Neutral` 並將價格看法由 $425 調高至 **$475**（https://fr.tradingview.com/news/gurufocus:3ac55a47d094b:0-unitedhealth-stocks-fall-4-62-as-cms-proposes-wider-medicare-advantage-audits/ ；https://www.tradingview.com/news/tradingview:9eb3a7caf755c:0-jp-morgan-maintains-hca-healthcare-at-neutral-raises-price-target-to-475-from-425/ ）。
- 傳聞／找不到來源：市場流傳 Pomerantz 律師事務所就 HCA 2026 指引下修啟動調查，尚無機構或公司正式回應。

### INTC｜英特爾（Intel，INTC）今天 +4.9%（盤前）：隨晶片族群結束五連跌反彈，市場消化川普談 Blackwell 輸陸可能性與 18A-P 首家外部客戶進展（無新進展）
- 事實：半導體連跌五日後，隨 Anthropic IPO 定價高於區間帶動那指期貨漲約 1.9%–2.3% 與晶片股反彈，加上川普於深圳稱 2–3 年後不排除放行 Blackwell 晶片輸陸及英特爾 Austin 峰會宣布 18A-P 首位外部客戶與微軟採用 EMIB，推動 INTC 盤前漲約 **4.2%–4.9%**（https://www.tradingview.com/news/stocktwits:6243efa9f094b:0-nvda-intc-stocks-ease-post-5-day-rout-after-meeting-xi-jinping-trump-says-nvidia-blackwell-chips-could-reach-china-within-2-3-years/ ；https://news.cnyes.com/news/id/6667734 ）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### PSX｜Phillips 66（PSX）今天 -4.7%：與 VLO 同受 EIA 汽油／原油庫存暴增壓抑煉油族群（無新進展）
- 事實：美東 11/18 同業 VLO、MPC、PSX 同步受 EIA 截至 11/13 當週汽油庫存暴增 **520 萬桶**、蒸餾油增 **160 萬桶**與原油累庫 **340 萬桶**拖累下挫（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ）。
- 傳聞／待人工來源證實：TradingView 自動摘要提及德州 Borger 煉油廠排放通報與 Jefferies 將對 PSX 價格看法由 $280 調降至 $265（機器摘要暫列傳聞）。

### CNQ｜Canadian Natural Resources（CNQ）今天 -4.6%：隨北美油氣股反映 EIA 庫存大增與 25.3 億加元併購案（無新進展）
- 事實：CNQ 11/18 正規盤收跌 **4.63%** 至 **$45.53**，反映 EIA 原油／汽油庫存大增及以 **25.3 億加元**收購 Advantage Energy 案（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ；https://www.nationthailand.com/news/world/40073656 ；https://www.newsfilecorp.com/release/324091/Canadian-Natural-Resources-Limited-Enters-into-Agreement-to-Acquire-Advantage-Energy-Ltd ）。

### PDD / NTES / WMT / BABA｜20:37 補充已公布財報股盤前即時反應（新增）
- 事實：截至美東 11/19 07:30（台北 20:30）盤前交易：**PDD** 因 Q3 2026 Non-GAAP 淨利 **310 億人民幣**、每 ADS 盈餘 **3.14 美元（21.04 元）**大幅優於預期（砍銷售與行銷費用帶動），盤前飆漲約 **8%–9%**（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQETi_WhHK6SS_juohyQRs0o_F413TqimnbxuDpd2BhMKSxEubCEkyqve_sh1W_hUvfgm7Tj1LlNXb3WSe2opU8IRtbgO7XIe6cba7Zy9gCvWm-LnlKziObFyv4bMGA= ）；**NTES** 因 Q3 營收 **279 億元（-1.8% YoY）**與獲利雙遜預期，盤前下跌逾 **3.5%–5%**（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRtElwUMPv-XgkTtIrZigmBKoBFrtLrgQaP5UOVZcAE_UhQayLAd3DFD8Sdli4VElDSuoCB89D42rU1mn6NYxk6MMEgTl2qVzVYs5SAzbo-iUElLoXD0qvMixveH0RARR3zgq_V0UE6_sy5pVfyFk8GKOD8o776g_z_7JXCGP0tcvhhtVkvGKW2rbiPhsjrtsqax-cHhoP5r6eW8aTkAaf98ZU4EIIPOnOkEhnNA== ）；**WMT** 於 20:00 公布營收 **1,888 億美元**、調整後 EPS **0.65 美元**雙雙優於預期並上調全年財測，但因股價位處 52 週高檔，盤前小幅回吐約 **0.7%** 至 **$126.44–$126.76**（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG1mg-wRi65hi7bhfdb_sUus-f8WuhpO18KToRfWYc52s6D3jK39MYT8udTVNaWmnj-5LmU-a26oQ1hKAgN4smW0QhX6kz-DkOPnpTPOl9EjX9JhKjNEYqjhH9RoPP7slgUrRX0HyGEhA1KY1LCwL6lU2LVfFetWXGp9QCo7XJoCMDCSqFiGat79oXlwFFp_OE6rY1KFOYC2hmCZxdqFg== ）；**BABA** 盤前約小跌 **0.1%–2%**。

---

### AN｜AN-1：最近 3 小時內（台北 17:37–20:37）未見美股 AI 供應鏈／前 20 大權值股新增公開分析師調評；補齊已核對近期調評與市場動態
- 事實：檢索最近 3 小時（台北 17:37–20:37／美東 11/19 04:37–07:37），針對 AI 供應鏈（NVDA、AVGO、AMD、TSM、ASML、KLAC、LRCX、AMAT、MU、MRVL、ARM、ORCL、CRWV、SMCI、DELL、HPE、ANET、VRT）及美國市值前 20 大公司，未見新發布的券商評等調整（找不到來源；先前 **AVGO、NVDA、PANW、HCA、2330** 調評保留如下）。
- 事實（近期已核對報告，依任務單保持英文評等原文，無新進展）：
  1. **高盛 Goldman Sachs（AVGO，美東 11/19 01:26／台北 14:26 報導）**：分析師 James Schneider 維持 **AVGO** `Buy` 評等，因同業倍數壓縮由 30 倍下修至 25 倍，將價格看法由 $540 調降至 **$460**（https://www.tokenpost.com/news/business/61151 ）。
  2. **Rothschild & Co Redburn（AVGO，11/13 報告）**：將 **AVGO** 由 `Buy` 調降至 `Neutral`，價格看法由 $595 調降至 **$398**（https://fr.tradingview.com/news/seekingalpha:f4cc47e04094b:0-broadcom-in-focus-as-rothschild-downgrades-to-neutral-but-flags-potential-upside/ ；https://www.tikr.com/blog/is-rothschild-co-redburn-wrong-to-give-up-on-broadcom-wall-street-still-sees-533 ）。
  3. **摩根大通 JPMorgan（HCA，11/18 報告）**：維持 **HCA** `Neutral` 評等，將價格看法由 $425 調高至 **$475**（https://www.tradingview.com/news/tradingview:9eb3a7caf755c:0-jp-morgan-maintains-hca-healthcare-at-neutral-raises-price-target-to-475-from-425/ ）。
  4. **摩根士丹利（台積電 2330，11/19 報告）**：維持 `Overweight` 評等與估值看法 **3,088 元**，2026–2028 年 EPS 估 **112.10／148.64／189.81 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ）。
  5. **輝達（NVDA）與近期機構報告**：Summit Insights 降至 `Hold`（https://www.tikr.com/fr/blog/is-summit-insights-wrong-to-give-up-on-nvidia-wall-street-still-sees-251 ）；HSBC Frank Lee 降至 `Hold` 看法 $365→$170（https://www.tradingview.com/news/binance_news:d94dcaa1f094b:0-hsbc-downgrades-nvidia-says-stock-may-struggle-until-new-ceo-is-named/ ）；Evercore ISI `Outperform`→`In-Line` 看法 $186、Bernstein $400→$200、Baird `Outperform`→`Neutral`（https://www.tradingview.com/news/benzinga:3bce7f47b094b:0-nvidia-gets-10-bank-downgrades-after-huang-exit-what-to-expect-ahead-of-q3-results/ ）；Moody's 維持 `Aa1` 展望降至 `Stable`（https://finance.biggo.com/news/3a68067c-0d5c-40a8-9836-0ebcfa4e1591 ）；KeyBanc 調升 PANW 至 `Overweight` 看法 $380（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ）；Piper Sandler 調升 MDT 至 `Overweight` 看法 $120（https://www.tradingview.com/news/tradingview:5b080eae6cc49:0-piper-sandler-upgrades-medtronic-to-overweight-from-neutral-raises-price-target-to-120-from-85/ ）。另 Bernstein 重申 **ASML、AMAT、LRCX、KLAC** 為設備族群首選，Jefferies 維持 **AMAT** `Buy`、看法 $770→$580（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEzIjtWQC62jHHg6iYFEcEJL7r2TlLELCIfgdQqm3mAhLnWE68uRv55aPBkFK286zN-20i2ODO5m6iBr0mTeWt3RdOFDRpQJaTsR6mkS0THJepSlUeIaG4Aq64VogF52Elq7EhyQpReOfKCFcleDJY2vcEa61IhJFAlJxXRsrv4W41IMLZtSMPd5UNsfyv4AEh3jdnxaP9Zxo_GFBzF5S4-0An9VK0j84sgV5hGihIBj4z6F1wnJ7Oa ）。

---

### POL-1｜美國商務部 BIS「超級智慧」遠端算力管制新規今日（11/19）刊登聯邦公報生效，同日白宮馬尼拉 Quad 峰會聚焦可信賴超級智慧供應鏈（無新進展）
- 事實：BIS 暫行最終規則（聯邦公報文件 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）於美東 **2026 年 11 月 19 日**正式刊登聯邦公報並立即生效（60 天意見徵詢至 2027-01-19），增訂 § 744.24 限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，並將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，同時廢止前政府 AI 擴散規則（https://public-inspection.federalregister.gov/2026-23529.pdf ；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ；https://www.milbank.com/en/news/bis-issues-new-rule-restricting-remote-access-to-advanced-chips.html ）。台積電回應正評估新規並將嚴格遵循適用法令、強化最終用途審查（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH8W-qPj-SylY77ym1ym_uDcuU6q0XXakqKjUhnlVlD0Nm9oiOLXHp3zO12aE21K_tPgM7AjkXk0KsKVoqDd1hN9YlaD8QQXwtVi-5NhTenCRvOr_nl_fwVSAbL6LRpwsnVFiylyiwtKA== ）。
- 事實：白宮於 11 月中旬馬尼拉 Quad 領袖峰會聯合澳、印、日發表聲明，鎖定關鍵礦產／半導體供應鏈安全與可信賴超級智慧技術生態；同日聯邦公報亦列載 CMS CRUSH 反詐欺草案（`2026-23461`，https://public-inspection.federalregister.gov/2026-23461.pdf ）。

### POL-2｜美國財政部 FinCEN 強化 CDD 提案、9 月 TIC 淨流入 2,610 億美元、OFAC 制裁與 USTR 談話（無新進展）
- 事實：財政部 FinCEN 發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，https://home.treasury.gov/news/press-releases/sb0691 ）；9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ）；OFAC 制裁真主黨與聖城軍金流（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 大使 Greer 11/18 於 RBA 年會重申美國優先貿易（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）。

---

### TW-1｜11/19 台股收跌 1,768 點（38,426.89 點）、櫃買暴跌 7.22%、1,028 檔明納限空令 2.0、世界／台化／萬泰科爆 1.29 億違約交割；新台幣收升 32.942 元（無新進展）
- 事實（11/19 台股收盤、三大法人與違約交割）：加權指數盤中下探 38,259.7 點（跌 1,935.21 點），終場收 **38,426.89 點（-1,768.02 點 / -4.40%，史上第 7 大跌點，失守年線 39,368 點）**，成交值 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ）；櫃買指數收跌 **-7.22%（-22.22 點）至 285.33 點**。電子權值股收盤：**台積電 2,100 元（-3.45%）**、**聯發科 3,720 元（-5.58%）**、**鴻海 220.5 元（-0.23%）**、**日月光投控 504 元（-8.03%）**、**緯穎 1,410 元（跌逾 4%）**（https://www.moneyweekly.com.tw/ArticleData/Info/Article/212266 ）。三大法人合計賣超 **461.03 億元**（**外資 -243.12 億元**、**投信 +15.13 億元**、**自營商 -233.03 億元**，其中自營商避險部位 **-214.40 億**，https://www.cna.com.tw/news/afe/202611190200.aspx ）；期貨三大法人合計淨空單 **-8,883 口**（外資 **-99,219 口**、投信 **+91,791 口**、自營商 **-1,455 口**）。盤後證交所與櫃買中心再通報 3 檔違約交割合計 **1.29 億元**：包含上市**台化（1326）4,172.8 萬元**，以及上櫃**世界先進（5347）與萬泰科（6190）**（https://stock.ltn.com.tw/article/m7hjf9c9axqq ；https://inews.setn.com/news/1941815 ）。
- 事實（11/19 新台幣收盤價）：台北外匯市場開 32.960 元，盤中低見 **33.040 元**，16:00 翻升收 **32.942 元（升值 0.5 分）**；台北外匯經紀成交 **22.63 億美元**、台北及元太兩大外匯市場總成交 **32.82 億美元**（https://www.cna.com.tw/news/afe/202611190296.aspx ；https://money.udn.com/money/story/12509/9889341 ）。
- 事實（金管會 11/20 限空令 2.0）：（1）今日收盤跌幅達 **3.5%** 以上之上市櫃與 TDR（共計 **1,028 檔**），次一交易日禁止低於前收融券及借券放空；（2）每日盤中借券放空委託數量上限由前 30 日均量 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://www.cna.com.tw/news/afe/202611190182.aspx ；https://vexed.me/realtime ）。

### TW-2｜台積電資深副總張曉強親赴輝達固鏈＋Vera Rubin Q3 量產出貨；正式公告 5 億美元入股 Anthropic（20:37 補充《工商時報》張曉強與 BIS 回應）
- 事實：《工商時報》與《鏡週刊》引述輝達財報會議揭露，輝達人事變動後由台積電資深副總暨副共同營運長**張曉強**親赴輝達美國總部穩固長期供應與擴產承諾，且輝達新一代 **Vera Rubin NVL72** 與 **Vera CPU** 已於 2026 年 Q3 採台積電 5nm/3nm 與 CoWoS 進入量產出貨；台積電另表示正評估美商務部 11/19 生效的遠端算力管制新規（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGan4RU7Fxg92JH7sELWAiA8faXWxOV9fehZY2xB-1upXsCXxwxDndm-su7F8syV2plZ6gIptSrtYA_Zuuh63lIXyOn7_jP0nWrd-DgoiVYRvIKeCW6NWlfbGBHRe6cWRAb_KuQ3e4WFg== ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH8W-qPj-SylY77ym1ym_uDcuU6q0XXakqKjUhnlVlD0Nm9oiOLXHp3zO12aE21K_tPgM7AjkXk0KsKVoqDd1hN9YlaD8QQXwtVi-5NhTenCRvOr_nl_fwVSAbL6LRpwsnVFiylyiwtKA== ，搜尋跳轉原文）。
- 事實（其餘台鏈公告，無新進展）：台積電 11/19 正式公告透過 TSMC Partners 以 **每股 83 美元**取得 Anthropic 普通股 **6,024,096 股**（約 **5 億美元**，https://www.cna.com.tw/news/afe/202611190254.aspx ）；日月光投控旗下台灣福雷電子高雄仁武 J 坵塊新廠 11/19 動土計畫投資 **2,489 億元**（https://www.cna.com.tw/news/afe/202611190122.aspx ）；廣達田納西廠租約 1,490.8 萬美元（https://news.cnyes.com/news/id/6666244 ）；海龍 2A 綠電轉售台積電（https://www.cna.com.tw/news/afe/202611190102.aspx ）；鴻海 72.4 億日圓收購 Sony 車載相機事業（https://www.ctee.com.tw/news/20261119700316-439901 ）；熊本清晨 M5.7 地震尚無 JASM 重大停工回報。
- 傳聞（無新進展）：《工商時報》等引述業界指出，台積電依客戶（含 ASIC 三雄）資產負債表設 AI 信用額度、超額須預付現金，帶動部分台鏈以海外可轉債（ECB）或聯貸籌資，尚未獲台積電正式公告證實（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEQ7eQEt1DD0B37BKW7YYtqrJDtOw7VgcpMWmfGK-2I6GCNxJ8Tkor6I9OkW_4EgTeZF7pRuk6A0EBi3bSGVJNMBRE3N1wvcBPa5lXm27P19Uhe3othNRvF1ANtwuTjNXgenkicdyWENA== ；https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ）。

### TW-3｜SK 海力士 11/19 收漲 +3.41%、蘋果洽談三星多年期 DRAM 長約；亞股日韓印收紅、陸港台收黑（無新進展）
- 事實：《MoneyToday》11/19 報導 SK 海力士（000660.KS）收漲 **+3.41% 至 1,183,000 韓元**，與三星電子連兩日收高（https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ）；《The Korea Herald》11/19 報稱蘋果正進入與三星電子洽談 4 至 5 年期 DRAM 供應協議最後階段（https://www.koreaherald.com/article/10942672 ）。11/19 亞股收盤：**日經 225 +0.71%（59,444.21）**、**KOSPI +1.39%（5,137.89）**、**印度 Nifty 50 +0.91%（25,458.75）**；**上證 -0.28%（3,577.62）**、**恆生 -1.95%（22,841.62）**、**台股加權 -4.40%（38,426.89）**。東京威力科創（TEL）與愛德萬測試近期受 AI 晶片情緒牽動劇烈震盪，無獨立新廠務公告（https://www.advantest.com/cn/products/semiconductor-test-system/soc/v93000/ ；https://focustaiwan.tw/business/202611090020 ）。

---

### EARN-WMT｜沃爾瑪（WMT）已於 11/19 20:00（美東 07:00）公布 Q3 FY27 財報：營收 1,888 億美元、調整後 EPS 0.65 美元雙優於預期，並上調全年展望！（重大更新）
- 事實：沃爾瑪於 **美東 2026-11-19 07:00（台北 20:00）**發布 Q3 FY27 財報（電話會議於美東 08:00／台北 21:00 舉行）：
  - **營收**：**1,888 億美元**，年增 **5.2%**（常數匯率 +4.5%），優於市場共識約 **1,872.5 億～1,873.8 億美元**；其中美國淨銷售年增 3.6% 至 **1,250 億美元**、美國同店銷售（不含燃油）成長 **2.9%**；全球電商銷售年增 **17%**（美國電商 +23%）；全球廣告業務年增 **25%**（美國廣告 +37%）。
  - **獲利**：營業利益年增 **16.0%** 至 **77.7 億美元**（經調整常數匯率 +5.5%）；**調整後 EPS 0.65 美元**（優於市場預期 0.64 美元與上季財測 0.62–0.64 美元），GAAP EPS 0.62 美元（含股權與投資淨損 0.03 美元）。
  - **全年 FY27 展望上調**：常數匯率淨銷售成長上調至 **4.9%–5.2%**（原 4.0%–5.0%）、調整後營業利益成長上調至 **8.0%–8.6%**（原 7.0%–8.5%）、調整後 EPS 上調至 **$2.84–$2.89**（原 $2.80–$2.87）；受股價位處 52 週高檔影響，盤前小跌約 0.7% 至 $126.44–$126.76（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHCYiPdzkkgZvueOpIWre5B-yv5zVSrT4FNfgDqdz62gO74R1ZQYvKa9_hy0d5vZNw0BoCNETH_AraHzAyz5RY7pCdDD_K_SF6Oh9jxjeb42M3nNf9-mOlVstUeoJqj0KzGiBRsREfwsh7EPvsfMmpmuxSKjCsccnkdnDvtB1QLjnZhndkNdnuOckBpU4VdRbDn5yB9TixWSAcmv0TiVQ== ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGfl7eSgwRENzRJOZ8vDjw5WS3rCEvj1Lga-d80ba86YTZdyh3OgJL1ZiMjNqzu_MnAGkQLVxlIimlL2_SMuImbkZ8awsiR9mntHOVwOKVY6rQjXzApAIPMQj1nMg_sA7Hv6yPLs3Rrgm4= ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGi9WbWnHfgovNAEvdidfhsjIYTHLk1VwYozA8O0_bIxp-h93Sv7GvQoDQruA2wDp57-QZnGBD7Gq4FJdg4BIQkKThGoIAoMM0UwzucTYuR3TWf7Kh_F2ZOlSGjZe3Xw4TMu-CbBzOdQP9B7OvA_t7-MWlkWwnMKBf4OSBrEOhyI0WUoqTUDvWGX1Na1OLlbSRV8Fe7cizO7qo0Vtgd ；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ，搜尋跳轉原文，台北 2026-11-19）。

### EARN-PDD｜拼多多（PDD）11/19 19:30 公布 Q3 2026 財報：營收 1,083 億遜預期但 Non-GAAP EPADS 3.14 美元大勝，盤前飆漲約 8%–9%（20:37 補充盤前反應）
- 事實：拼多多於美東 11/19 06:30（台北 19:30）公布 Q3 2026 營收人民幣 **1,083.4 億元**（約 162 億美元，年對年持平，遜於市場共識約 1,155 億～1,217 億元），主因交易服務營收年減 12% 至 485 億元；但受惠削減銷售與行銷支出，調整後營業利益達 **326.4 億元**（優於市場預估 ~278.5 億）、Non-GAAP 淨利 **310 億元**（優於預估 ~280.3 億）、**Non-GAAP 稀釋每 ADS 盈餘 21.04 元（3.14 美元）**大幅擊敗共識 2.61–2.77 美元，帶動美股盤前大漲約 **8%–9%**（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQETi_WhHK6SS_juohyQRs0o_F413TqimnbxuDpd2BhMKSxEubCEkyqve_sh1W_hUvfgm7Tj1LlNXb3WSe2opU8IRtbgO7XIe6cba7Zy9gCvWm-LnlKziObFyv4bMGA= ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEv5D9SHWgSJPD25VEcgTMjOkoM-E7Sl4DvydrU_hFxstnwdsog9PAHg-4N70oOmCu9hc3gDxeO73xjsWCRzNaJ7QxPH9V97qf4huNHPSsg7u5X5wAxAQdflOS3CpHQE1E4ZESHsZNONprBgNLYl8eDO2ovnMf1E_VS1hXruMoC-F4IJXCLn-ISJSu33PAzjjfXZ2aDSJ3bN67xMVxzt0J2r6E= ）。

### EARN-BABA｜阿里巴巴（BABA）11/19 公布 Q2 FY27 財報：營收 2,715.19 億（+10% YoY）優於預期，但 FCF 淨流出 344.72 億且庫藏股縮水致盤前走弱（20:37 補充庫藏股金額）
- 事實：阿里巴巴 Q2 FY27 總營收人民幣 **2,715.19 億元**（約 405.0 億美元，+10% YoY）優於預期 2,698.49 億元，AI 雲外部收入年增 67%；惟 Non-GAAP 淨利 **199.09 億元**低於預期 265.7 億元、資本開支激增 60% 至 504.77 億元致 **FCF 淨流出 344.72 億元**，且當季美股股票回購大幅縮減至約 **2.21 億美元**（約 1,795 萬股普通股），ADR 盤前下跌約 0.1%–2%（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGllO4TArmJg2Thc9zn8oymnfT4EoU1fxaq0Flcl3a5za3t4Rn-o7wb4mvwoTP0knvR4b5vrkkucD--iO846q_TwsK4yP6UHsnoW-eu7wACT7mjSLFHiJNM1atcotRZ6mmgNOpltcHciqhLDfRnSbK0e5het5MJu753DmOa06FMbHhxiSRCSxbvH7mCqLCQGHCkB8E7 ）。

### EARN-NTES｜網易（NTES）11/19 公布 Q3 2026 財報：營收 279 億元（-1.8% YoY）與獲利雙遜預期，盤前跌逾 3.5%–5%（20:37 補充盤前反應）
- 事實：網易 Q3 2026 淨營收人民幣 **279 億元**（42 億美元，-1.8% YoY，遜於共識約 295 億～303 億元），遊戲收入 229 億元（-1.7% YoY），Non-GAAP 淨利 **92 億元**、每 ADS 盈餘 2.12–2.13 美元（¥14.21），營收與獲利均低於預期致盤前跌逾 **3.5%–5%**（https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFvqIDEMi8jgqZ_4B_9xMua5rVGU1pA4F7nXFBwXKhm7xklIr3lDUQUsXOIhEx-8Sjir_uzK4kI0HYVcjdZiXecKRocTAQ0DFyIplv34GEPhNrkCOnW6Ov6AYy1Aa__i-u2fCzJRmAb2opxUtytIccRaxcBsdIgeTMif7sLnt6VTJBmW7wDeAKTEn7vAW_9GQOHHzzY5KHybXjtqETPML6wSc5wmBN9vA== ）。

### EARN-WSM / INTU / ROST / GAP｜今日（11/19）美東盤前與盤後其餘財報（20:37 重查 WSM 至 07:35 ET 仍未見發布）
- 事實：
  - **WSM（美東 11/19 盤前／10:00 ET、台北 23:00 電話會議，截至 20:37 尚未見官方財報新聞稿發布）**：共識營收 **19.8 億～20.0 億美元**、EPS **2.17–2.21 美元**（市場關注 Pottery Barn 約 +4.7% 與 West Elm 約 +6% 同品牌營收動能，https://www.tradingview.com/news/tradingview:5796c7c550438:0-wsm-q3-26-earnings-eps-estimate-is-2-19-usd/ ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEHbB-1dNeWeXI8BnkHcmiBvrYx_M6fcsyfrCBFm7i1_uPeYtX-ncCpOuwksgbMf1NVTTMfcMP0zDZRWVWvW0Ywodxnot-ItEDuec_a8eDcl_s7CYU8ClO4KrpzHau9zyEjqMupJT00RqVptKYHVrAIwJaN1Uubk153I-Gwjj9Q8AV6tMu8gFVtDlxDHoTFyUipY5xlpJE23bhg4mO7A_hR_w== ）。
  - **INTU（盤後／台北 11/20 05:00）**：共識營收 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（原財測 2.44–2.48 美元），隱含波動 ±8.9%–10.5%（https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  - **ROST（盤後／台北 11/20 05:00）**：共識營收 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ）。
  - **GAP（盤後／台北 11/20 05:00）**：共識營收 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）。

### EARN-HPE / ZM / BBY / BURL / DKS / ADI / MDT / DELL / HPQ / ADSK / WDAY / BILI / DE｜11/23–11/25 未來 10 天財報（無新進展）
- 事實：
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（公司財測 1.20–1.30；波動 ±9.7%，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ）；**ZM** Zacks 共識營收 **12.8 億美元**、EPS **1.49 美元**（https://www.zacks.com/stock/news/3030700/zoom-communications-zm-falls-more-steeply-than-broader-market-what-investors-need-to-know ）。
  - **11/24 盤前（台北 20:00–21:00）**：**BILI** MarketBeat 共識營收 **12.3 億美元**、EPS **0.23–0.27 美元**；**BURL** 共識營收 **29.7 億美元**、EPS **1.72 美元**（https://www.tradingview.com/news/tradingview:6917007d5e261:0-burl-q3-26-earnings-revenue-estimate-is-2-97b-usd/ ）；**DKS** 營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ）；**ADI** FactSet 共識營收 **43.2 億美元**、EPS **3.88 美元**（https://www.tradingview.com/news/tradingview:4441db86105da:0-adi-q4-26-earnings-revenue-estimate-is-4-32b-usd/ ）；**MDT** FactSet 共識營收 **94.8 億美元**、EPS **1.33 美元**（https://es.tradingview.com/news/tradingview:dcc2d0d8b8c99:0-mdt-q2-26-earnings-revenue-estimate-is-9-48b-usd/ ）；**BBY** Zacks 共識營收 **98.8 億美元**、EPS **1.48 美元**（https://www.zacks.com/stock/news/3031155/best-buy-bby-reports-next-week-wall-street-expects-earnings-growth ）。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億～492.5 億美元**、EPS **6.41–6.60 美元**（波動 ±14.85%，https://www.tradingview.com/news/tradingview:e525c4bdcb809:0-dell-q3-26-earnings-revenue-estimate-is-49-25b-usd/ ）；**WDAY** 營收 **26.9 億美元**、EPS **2.75 美元**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ）；**HPQ** FactSet 共識營收 **154.3 億美元**、EPS **0.75 美元**（https://in.tradingview.com/news/tradingview:2627939d5b773:0-hpq-q4-26-earnings-revenue-estimate-is-15-43b-usd/ ）；**ADSK** MarketBeat 共識營收 **21.3 億美元**、EPS **3.07 美元**（https://www.marketbeat.com/instant-alerts/upcoming-autodesk-adsk-set-to-announce-quarterly-earnings-on-tuesday-2026-11-17/ ）。
  - **11/25 盤前（台北 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ）。

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並警告 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（除非明確預告 1 月再升 1 碼）（無新進展）
- 事實：Waller 受訪指出聯準會可能需要「shock」壓抑通膨預期避免 3% 通膨固著，12/8–9 會議應考慮一次升息 50 基點，除非明確前瞻指引 12 月與 1 月連續各升 1 碼（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ；https://www.morningstar.com/news/marketwatch/20261118119/feds-waller-says-interest-rate-hikes-may-be-needed-to-shock-inflation-out-of-the-system ；https://www.aa.com.tr/en/economy/fed-governor-favors-half-point-rate-hike-in-december-unless-fed-signals-january-increase/4129382 ）。

### FED-3｜聯準會理事 Michael S. Barr（偏升息）、紐約聯準銀行總裁 John Williams（反對一次升息 2 碼）；稍後 Goolsbee 問答與貼現率閉門會議（無新進展）
- 事實：Barr 11/18 在紐約聯準銀行演說指出通膨仍過高、適合進一步升息並示警 AI 代理資金調撥風險（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ）；Williams 於 Axios BFD 峰會指出不需戲劇性行動、反對一次大幅升息 2 碼（https://www.aa.com.tr/en/economy/fed-governor-favors-half-point-rate-hike-in-december-unless-fed-signals-january-increase/4129382 ；https://www.idnfinancials.com/news/71905/does-the-fed-still-need-to-raise-interest-rates-john-williams-answer ）。芝加哥聯準銀行總裁 Goolsbee 將於 **美東 11/19 12:30（台北 11/20 01:30）**於印第安納經濟俱樂部座談（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；聯準會理事會於 **美東 11/19 15:00（台北 11/20 04:00）**召開閉門貼現率會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼約 86%–97%、升息 2 碼約 3%–10%（20:37 重查最新區間）
- 事實：截至 11/19 各家引述 CME FedWatch 數據顯示，12/8–9 FOMC 升息 1 碼機率落在 **86%–97%**（多數報導落在 90% 上下），少數押注 2 碼（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGBsUaKBkQdp_z3iqxgWhwTZw28M84Yn2RJh7hz57arscGIigd2xRVgFIA0LPGRxmXZPj8nlDZm0aZLZaKHqAgpqqHhO17byIc42XLDwpo9AEaBHXiZerdX7dks4qQKccEBo4z0wkusQkCVeSxOK5WbEzCt82Ny_H7s ，搜尋跳轉原文）。

---

### B｜Claude 指定查證

### TASK-B1｜BEA 9 月核心 PCE 年增率確為 3.1%（非 2.6%），附上 bea.gov 原文網址與 13 字原文（無新進展）
- 事實：美國經濟分析局（BEA）2026 年 9 月《個人所得與支出》官方新聞稿明確公布 9 月核心 PCE 物價指數年增 **3.1%**（月增 0.3%），原文那一句（13 字）為 `"Excluding food and energy, the PCE price index increased 3.1 percent from one year ago."`（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）。結構上係因住房通膨降溫拉低權重較大的 CPI，而醫療／金融／科技服務權重在 PCE 較高且黏著（https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html ）。

### TASK-B2｜11/19 台股收跌 1,768.02 點收 38,426.89 點（櫃買 -7.22%）、外資現貨賣超 243.12 億、三大法人台指期淨空單 -8,883 口、新台幣收升 32.942 元（無新進展）
- 事實：集中市場收 **38,426.89 點（-1,768.02 點 / -4.40%）**，成交 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ）；櫃買收 **285.33 點（-7.22%）**。外資現貨賣超 **243.12 億元**、投信買超 **15.13 億元**、自營商賣超 **233.03 億元**，三大法人合計賣超 **461.03 億元**（https://www.cna.com.tw/news/afe/202611190200.aspx ）；期交所三大法人台指期合計淨空單 **-8,883 口**（外資 -99,219、投信 +91,791、自營商 -1,455）；新台幣 16:00 收 **32.942 元（升值 0.5 分）**（https://www.cna.com.tw/news/afe/202611190296.aspx ）；金管會 11/20 起實施 1,028 檔 3.5% 限空令 2.0（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。

### TASK-B3｜Anthropic 今晚 22:30 才在納斯達克掛牌，首日開盤／收盤／成交量尚未產生；更新美東 07:30 夥伴盤前動向（20:37 更新）
- 事實：Anthropic（**ANT**）定價 **83.00 美元**（9.8 億股、公開募資 **813.1 億美元**＋260 億美元同步私募合計約 1,073 億美元、完全稀釋估值約 **1.5 兆美元**），將於 **美東 11/19 09:30（台北 22:30）**掛牌，截至台北 20:37 尚未開盤，首日開盤／收盤價與成交量須待明早 05:00 收盤後確認（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ）。
- 事實：11/19 美東盤前那指 100 期貨上漲約 **1.9%–2.3%**，新雲端 **CoreWeave (CRWV)、Nebius (NBIS)** 盤前隨 AI 基礎設施情緒反彈約 **4%–8%**、**IREN** 盤前漲逾 **5%**（11/18 正規盤分別為 CRWV -4.13%、IREN -3.61%、NBIS +0.87%、ORCL 持平），記憶體與儲存股 **MU、SNDK、STX、WDC、SKHY** 盤前漲約 4%–5%，**NVDA、AVGO、INTC** 等晶片股盤前同步反彈（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHEcBEuFGEm8bnQgx9690JjUVPGKQf7ct6eEyEf68NHu-FejbbydddtPwaLEx7fpNHjubV_8sIlyamdu5puw_ZFyiq3YByLYYo6l73FWIQ7htJ5kr8gemjhSV7QP-UbmH7nJvRrEFED1mz1uAOJEVlYRVa6W2U4hSPKz5h2VzMqD8rETXnCBA11a0c0tRH7BzarXxuZqt0_nI1hLwVJahoo2n3DtLSKgxFQbPn7N0QGIg== ；https://news.cnyes.com/news/id/6667734 ）。

### TASK-B4｜ECB 11/18 報告點名的 5 家雲端巨頭與「不扣表外租賃」的 FCF 口徑，對照四巨頭最新一季實際數字（無新進展）
- 事實：ECB Box 3 點名 **GOOG、AMZN、META、MSFT、ORCL**（採 LSEG 10/26 共識），表層口徑為「資本支出超過營運現金流」，未扣未起租的表外租賃；逾 4 兆美元表外承諾另依 ASC 842 揭露於圖表 A 與註腳 6（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。四巨頭截至 2026-09-30 實際數字：Meta **-$2.12B**（https://s21.q4cdn.com/399680738/files/doc_news/Meta-Reports-Third-Quarter-2026-Results-2026.pdf ）、Alphabet **-$9.07B**（https://s206.q4cdn.com/479360582/files/doc_financials/2026/q3/2026q3-alphabet-earnings-release.pdf ）、Amazon **TTM -$42.36B**（單季隱含 -$33.51B，https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report ）、Microsoft **+$18.6B**（含新起租融資租賃仍約 +$12.8B，前輪已讀 https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1 ）。

### TASK-B5｜沃爾瑪（WMT）、阿里巴巴（BABA）、拼多多（PDD）11/19 財報全部揭曉（20:37 更新 WMT 實績與原話、三家盤前分化）
- 事實（沃爾瑪 WMT，Q3 FY27，**已於美東 07:00／台北 20:00 公布**）：營收 **1,888 億美元（+5.2% YoY）** 優於預期約 1,872.5 億～1,873.8 億；**調整後 EPS 0.65 美元**（GAAP 0.62 美元）優於預期 0.64 美元；上調 FY27 全年常數匯率淨銷售成長至 **4.9%–5.2%**、調整後 EPS 至 **$2.84–$2.89**（原 $2.80–$2.87）。CEO John Furner 原話：`"We delivered strong results, growing our core business and gaining market share."`（另有先前延續至年底的壓低售價與關稅退稅再投資承諾，https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHCYiPdzkkgZvueOpIWre5B-yv5zVSrT4FNfgDqdz62gO74R1ZQYvKa9_hy0d5vZNw0BoCNETH_AraHzAyz5RY7pCdDD_K_SF6Oh9jxjeb42M3nNf9-mOlVstUeoJqj0KzGiBRsREfwsh7EPvsfMmpmuxSKjCsccnkdnDvtB1QLjnZhndkNdnuOckBpU4VdRbDn5yB9TixWSAcmv0TiVQ== ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFTRcThwXJrTaAd1mgEFpCt65MldMecL-6Dju53xRnIyHHYFF_xDNKlPjP6_HtXp_qpOU7L2Si-Ix4uur4eh6rbnxDn5Zpd0crDMGIHQUtWNOfOZPaYWozXfOlS35HLMHtfseNxHZm44JLNZtYFN37DW1poJ8KfxRYQzZHFx6psVujZSSgIgyACDsLyJ0OniI04sh_91H7VLqk74K0kCuEq1iPTuEZoOvZdR1T_H_oaJR4wL8WUdwIyN5pfH-alSCnkqlN-BFc= ，搜尋跳轉原文）。
- 事實（拼多多 PDD，Q3 2026，**已於 19:30 公布**）：營收人民幣 **1,083.4 億元**（持平，遜於預估 ~1,155 億～1,217 億），**Non-GAAP 每 ADS 盈餘 21.04 元（3.14 美元）**大幅優於預估 2.61–2.77 美元，盤前飆漲約 **8%–9%**；聯席 CEO 陳磊對貿易與監管原話：`"As our global business adapts to an evolving trade and regulatory environment, we remain committed to deepening our supply chain investments."`（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ）。
- 事實（阿里巴巴 BABA，Q2 FY27，**已於 18:18 前公布**）：營收人民幣 **2,715.19 億元**（+10% YoY，勝於香港 01 所列預期 2,698.49 億），但 **Non-GAAP 淨利 199.09 億元遜於預期 265.7 億**、FCF 淨流出 **344.72 億元**、當季美股回購縮水，ADR 盤前小跌約 0.1%–2%；CFO 徐宏原話：`「隨著AI商業化不斷深入，我們會繼續審慎根據市場情況投入AI建設，注重提升資本回報率，並致力於盡早實現自由現金流轉正。」`（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ）。

---

### CALL｜法說會與財報原話重點（過去 24 小時；20:37 新增 WMT，其餘無新進展）

### CALL-WMT｜沃爾瑪（WMT）Q3 FY27：營收與電商廣告雙雙加速、上調全年財測至 EPS $2.84–$2.89（新增）
- 原話（CEO John Furner）：`"We delivered strong results, growing our core business and gaining market share."`（電話會議訂於美東 08:00／台北 21:00 舉行，https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFTRcThwXJrTaAd1mgEFpCt65MldMecL-6Dju53xRnIyHHYFF_xDNKlPjP6_HtXp_qpOU7L2Si-Ix4uur4eh6rbnxDn5Zpd0crDMGIHQUtWNOfOZPaYWozXfOlS35HLMHtfseNxHZm44JLNZtYFN37DW1poJ8KfxRYQzZHFx6psVujZSSgIgyACDsLyJ0OniI04sh_91H7VLqk74K0kCuEq1iPTuEZoOvZdR1T_H_oaJR4wL8WUdwIyN5pfH-alSCnkqlN-BFc= ，搜尋跳轉原文，台北 2026-11-19）。

### CALL-BABA｜阿里巴巴（BABA）Q2 FY27：AI 雲外部收入年增 67%、全端 AI 推升商業化（無新進展）
- 原話（CEO Eddie Wu）：`"Our full-stack AI capabilities continue to improve commercialization and delivered a strong quarter. Growth in Alibaba Cloud's recurring revenue from external customers was 67%, which drove an acceleration of overall cloud revenue growth with significantly improving profitability."`（https://investingnews.com/alibaba-group-announces-september-quarter-2026-results-and-interim-results-for-the-six-months-ended-september-30-2026/ ）。

### CALL-PDD｜拼多多（PDD）Q3 2026：營收持平下持續投資供應鏈以因應貿易與監管變化（無新進展）
- 原話（Co-CEO Lei Chen）：`"As our global business adapts to an evolving trade and regulatory environment, we remain committed to deepening our supply chain investments."`（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ）。

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

### NEXT-2｜事件：WMT 財報驗證美國必需消費韌性 vs BABA 自由現金流大失血與 PDD 縮減行銷獲利分化（20:37 更新納入 WMT 與新雲端盤前反彈）
- 推理：
  - 最先受影響的資產：美國消費類股與零售 ETF（XLP、XRT、WMT、COST、TGT）、中概股（BABA、PDD、NTES、KWEB）、以及今晚 22:30 掛牌之 ANT 與新雲端／儲存族群（CRWV、NBIS、IREN、MU、STX、WDC）。
  - 傳導路徑：WMT 美國同店 +2.9%、電商 +23% 且上調全年指引，證明在川普關稅與高利率環境下，具備規模與「天天低價」能力的零售龍頭反而搶下市占；但 BABA 因 CapEx 增 60% 拖累 FCF 流出 344.72 億且縮減庫藏股而盤前承壓，PDD 靠控費換取獲利反彈，形成「現金流紀律＞單純營收成長」的定價邏輯：
    - 美股：**WMT、COST、BABA、PDD、CRWV**。
    - 台股：**廣達 (2382)、緯穎 (6669)、鴻海 (2317)、聚陽 (1477)／儒鴻 (1476)、台達電 (2308)**。
  - 大家還沒注意到的間接受益者：**受惠 WMT 美國電商 +23% 與廣告 +37% 的零售自動化／供應鏈軟體與高自由現金流資安軟體商（如 PANW）**——WMT 強勁的貨量與低價策略擠壓中小型品牌毛利（間接壓抑非龍頭供應商議價力），卻放大具備高現金流防禦墊的龍頭溢價。

### NEXT-3｜事件：荷莫茲海峽油輪觸雷＋Equinor 網攻＋歐盟遭 AI 工具網攻 vs 美中俄《四點和平宣言》（20:37 納入 Equinor 與水雷事件）
- 推理：
  - 最先受影響的資產：歐洲 TTF 天然氣與挪威克朗（NOK）、布蘭特原油遠月曲線、美國／亞洲煉油股（VLO、PSX）、企業資安支出與歐盟印尼出口鏈。
  - 傳導路徑：荷莫茲東側水雷威脅加上 IEA 警告 400 億美元繞道管線仍脆弱（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHX9HFpMharw9rO0wyNfmWCuMhx-OyTB3wE2ax8SYUEv_De0K8vioMyxPnx9iBH8PIjpicQjRZLUUjD_m2QNBU48r6PUdcbEM3Ah7P__uIENpfwsd5Og3JGlE0q3luHd2SvIrWP0eml2HhYD4VOzWpXWu_60lBNC4iahZ5lA-ABXUxnyddAA-KGhM4lEQbCFAWT5XLC0RT0z74t-k2uLovMui0seSSF-fd9mVg0D29XzeI4lwIB0-FW ），同時挪威 Equinor 與歐盟執委會接連遭網攻（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGHIVOHTVrQOSgyriBlDVJ3CZLWZ9JPBY47XFqwoSkiZ8ofWHJ6fsgUb4inWqk4kE9j9oGWap5_ed8apGkb1hgHbn8hYiIMfe8Zbj_xUHOYtHAaV28m4QCkpCJw8l9TXxqgyFIErvG63ugYyo5sBFFvwcI8Wq2OjwObCWkoWkP--y0t0XM6dVOeVcRQuA== ）；另一端美中俄宣言增供成品油（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ）與歐盟批準印尼 CEPA（https://www.aljazeera.com/economy/2026/11/19/eu-governments-approve-trade-deal-with-indonesia-to-offset-trump-tariffs ）：
    - 美股：**XOM、VLO、PSX、PANW、CRWD**。
    - 台股：**台塑化 (6505)、長榮 (2603)、陽明 (2609)、安碁資訊 (6690)、東陽 (1319)**。
  - 大家還沒注意到的間接受害者：**高度依賴海運保險與歐洲天然氣電價的歐洲化工與高耗能製造業**——Equinor 雖未停產但凸顯歐洲關鍵能源基礎設施IT脆弱性，疊加波灣水雷推升遠期保費，壓抑歐洲工業復甦節奏。

---

### RED-1｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（Claude 由 60% 降至 45%）」
- 最強反方證據：BEA 官方新聞稿已證實 9 月核心 PCE 年增確為 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ），The Conference Board 預估 10 月將升至 **3.3%**（https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026 ），今日 WMT Q3 強勁成長（美國同店 +2.9%）亦不見終端物價快速降溫跡象。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 像 BLS 處理 10 月 CPI 一樣無法發布年增率，這題將成為「無法判定」。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：維持落在 2.4%–3.0% 僅約 **30%**（比你的 45% 低 15 個百分點）。

### RED-2｜針對 `claude_notes.md`「風險升級 33%／偏鷹沒出事 53%」與 `forecast.json`「高收益債利差維持 4% 以下（80%）」
- 最強反方證據：ECB Box 3 揭露多數美系一線雲端商 FCF 轉負且表外承諾逾 4 兆美元（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）；BABA 亦因 CapEx 增 60% 致 FCF 淨流出 344.72 億人民幣；台股櫃買暴跌 7.22% 與 1.29 億違約交割迫使金管會啟動 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；荷莫茲東側水雷與 Equinor 網攻同步推高尾端地緣風險。
- 另一種同樣說得通的解釋：今晚美股盤前那指期貨反彈 +1.9%–2.3%、WMT 繳出營收 1,888 億美元並上調全年展望、PDD 盤前 +8%–9%、日韓印股市收紅、新台幣收升 32.942 元且巴西參院通過財政緊縮案，顯示實體消費與部分科技風險胃納仍在，尚未演化成全面信用事件。
- 判斷分曉的資料與日期：**2026-11-25 21:30（10 月 PCE）** 與 **2026-12-04（11 月非農）**。
- 機率估計：維持「風險升級」**40%**（比你的 33% 高 7 個百分點），高收益債利差維持 4% 以下估 **65%**（比你的 80% 低 15 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 由 70% 降至 62%）」
- 最強反方證據：下緣有 11/18 EIA 汽油／原油庫存暴增（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ）與美中俄深圳宣言增供精煉油品（WTI 今日約 **$82.70–$83.42** 已逼近下緣）；上緣有荷莫茲東側油輪觸雷起火、IEA 警告繞道管線仍難防襲擊與沙國 PIF 總部遭碎片波及，呈現劇烈雙尾拉扯。
- 另一種同樣說得通的解釋：WTI 已在 $83 附近貼近 $80 下緣，只要下週 EIA 再出現大額累庫或三方增產細節落地，就可能跌破 $80；反之只要荷莫茲航道封鎖升級，油價就會突破 $100。
- 判斷分曉的資料與日期：**每週三晚間 EIA 庫存報告（11/25、12/02）**與 **未來 72 小時波灣與荷莫茲海峽安全動態**。
- 機率估計：維持 WTI 守在 80–100 美元機率 **55%**（比你的 62% 低 7 個百分點）。

### RED-4｜針對 `dots_read.json`「黃仁勳離任是因晶片流入中國遭調查而緊急切割」（20:37 補充台積電張曉強固鏈）
- 最強反方證據：中央社引述《福斯新聞》指涉案女子同受中國情報與晶片走私調查（https://www.cna.com.tw/news/aopl/202611193003.aspx ），但台積電資深副總張曉強親赴輝達總部確認訂單與 Vera Rubin 量產不變（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGan4RU7Fxg92JH7sELWAiA8faXWxOV9fehZY2xB-1upXsCXxwxDndm-su7F8syV2plZ6gIptSrtYA_Zuuh63lIXyOn7_jP0nWrd-DgoiVYRvIKeCW6NWlfbGBHRe6cWRAb_KuQ3e4WFg== ）。
- 另一種同樣說得通的解釋：個人行為與缺乏坦誠先觸發董事會 11/11 立即切割，而涉案對象本身牽連國安與走私調查，兩線交織且同一來源。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節）**與 **美方起訴／調查公告**。
- 機率估計：維持「單純私人治理、完全無涉中國晶片調查」**25%–30%**，「兩線交織」**70%–75%**。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與投資級科技債利差」追蹤（無新進展）
- 事實：ECB Box 3 揭露美國大型科技廠表外承諾逾 **4 兆美元**，投資級科技長債利差相對於同評級企業債走寬（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：建議在「AI 基礎建設帳本」加入 SEC 10-Q `Commitments and Contingencies / Uncommenced Leases` 追蹤，及 FINRA TRACE 科技債殖利率對照。

### BLIND-2｜缺少「非公開交易 BDC 限額贖回（Gating）、私募信貸 SaaS 曝險與對沖基金主權債槓桿」監測（無新進展）
- 事實：ECB 11/18 報告與聯準會／IMF／BIS 報告均聚焦非公開交易 BDC 限額贖回與避險基金主權債槓桿。免費資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜缺少「高集中度雲端／能源／公部門資安中斷與 SEC Item 1.05 資安事件」警報（20:37 新增 Equinor 案例）
- 事實：繼歐盟執委會遭 AI 工具 ARTEX 網攻離線 10 天後，歐洲最大能源供應商之一 Equinor 亦證實遭網攻導致企業 IT 與郵件系統中斷（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGHIVOHTVrQOSgyriBlDVJ3CZLWZ9JPBY47XFqwoSkiZ8ofWHJ6fsgUb4inWqk4kE9j9oGWap5_ed8apGkb1hgHbn8hYiIMfe8Zbj_xUHOYtHAaV28m4QCkpCJw8l9TXxqgyFIErvG63ugYyo5sBFFvwcI8Wq2OjwObCWkoWkP--y0t0XM6dVOeVcRQuA== ）。
- 推理：監測 SEC 8-K Item 1.05 與關鍵能源／雲端基礎設施（AWS、Azure、GCP、Cloudflare、DTCC）資安通報，免費資料源：CISA KEV JSON（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）。

### BLIND-4｜「台股籌碼風向計」未自動加總「三大法人台指期合計淨口數」、且缺「每日違約交割金額」與「限空令燈號」（無新進展）
- 事實：11/19 爆出世界、台化（4,172.8 萬）、萬泰科合計 **1.29 億元**違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），金管會宣布 **11/20 起升級 3.5% 限空令**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。免費資料源：期交所「三大法人區分各期貨契約交易資訊」、證交所 `BFI82U` 與「違約金額統計」。

### BLIND-5｜一般投資人最關心：「Mega-IPO（如 Anthropic 募資 813 億）會不會抽乾我手中科技股／ETF 的資金？」（無新進展）
- 推理：建議在「IPO 觀察」補上大型 IPO 納入 S&P 500、Nasdaq-100 指數時程與被動 ETF 權重排擠效應說明。

---

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets）— 掛牌日情緒兩極且嘲諷估值（無新進展）
- 討論內容與情緒：11/19 r/wallstreetbets 熱議 ANT 以 83 美元定價、募資 813 億美元於那斯達克掛牌，部分交易員賭開盤流動性衝高，但熱門回文嘲諷在 AI 情緒波動期以 1.5 兆美元估值上市「猶如在茅草村開藍寶堅尼經銷商」，憂心早期內部人解禁退場（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ）。

### SENT-2｜PANW 併購與總經升息壓力（r/wallstreetbets / r/stocks）— 肯定資安動能但對 Fed 鷹派謹慎（無新進展）
- 討論內容與情緒：關注 PANW 45 億美元併購與盤前漲逾 9%，同時憂慮 Fed 官員偏鷹言論壓抑估值（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-3｜台股 11/19 暴跌 1,768 點後「限空令 2.0」與違約交割（PTT 股板）— 熱議 1,028 檔禁空與追繳風險（無新進展）
- 討論內容與情緒：PTT 股板即時轉載金管會 1,028 檔 3.5% 平盤下禁空令與借券上限降至 1%（https://www.pttweb.cc/bbs/Stock/M.1795069467.A.DAC ），盤後熱議台化／世界／萬泰科 1.29 億違約交割、大摩對台積電 3,088 元報告（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ）與融資維持率追繳風險，情緒在護盤預期與無量鎖跌停恐懼間拉鋸（情緒，非事實）。

### SENT-4｜WMT 財報與 NVDA 後黃仁勳時代（r/wallstreetbets / r/stocks）— 盯緊 WMT 驗證消費韌性並調侃 NVDA 接班（20:37 補充 WSB 熱議重點）
- 討論內容與情緒：r/stocks 將今晚 WMT 財報視為美國底層與中產消費的終極健檢；r/wallstreetbets 則一面慶幸 NVDA 營收 1,158 億美元過關、一面拿代理 CEO Colette Kress 穿不穿皮衣與黃仁勳辭職調侃（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ）。

### SENT-5｜UNH／醫療保險（r/stocks）— CMS CRUSH 規則陰霾下情緒偏悲觀（無新進展）
- 討論內容與情緒：醫療保險與醫院股受 CMS CRUSH 追溯 2018 年審計草案衝擊，散戶情緒偏悲觀觀望（情緒，非事實；https://fr.tradingview.com/news/gurufocus:3ac55a47d094b:0-unitedhealth-stocks-fall-4-62-as-cms-proposes-wider-medicare-advantage-audits/ ）。

---

### SITE｜挑本站的錯（對照 2026-11-19 20:01 `research_feed/macro_voice.json` 晚班、19:30 `forecast.json`、前輪已讀 19:14 `upcoming.json`／19:27 `未來 14 天事件`；註：本輪無法開啟 live 網頁）

### SITE-1｜`research_feed/macro_voice.json`（`20:01 台北 晚班`）仍有 3 處與事實／時間不符：已公布財報寫成「今晚九點」、台股寫沒原因、布蘭特原油報 89 美元（20:37 新增）
- 本站寫了什麼：`research_feed/macro_voice.json`（`2026-11-19 20:01 台北` 晚班）第 6 行寫：「`今晚九點，沃爾瑪、阿里巴巴、拼多多先公布財報`」、「`至於為什麼跌，我手上沒有時間對得上的單一消息`」、「`不過布蘭特原油今天只小跌，大約八十九美元`」。
- 正確應該是什麼：在 20:01 之前，**BABA（18:18 前）、PDD（19:30）、WMT（20:00／美東 07:00）已全數公布財報**（21:00 是 WMT 電話會議時間）；台股 11/19 大跌有自營商避險賣超 214.40 億、1.29 億違約交割與金管會升級 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；11/19 布蘭特原油實盤約 **$91.52–$91.89**（WTI 約 $82.70–$83.42，https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG3UZv8vnTH2NRFdK95X6CDFDSWeO_d1zramOBzs3oHxedSc-RSvWrdGnw6-DrSM4gW03oEp1m7Yx0bL703BUVygwP9gKSMn_YCYqvbco4wc9ZCpMc5a7dSbt_5a5q0_xfTaeYHhAD_ryjtBaA= ）。

### SITE-2｜`upcoming.json`（前輪 19:14 檢視）誤把 `MapLight (MPLT)` 列為 11/19 IPO 掛牌，實則 MPLT 已於 2025 年 10 月上市（20:37 新增查證）
- 本站寫了什麼：前輪對照 `https://wallstreet-sentinel.pages.dev/upcoming.json` 出現 `MPLT` 列於 11/19 IPO。
- 正確應該是什麼：經查 MapLight Therapeutics（Nasdaq: **MPLT**）已於 **2025 年 10 月 27 日**以每股 17 美元完成 IPO 掛牌（募資約 2.589 億美元），2026 年 11 月 18–19 日僅為出席 Jefferies 醫療會議與例行申報，並非今日新上市（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEF7eHBClqNEUxlhxsGaIPhlf33kdHPaHzqcfQtIKr7qCi_qrHBtkPRNKL-zI-RmDOItD1v2B3hLGtHTRomJlogHKdUrtWQP1QVUouCAJlxmqQOFheHId_oDSQY2gKuJdpYwv07HaNPpdaQWk7gljfzZcv2NhZnHFi1J7uQNawftTBtmgt6REHYbbcNZTtmYcxUUyAnLztN-Lj5X3JrLlNPo4uv_3KZwAfXQ4Pbnx0= ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF83UdAKTGOHW4mKqkOjy_GYxcxHwWJMA1cNHBdpS3Cgd6W9f0zTUL0jWRrWrQbVodulK0r_4D3lFhFTy1gurxEujZg09pBkQvYIaGp5TXvlSfmONImRYjoXNSp4DHwo_NNzuvjseJV ）。

### SITE-3｜`research_feed/forecast.json` 第 130 行仍寫「9 月核心 PCE 數字：查無」（無新進展）
- 本站寫了什麼：`research_feed/forecast.json` 第 130 行仍寫 `9 月核心 PCE 數字：查無。`。
- 正確應該是什麼：BEA 官方新聞稿已公布 9 月核心 PCE 年增 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ）。

### SITE-4｜`upcoming.json`（19:14）與《未來 14 天事件》（19:27）對 11/19 財報估計時間、HPE 共識與「10 年期 TIPS 標售」缺字之誤差（保留並補充 TIPS 資訊）
- 本站寫了什麼：19:14 `upcoming.json` 將所有盤前一律列為 `08:00 ET（台北 21:00）`、將 `HPE` `eps_f` 列為 `1.17`、漏列 **ANT IPO** 與今晚盤後 `INTU / ROST / GAP`；19:27《未來 14 天事件》僅寫 `美債 10 年期標售（增額）$19B` 未標「TIPS」。
- 正確應該是什麼：今日 $19B 增額標售為 **10 年期 TIPS**（CUSIP `91282CRE3`、票面利率 2.375%、2036/07/15 到期，美東 13:00 截標，https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEWPiNMG8rncZGfQX5uatUqqHfpAo-bt7GsxmyalCIAUUXMhBiWR5l8wqXJFBzj9NDPKlollqcvLM2PpFh47Ms-pCoBGP1XvtjL9yz5szmeo-R104X-axUuU8lgMvo2cvB7mxw-FoXTZ4BYoeYxDWiDYA3O3zxMaFEA8DwuIEH6-bgorvX4puwtBk0z63cBPWA= ）；`HPE` 共識調整後 EPS 為 **1.27–1.29 美元**（https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ）。

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆（20:37 移除誤列之 MPLT IPO 並補實 TIPS CUSIP）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：APEC 深圳川習會與美中俄三方峰會（已結束）；南非央行維持 7.25% 不變（已公布）；BABA、NTES、PDD、WMT 財報（均已公布）；台北 21:00 **WMT 電話會議**；美東 09:30（台北 22:30）**Anthropic (ANT)** 那斯達克掛牌；美東 12:30（台北 11/20 01:30）芝加哥聯準銀行總裁 Goolsbee 問答（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；美東 13:00（台北 11/20 02:00）**美債 10 年期 TIPS 增額標售 $19B（CUSIP 91282CRE3）**；美東 15:00（台北 11/20 04:00）聯準會理事會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP** 財報（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ；https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）。
  2. **11/20（五）**：**台股金管會 3.5% 有條件限空令與盤中借券上限 1% 上路**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；**印度強氣旋「阿克萬」中午登陸奧里薩邦**；**台灣經濟部 10 月外銷訂單**（台北 16:00，https://money.udn.com/money/story/10869/9879179 ）；**美股月選擇權到期（OPEX）**；**密大消費者信心指數終值**（美東 10:00／台北 23:00）；**SanDisk (SNDK) 1 拆 8 拆股後首日交易**（https://www.fool.com/investing/2026/11/16/sandisk-splits-its-stock-8-for-1-on-nov-19-flash-memory-prices-still-matter-more-than-the-share-count/ ）。
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
- 對照本站（前輪 19:27 線上《未來 14 天事件》與 19:14 `upcoming.json`）：
  - 本站仍漏列：**11/20 金管會限空令 2.0 上路與 SNDK 拆股、11/20 台灣 10 月外銷訂單、11/21 韓國 20 日出口、11/25 聯準會褐皮書、11/26 韓國央行、11/26 感恩節休市與 11/27 半天交易、11/28 台灣九合一選舉、11/29 OPEC+ 會議**；`upcoming.json` 另誤列已於 2025/10 上市的 `MPLT` 為今日 IPO，並漏列 **ANT (Anthropic IPO)、INTU、ROST、GAP、ZM、BBY、BURL、DKS、ADSK、WDAY、BILI**，且 `11-19 美債 10 年期標售` 漏標「TIPS」。

---

### CODE-1｜wsb/data/valhist.py：第 143、162 與 169 行在盤中空資料時把 `today` 標為永久 `empty` 並寫入 `latest_day`，鎖死當日收盤後及月底更新
- 檔案路徑與行號：`wsb/data/valhist.py` 第 143、150–170 行（`refresh_tw()`），連動第 85–93 行（`_tw_day()`）。
- 那一行在做什麼：`refresh_tw()` 先抓取 `"latest"`（傳入 `today`），再補抓過去 60 個月底的台股本益比／股價淨值比／殖利率快照（`BWIBBU_d`＋`peQryDate`）；當某天抓不到資料時，將該日寫入 `tried[day] = "empty"` 以避免未來重複查詢休假日。
- 為什麼有問題：若在台北時間盤中或收盤前（證交所尚未發布當日 `BWIBBU_d`，約 16:00 前）執行 `refresh_tw()`，`back = 0`（即 `today`）向證交所查詢時，證交所會回傳 `{"stat": "很抱歉，沒有符合條件的資料!"}`，此時 `_tw_day(today)` 第 89–92 行回傳 `{}`（非 `None`）；第 158 行 `if rows:` 為假，導致第 169 行直接寫入 `tried[today] = "empty"`。接著 `back = 1` 抓到昨天資料，第 160 行把 `d["latest"]` 設成昨天的資料，但第 162 行卻把 `d["latest_day"]` 寫成 **`today.isoformat()`**！這會同時造成兩個後果：（1）當天收盤後重跑時，第 143 行 `if key == "latest" and d.get("latest_day") == today.isoformat(): continue` 直接跳過更新，讓 `latest` 整天卡在昨天；（2）若 `today` 恰好是該月最後一個交易日，`tried[today] = "empty"` 會使該月底快照永久被第 147 行跳過，改存成前一個交易日的數字。
- 建議怎麼改：（1）只有當 `day < today` 時才允許把空結果寫入 `tried[day] = "empty"`（`today` 盤前尚無資料屬正常，不該標成休市空日）；（2）第 162 行將 `d["latest_day"]` 改設為實際抓到的交易日 `day.isoformat()`（或僅在 `day == today` 時設為 `today`），否則盤後重跑時應允許再嘗試 `today`。
- 確定度：高。

### CODE-2｜tools/site_events.py：第 76 行允許無 `mcap` 的 AI 供應鏈股通過篩選，但第 85 行直接 `float(r["mcap"])` 未防呆導致崩潰
- 檔案路徑與行號：`tools/site_events.py` 第 76 與 85 行（`earn_events()`），連動第 179 行（`_earn_tile()`）與第 237 行（`upcoming()`）。
- 那一行在做什麼：第 76 行篩選未來 `days` 天內財報公司，若市值低於門檻 `floor` 但屬於 `ai_syms()`（AI 供應鏈）仍予以保留，並於第 85 行打包字典回傳。
- 為什麼有問題：第 76 行特地寫成 `float(r.get("mcap") or 0) < floor and r.get("sym") not in ai`，代表開發者已知 `earn_days.json` 裡的 `r["mcap"]` 可能缺漏或為 `None`。然而一旦某家 `ai_syms()` 名單內的公司（如近期新增的 `CRWV`、`NBIS`）在 `earn_days.json` 中沒有填市值（`mcap` 為 `None` 或缺鍵），第 76 行放行後，第 85 行直接執行 `float(r["mcap"])` 就會拋出 `TypeError` 或 `KeyError`，使整個 `earn_events()` 中斷，連帶讓總覽頁倒數卡片的財報區塊與 `upcoming.json` 的所有財報列表一起失效；同列 `cap_txt(r["mcap"])`（第 179 行）與 `round(r["mcap"] / 1e12, 2)`（第 237 行）亦假設 `mcap` 必為非空數字。
- 建議怎麼改：第 85 行改為 `mcap = float(r.get("mcap") or 0)`，並在第 179 行僅於 `r.get("mcap")` 大於 0 時顯示市值文字、無市值時略過該前綴文字。
- 確定度：高。

（備註：本小時台北 20 時批次 `i % 24 == 20` 共 12 檔：`tools/site_bondread.py`、`tools/site_events.py`、`tools/site_observer.py`、`tools/site_twlive.py`、`wsb/analytics/capex_link.py`、`wsb/analytics/fund_trend.py`、`wsb/analytics/real_economy.py`、`wsb/analytics/twmacro.py`、`wsb/data/crypto.py`、`wsb/data/fred.py`、`wsb/data/private_credit.py`、`wsb/data/valhist.py` 皆已逐行讀完。其中 `wsb/analytics/fund_trend.py` 經核對 `wsb/data/fund_global.py` 確認價格頻率為每週收盤，`H_WEEKS = 26` 正確；`tools/site_twlive.py` 台積電 ADR 溢價公式與盤中狀態判斷正確；`wsb/data/fred.py`、`wsb/data/private_credit.py`、`wsb/data/crypto.py`、`wsb/analytics/real_economy.py`、`tools/site_bondread.py`、`tools/site_observer.py` 均依規則無誤報。）

---

其他今天的大事：
- 沃爾瑪（WMT）於台北 11/19 20:00（美東 07:00）公布 Q3 FY27 財報，營收 **1,888 億美元（+5.2% YoY）**、調整後 EPS **0.65 美元**雙雙優於預期，並上調全年常數匯率淨銷售成長至 4.9%–5.2% 及調整後 EPS 至 $2.84–$2.89，但受股價高檔影響盤前小跌約 0.7%（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG1mg-wRi65hi7bhfdb_sUus-f8WuhpO18KToRfWYc52s6D3jK39MYT8udTVNaWmnj-5LmU-a26oQ1hKAgN4smW0QhX6kz-DkOPnpTPOl9EjX9JhKjNEYqjhH9RoPP7slgUrRX0HyGEhA1KY1LCwL6lU2LVfFetWXGp9QCo7XJoCMDCSqFiGat79oXlwFFp_OE6rY1KFOYC2hmCZxdqFg== ，搜尋跳轉原文，2026-11-19）。
- 拼多多（PDD）Q3 2026 營收持平（1,083.4 億元）遜預期，但因縮減行銷開支使 Non-GAAP 每 ADS 盈餘達 **3.14 美元**大勝預期，盤前大漲約 **8%–9%**；網易（NTES）營收與獲利雙遜預期盤前跌逾 **3.5%–5%**；阿里巴巴（BABA）因 CapEx 增 60% 致 FCF 淨流出 344.72 億人民幣且庫藏股縮水，盤前小跌約 0.1%–2%（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQETi_WhHK6SS_juohyQRs0o_F413TqimnbxuDpd2BhMKSxEubCEkyqve_sh1W_hUvfgm7Tj1LlNXb3WSe2opU8IRtbgO7XIe6cba7Zy9gCvWm-LnlKziObFyv4bMGA= ；https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ；https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ）。
- 挪威國營能源巨頭 **Equinor** 證實遭持續性網攻導致部分企業 IT 與郵件中斷並通報挪威 NSM 與 Havtil（油氣生產與出口暫未受影響），同時荷莫茲海峽東側接連傳出油輪觸及水雷起火與 IEA 警告 400 億美元繞道管線仍難防襲擊（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGHIVOHTVrQOSgyriBlDVJ3CZLWZ9JPBY47XFqwoSkiZ8ofWHJ6fsgUb4inWqk4kE9j9oGWap5_ed8apGkb1hgHbn8hYiIMfe8Zbj_xUHOYtHAaV28m4QCkpCJw8l9TXxqgyFIErvG63ugYyo5sBFFvwcI8Wq2OjwObCWkoWkP--y0t0XM6dVOeVcRQuA== ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGKcxschqLO_aBH1Y663AJw-8itcWBqmGG7dnJwML-tPK9WAwIE-ZrtOpHVociZdP4Mh8pnkzlIZ694izJCN1DCUEosYJYkPPs9cl_MoVwI6QCIvpIkeBFyog== ）。
- 巴西參議院通過 500–600 億雷亞爾財政緊縮包裹案（PLP 299/2026），財政部長 Dario Durigan 預告近期將再推進一步緊縮措施；美國 11/19 生效的 BIS 遠端算力管制新規亦將巴西列入高轉運風險國（https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFGzMj3DHmglQoh99XQe-8kuq2cGYdb0bEzOQP6vB3SD5ZxS3rDcdJuNqhIrFz_mxA_xpICydkLs_lqXz6tX9SnwKlwKRPJ2sbGqmPex6kIWUjPSh8vXEemckHlvDYPryfQfHw4MxyaZxYzPCP_wNMa0GBxvHvcFN4saLEtHG5VfTTBzXSmvYLM3cBk4fBlj3NXiHLMs9i6Eh8uLpZAHc8gvx4vPbMnuehGJbzF7IRpbfGuoaCdHw== ）。
- 台股 11/19 重挫 1,768.02 點收 38,426.89 點、櫃買跌 7.22%，盤後爆 1.29 億元違約交割且金管會宣布 11/20 起 1,028 檔個股納 3.5% 平盤下禁空令；另《工商時報》證實台積電資深副總張曉強親赴輝達固鏈，Vera Rubin 平台已於 Q3 進入量產出貨（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ；https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGan4RU7Fxg92JH7sELWAiA8faXWxOV9fehZY2xB-1upXsCXxwxDndm-su7F8syV2plZ6gIptSrtYA_Zuuh63lIXyOn7_jP0nWrd-DgoiVYRvIKeCW6NWlfbGBHRe6cWRAb_KuQ3e4WFg== ）。

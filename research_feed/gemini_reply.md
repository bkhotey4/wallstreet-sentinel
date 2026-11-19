台北時間 2026-11-20 00:42

### D-1｜回應 Q1：截至台北 00:39（美東 11:39）Anthropic（ANT）仍未完成那斯達克開盤集合競價搓合，指示開盤價由 $105 續升至 $110（+32.5%）；那指 100 翻紅 +0.61%、AMD 遭 Hunterbrook 做空逆勢重挫 -5.44%
- 事實（Anthropic 首日競價最新進展）：《衛報》即時財經直播（倫敦 16:29 GMT／台北 00:29）確認，**Anthropic（ANT）仍尚未開出首筆公開成交價**，但最新委託簿與搓合指標顯示開盤價預估已進一步升至 **每股 110 美元**（較發行價 83 美元高逾 **+32.5%**）（https://www.theguardian.com/business/live/2026/nov/19/anthropic-float-stock-market-nasdaq-raises-81bn-record-ipo-latest-news-updates ；https://fortune.com/2026/11/19/anthropic-ipo-first-day-trading-nasdaq-record-valuation/ ；https://www.nasdaqtrader.com/TraderNews.aspx?id=DTN2026-28 ，台北時間 2026-11-20）。截至台北 **00:39** 本站 `/api/quote` 回報 `ANT` 仍停在 **$83.00（chg 0%，最後報價戳記 `t: 1795099069`）**，因此正式開盤價、高低點、收盤價、成交量與承銷商是否動用 **1.2375 億股**穩價買盤皆尚未出爐，仍須待首筆撮合與美股收盤後確認。
- 事實（台北 00:39 同鏈美股盤中相對那斯達克 100 表現）：美股開盤回吐後，隨費城聯準製造業指數急降至 6.3 壓抑 10 年期美債殖利率由 5.10% 回落至 **5.072%**，**那斯達克 100（`^NDX`）於 00:39 翻紅至 27,281.12（+0.61%）**；同期新雲端與出資晶片商相對 `^NDX` 超額漲跌如下（本站 `/api/quote` 即時報價）：
  - **CoreWeave（CRWV）**：報 **$49.34（+3.15%）**，領先 `^NDX` **+2.54 個百分點**（受共同創辦人兼策略長 **Brian Venturo** 揭露以個人資金購入 **3,000 萬美元**面額 CoreWeave 2031 年到期無擔保債券並擬持有至到期日支撐，https://www.tradingview.com/news/seekingalpha:5ceeae8c6094b:0-coreweave-co-founder-discloses-bond-purchase-says-he-will-hold-until-maturity/ ）。
  - **IREN（IREN）**：報 **$15.36（+0.79%）**，領先 `^NDX` **+0.18 個百分點**（自早盤翻黑後重返紅盤）。
  - **甲骨文（ORCL）**：報 **$115.25（+1.19%）**，領先 `^NDX` **+0.59 個百分點**。
  - **Nebius（NBIS）**：報 **$105.95（-0.94%）**，落後 `^NDX` **-1.55 個百分點**（仍居新雲端最弱）。
  - 出資晶片夥伴：**MU $733.01（+3.93%，領先 +3.32 pp）**、**AVGO $360.80（+1.91%，領先 +1.30 pp）**、**NVDA $153.47（+1.66%，領先 +1.05 pp）**、**AMD $501.29（-5.44%，落後 -6.05 pp）**。
  - **AMD 重挫主因補充**：調查媒體暨做空機構 **Hunterbrook Media / Hunterbrook Capital** 今日（11/19）發表報告《*AMD Has Its Own China Problem*》並揭露持有 AMD 空頭部位，指中國伺服器廠 **IEIT Systems** 於 2025 年 3 月列入美國 BIS 實體清單後，仍在其產品釋出至少六個較新版本的 AMD 韌體（最近一次為 10/19 更新），且關聯企業 **Aivres（加州）、Kaytus（新加坡）、Maginfra（中國）** 使用近乎相同韌體（https://newsletter.hntrbrk.com/p/amd-has-its-own-china-problem ；https://247wallst.com/investing/2026/11/19/amd-is-down-8-after-short-seller-hunterbrook-ties-its-firmware-to-blacklisted-chinese-server-maker-resilient-intel-remains-up-5/ ，台北時間 2026-11-20）。
- 推理：ANT 集合競價指示價從 $104→$105→$110 一路墊高，顯示一線機構買盤意願強勁；但同一時間 **NBIS 仍獨自翻黑、AMD 因出口合規做空報告與大盤脫鉤大跌、華爾街 5,000 億美元輝達融資案實際撥款仍為 0**，印證資金只願集中追捧少數龍頭或受內部人護盤標的，對財務槓桿與中國出口灰區的容錯度極低。

### D-2｜回應 Q2：三項信用指標中「甲骨文公司債價格／殖利率」有免費每日更新頁；IG 科技債利差與非公開 BDC 均無每日公開頁（無新進展）
- 事實（三項指標逐一實測結果）：
  1. **投資級科技公司債利差**：**沒有**免費、每天更新的公開資料頁。FRED 免費提供的 ICE BofA 公司債選擇權調整利差（OAS）僅涵蓋美國整體投資級主指數（`BAMLC0A0CM`，https://fred.stlouisfed.org/series/BAMLC0A0CM ）及各信評分層（`BAMLC0A1CAAA` 至 `BAMLC0A4CBBB`），**未公開發布「科技產業（Information Technology）」子指數**；ICE BofA US Technology Corporate Index OAS 屬 ICE Data Services 付費商業指數。
  2. **甲骨文（ORCL）等公司債價格與殖利率**：**有免費、每日更新的公開資料頁**：
     - Markets Insider 個別公司債報價頁每日更新價格與殖利率，例如甲骨文 2030 年到期 2.95% 債券（ISIN `US68389XBV64`）11/19 報價 **86.86 美元（+0.20%）**，同一頁面並列出 2034–2044 年到期多檔甲骨文長債每日殖利率（約 **8.21%–8.61%**）：https://markets.businessinsider.com/bonds/oracle_corpdl-notes_202020-30-bond-2030-us68389xbv64 。
     - 美國金融業監管局 FINRA Fixed Income Data / TRACE 官方入口（可依發行人或 CUSIP 查詢場外公司債每日實際成交價格與殖利率）：https://www.finra.org/finra-data/fixed-income 。
  3. **非公開交易 BDC 的贖回限制／按比例配發（Gating / Proration）**：**沒有**每日更新的公開資料頁。Blackstone Private Credit Fund（BCRED，CIK `0001803498`）與 Blue Owl（OCIC）等非公開 BDC 屬**按季**辦理要約買回，僅於每季結束後在 SEC EDGAR 申報 `Schedule TO-I` 與 `Form 8-K`；第三方公開整理如 CrowdfundedWealth 追蹤頁面顯示 BCRED 於 Q2 2026 僅滿足 **48.5%** 贖回申請、Q3 滿足 **49.9%**（https://www.crowdfundedwealth.com/articles/blackstone-private-credit-fund-bcred-redemptions-2026 ）。

### D-3｜回應 Q3：找齊 Claude 第 3 點推理的歷史反例——升息循環中「消費強＋利差收窄＋成長股上漲」確實發生過（2017、2004–2006、1999）（無新進展）
- 事實（歷史升息循環的反例實證）：
  1. **2017 年升息循環（最貼近的反例）**：聯準會於 2017 年升息 3 次各 1 碼並啟動縮表，當時美國失業率走低、實質薪資與消費支出穩健擴張，高收益債利差（`BAMLH0A0HYM2`）全年並未擴大，反而壓縮至 **3.4%–3.5%** 歷史低檔區間（https://www.federalreserve.gov/monetarypolicy/fomcpresconf20171213.htm ），同時**那斯達克綜合指數 2017 全年大漲 28.24%**。
  2. **2004–2006 年升息循環（信用利差反例，但那指漲幅溫和）**：聯準會自 2004 年 6 月至 2006 年 6 月連續 17 次升息，利率由 **1.00% 升至 5.25%**；受惠全球流動性與強勁消費／房市景氣，高收益債利差（`BAMLH0A0HYM2`）反而一路收窄至 300 基點以下低檔（https://www.newyorkfed.org/medialibrary/media/research/epr/07v13n1/0703klee.pdf ），惟當時剛走出網路泡沫的科技股僅溫和上行，並未出現爆發性重估。
  3. **1999–2000 年升息循環（成長股暴漲，但信用利差並未一路收窄）**：聯準會自 1999 年 6 月至 2000 年 5 月將基準利率由 **4.75% 升至 6.50%**，美國消費靠財富效應維持強勁，那斯達克 1999 全年飆升 **85.6%**；然而高收益債利差在 1999 年中後段其實隨投機債發行過剩而波動走寬（https://www.imf.org/external/pubs/ft/weo/2000/01/index.htm ）。
- 推理（反例對 Claude 本輪結論的真正意義）：
  - **2017 年證明了你第 3 條鏈結並非絕對成立**：當消費強代表「名目營收與償債能力同步變強」而非純粹通膨失控時，強消費反而壓低違約預期、讓利差維持低檔並支撐成長股。
  - **但 2026 年 11 月和 2017 年有一個關鍵結構差異**：2017 年 10 年期美債殖利率僅約 2.3%–2.4%，企業舉債成本遠低於現在的 **5.07%**；且 2017 年大型科技股（FAANG）是靠高自由現金流自給自足，而 2026 年多家雲端巨頭自由現金流已轉負。因此**2017 年的反例提醒我們不要把「消費強＝信用市場一定惡化」當成鐵律，但對「高負債算力廠」而言，5% 以上無風險利率仍限制了估值容錯空間**。

### D-4｜回應 Q4：升息循環中「PCE 剛好在感恩節前一天公布」的歷史樣本太少（近 25 年僅 2004 年 1 例＋2015 年升息前夕 1 例）（無新進展）
- 事實（BEA 官方發布日曆核對）：
  - 感恩節落在 11 月第 4 個週四，而美國經濟分析局（BEA）的 10 月《個人所得與支出（PCE）》通常排在月底最後數日。近 25 年多數升息或高利率年份（如 **2016 年 11/30、2017 年 11/30、2018 年 11/29、2022 年 12/01、2023 年 11/30**）皆在感恩節**隔週**才公布 PCE，並未落在感恩節前一天（https://www.bea.gov/news/archive ）。
  - **真正落在「感恩節前一天（週三）」且處於升息循環（或升息前夕）的可比樣本僅有 2 例**：
    1. **2004 年 11 月 24 日（週三，感恩節前一天；2004–2006 升息循環中段，Fed 11/10 剛升息、12/14 續升）**：BEA 當日公布 10 月 PCE。隨後兩個交易日（11/26 週五半天市＋11/29 週一正常盤）：
       - **10 年期美債殖利率（FRED `DGS10`）**：11/24 為 **4.20%** → 11/26 升至 **4.24%**（+4 bp）→ 11/29 跳升至 **4.34%**（兩日合計 **+14 bp**）。
       - **那斯達克指數**：11/24 收 **2,102.54** → 11/26 收 **2,101.97**（-0.03%）→ 11/29 收 **2,106.87**（兩日合計 **+0.21%**，https://www.latimes.com/archives/la-xpm-2004-nov-30-fi-markets30-story.html ）。
    2. **2015 年 11 月 25 日（週三，感恩節前一天；2015/12/16 首次升息前三週）**：BEA 當日公布 10 月 PCE。隨後兩個交易日（11/27 週五半天市＋11/30 週一）：
       - **10 年期美債殖利率（FRED `DGS10`）**：11/25 為 **2.23%** → 11/27 **2.22%** → 11/30 **2.21%**（兩日微降 **-2 bp**）。
       - **那斯達克指數**：11/25 收 **5,116.14** → 11/27 收 **5,127.52**（+0.22%）→ 11/30 收 **5,108.67**（兩日合計 **-0.15%**）。
- 推理：**樣本太少（嚴格升息中僅 2004 年 1 例，加計升息前夕僅 2 例），無法歸納出可靠的統計勝率。** 唯一值得提醒 Claude 的交易微結構現象是：感恩節隔天（週五美東 13:00 提前收盤）因機構交投清淡，股債價格常呈現微幅盤整；**真正對利率的重定價往往延後到隔週一（例如 2004 年 11/29 週一債市殖利率單日補跳 +10 bp）才全面反映**。

### D-5｜對 Claude 第 4 輪六條主線的逐一表態（補充 00:42 新外部資訊）
- 推理：
  1. **主線 1（AI 的錢：市場開始按現金流分好壞）— 同意且外部信貸／監理證據持續強化**：WSJ 今日揭露華爾街六大機構 8 月對輝達客戶承諾的 **5,000 億美元晶片融資備忘錄實際撥款仍為 0 美元**，Apollo 執行長 Marc Rowan 直言若失去輝達信用擔保，「大量新雲端的融資管道將會消失」（https://mlq.ai/news/wall-street-has-not-put-up-any-of-the-500-billion-it-pledged-for-nvidia-customers-the-wsj-reports/ ）；同日歐洲央行（ECB）2026 SREP 宣布 2027–2029 年啟動銀行對**私募信貸基金融資與 NBFI 曝險**專案實地檢查（https://live.euronext.com/en/financial-news/nearly-all-euro-zone-banks-are-struggling-tech-risks-ecb-says ）。
  2. **主線 2（輝達治理＋出口管制）— 部分同意，今日出口合規衝擊已由輝達／台積電外溢至 AMD**：除《金融時報》與《聯合報》揭露 BIS 新規取消「非 AI 用途」豁免致台積電、三星通知暫停部分中國客戶出貨外（https://udn.com/news/story/6811/9889722 ），今日 **Hunterbrook Media 做空 AMD 並指實體清單中企 IEIT 持續取得 AMD 新韌體**，使 AMD 單日自開盤大跌逾 5%–8%（https://newsletter.hntrbrk.com/p/amd-has-its-own-china-problem ），證明出口合規風險已擴散至整個 AI 晶片陣營。
  3. **主線 3（利率是主壓力）— 同意，且今晚出現「成長降溫＋價格飆升」的停滯性通膨警訊**：今晚美東 08:30（台北 21:30）公布的 **11 月費城聯準製造業指數驟降至 6.3（6 個月新低，遠遜預期 23.2），但支付價格指數暴漲 15 點至 58.2（4 月以來新高）、初領失業金升至 20.3 萬、續領升至 176.3 萬**（https://mlq.ai/news/jobless-claims-edge-up-to-203000-as-the-philadelphia-fed-index-falls-to-a-six-month-low-and-prices-paid-jump/ ）；雖然疲弱的活動數據讓 10 年期殖利率自 5.10% 回落至 **5.072%**，但歐洲歐元區 10 月通膨終值衝上 **4.0%** 三年新高（https://ec.europa.eu/eurostat/web/products-euro-indicators/w/2-18112026-ap ）、ECB 11/25 準備金率討論與日銀 12 月升息預期仍鎖住全球利率地板。
  4. **主線 4（10 月核心 PCE 區間機率降至 30%）— 完全同意，雙方已對齊 30%**。
  5. **主線 5（油價 WTI 80–100 美元：Claude 58% vs 我 55%）— 部分同意，NYT 揭川普權衡對伊朗發動 4–7 天空襲推升 WTI 站回 $83.52（+1.47%）**（https://investinglive.com/commodities/nyt-trump-weighs-new-iran-strikes-as-israel-presses-for-a-four-to-seven-day-air-campaign/ ），短線支撐 80 美元下緣，我維持 **55%** 觀望下週 EIA 庫存。
  6. **主線 6（Anthropic 掛牌受影響順序＋1.2375 億股穩價額度）— 同意你的穩價額度風險**：截至 00:39 ANT 仍在等待開盤集合競價搓合，指示價已升至 **$110**，須盯首筆成交後的持續承接力。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題
- 1. 本晚美東 08:30 公布的 **11 月費城聯準製造業指數從 20.9 急墜至 6.3（新訂單轉負至 -0.4）、同時支付價格暴漲 15 點至 58.2、續領失業金跳增 7 萬至 176.3 萬**（https://mlq.ai/news/jobless-claims-edge-up-to-203000-as-the-philadelphia-fed-index-falls-to-a-six-month-low-and-prices-paid-jump/ ），目前本站《經濟日曆》未收錄費城聯準指數。這種「製造業活動急縮＋上游價格再衝」的區域數據，是否會讓你在第 5 輪下修「經濟沒壞」假設、並拉高停滯性通膨象限權重？
- 2. 今日（11/19）**Hunterbrook 做空 AMD** 引發盤中一度急殺 8%–10%，暴露美商晶片透過「中資伺服器母公司→新加坡／美國加州關聯公司（Kaytus／Aivres）」的韌體與系統銷售灰區（https://newsletter.hntrbrk.com/p/amd-has-its-own-china-problem ）。除原先僅針對輝達與台積電外，下一輪是否應在 `dots_read.json` 補入「AI 晶片商之非直銷海外伺服器關聯鏈（OSAT／OEM）合規風險」？
- 3. 我們在 `11-20 00:31` 重建後的線上頁面實測：`#econ`《美股財報日曆》仍將已送出 8-K 且已顯示在《各公司最新財報重點》的 **WMT** 留在「即將公布」清單，且《IPO 觀察》仍印出已取消承銷的 **宏偉 11-19、耐特 11-19**。請問「已送 SEC 財報申報就從即將公布拿掉」的規則是不是只修在倒數卡、還沒套用到《美股財報日曆》表格？台股 IPO 狀態欄位能否同步過濾「不開標／取消承銷」？

---

### WIDE-1｜《紐約時報》揭川普權衡對伊朗發動 4–7 天新一波空襲＋荷莫茲海峽油輪遇襲與 IEA 警告 400 億美元繞道管線脆弱（補充 NYT 空襲報導）
- 事實：《紐約時報》11/19 揭露，因情報顯示伊朗重建飛彈與無人機庫存，以色列總理納坦雅胡敦促美方加入一場 **4 至 7 天聯合空襲行動**，美國總統川普正權衡是否對伊朗發動新一波大規模軍事打擊（https://investinglive.com/commodities/nyt-trump-weighs-new-iran-strikes-as-israel-presses-for-a-four-to-seven-day-air-campaign/ ，台北時間 2026-11-19）；同日荷莫茲海峽東側接連傳出油輪疑觸水雷與遭襲起火，且 IEA 於《2026 世界能源展望》警告海峽衝突已累計中斷 **28 億桶原油與 600 億立方公尺天然氣**，就算波灣產油國斥資 **400 億美元**興建替代輸油管線，仍高度暴露於飛彈與無人機襲擊風險中（https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ）；胡塞飛彈攔截碎片同日損及利雅德沙國主權基金（PIF）總部大樓（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ）。
- 推理：美股過去兩天只看到 EIA 累庫帶來的油價回檔與深圳美中俄宣言，一旦美以對伊朗發動 4–7 天空襲，伊朗對波灣航運與繞道管線的報復將直接把「短線累庫」翻轉為實體供應斷鏈，進而阻斷所有央行降息空間。
- 先影響資產：布蘭特與 WTI 原油遠月價差、油輪運價與戰爭險保費、波灣主權債 CDS、防禦型航空／航運股。

### WIDE-2｜歐元區 10 月通膨終值衝上 4.0% 三年新高＋ECB 2026 SREP 揭露 96% 大銀行 IT／資安評等不佳並鎖定私募信貸實地檢查＋11/25 準備金率倍增辯論＋英國央行 AI 量子資安諮詢（更新歐元區 4.0% 通膨）
- 事實：歐盟統計局（Eurostat）於 **11/18** 公布最終數據確認，**歐元區 10 月年通膨率升至 4.0%**（9 月為 3.8%，創 2023 年 9 月以來新高），主要受能源年增高達 **21.0%** 與服務通膨 **3.3%** 推升（https://ec.europa.eu/eurostat/web/products-euro-indicators/w/2-18112026-ap ，台北時間 2026-11-19）；市場與經濟學家預期 ECB 將於 **12 月 17 日**升息 1 碼（存款利率由 2.50% 升至 2.75%）。同日 ECB 公布 **2026 年監理審查（SREP）結果**，指出近 **96%** 的大型受監理銀行在營運與 IT／資安風險管理僅獲得普通或不佳評等，並宣布 2027–2029 年將針對**私募信貸基金融資與 NBFI 曝險**啟動專案實地檢查（https://live.euronext.com/en/financial-news/nearly-all-euro-zone-banks-are-struggling-tech-risks-ecb-says ）；路透另指 ECB 將於 **11/25** 辯論把最低存款準備金率從 1% 倍增至 2%（回收約 1,750 億歐元，https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ）；英國央行、PRA 與 FCA 亦發布網路韌性與 AI／量子資安實務指引，指 10 月 FCA 通報資安事件較前高大增 **52%**（https://www.bankofengland.co.uk/news/2026/november/cyber-resilience-guidance-consultation-and-ai-and-quantum-effective-practices ）。
- 推理：美股幾乎全神貫注於 Fed 12/9 升息，卻忽略歐元區通膨已達 4.0%（是 ECB 目標的兩倍），加上準備金率倍增討論與 SREP 鎖定私募信貸實地檢查，將導致歐元區與美國同步進入「貨幣＋監理雙緊縮」，直接抽緊歐系銀行對美國資料中心與私募信貸基金的授信額度。
- 先影響資產：歐元區公債（Bund／BTP 利差）、歐洲銀行股（SX7E）、私募信貸與 BDC、EUR/USD。

### WIDE-3｜哥倫比亞 11/19 全國大罷工抗議 19% 食物 VAT 與國營石油 Ecopetrol 民營化疑慮＋銅／錫去槓桿急挫衝擊南美資源國
- 事實：哥倫比亞主要工會（CUT）與民間組織於 **11 月 19 日**發起全國總罷工與跨城大規模抗議（波哥大、麥德林、卡利等主要城市交通受阻），反對政府「經濟救援／稅改法案」擬對民生基本食品課徵 **19% 增值稅（VAT）**並尋求授權推進國營石油公司 **Ecopetrol** 民營化（https://colombiareports.com/colombias-labor-unions-and-social-organizations-call-national-strike-on-november-19/ ，台北時間 2026-11-19）。同時間，受強美元與宏觀資金退潮影響，LME 三個月期銅跌至 4 月以來新低（盤中一度跌 4% 至 $12,727.50／公噸）、AI 焊料關鍵金屬錫價單日急殺 **8%**（https://www.tradingview.com/news/seekingalpha:cb0deccc9094b:0-copper-extends-slide-to-lowest-level-since-april-on-firm-dollar-ai-doubts/ ）；南非央行 11/19 亦以 4 比 3 鷹派分歧維持利率 7.25%（https://www.moneyweb.co.za/news/economy/sarb-holds-rates-steady/ ）。
- 推理：拉美同時面臨「資源價格去槓桿（銅／錫重挫）」與「財政緊縮引發的社會抗爭（哥倫比亞罷工、巴西 PLP 299 緊縮案）」，若哥倫比亞油田與運輸遭長期干擾，將同時推升拉美主權風險溢酬與重油供給不確定性。
- 先影響資產：LME 銅／錫期貨、哥倫比亞披索（USD/COP）、Ecopetrol（EC）、智利披索（USD/CLP）、礦業股（FCX、SCCO）。

### WIDE-4｜Waymo 遭加州 DMV 以「公共安全立即危險」勒令暫停高速公路自駕營運並擴大至全美暫停＋Equinor 網攻與歐盟延後甲烷申報 2 年（新增 Waymo 監管禁令）
- 事實：美國加州車輛管理局（DMV）本週正式對 Alphabet 旗下自駕計程車 **Waymo** 下達高速公路營運禁令，將其多起在灣區誤闖 U.S. 101 施工封閉區與 I-280 企圖超越加州公路巡警（CHP）滾動交通管制車隊的行為定性為「**對公共安全構成立即危險（imminent hazard to public safety）**」，要求須提交可驗證的修正證據才能解禁；Waymo 隨後主動暫停全美所有營運城市（含鳳凰城、奧斯汀、邁阿密）的高速公路商業載客（https://www.kqed.org/news/12110123/hazard-to-public-safety-california-dmv-restricts-waymo-freeway-operations ，台北時間 2026-11-19）。另方面，挪威國營能源巨頭 **Equinor** 遭持續性網路攻擊（https://therecord.media/norway-equinor-cyberattack-energy ），歐盟則臨時妥協將油氣煤進口商甲烷申報延後兩年至 2029 年（https://europeansting.com/2026/11/19/methane-deal-to-delay-reporting-and-monitoring-for-energy-importers/ ）。
- 推理：市場在討論 Anthropic IPO 與 AI 算力資本支出時，往往假設實體世界 AI（自駕車／機器人）會線性商轉；加州 DMV 的高速公路禁令顯示實體 AI 面臨零容錯監管門檻，可能拖慢自駕車隊單車經濟規模化與機場高速接駁營收預期，同時影響對優步（UBER）／Zoox 的合作品質定價。
- 先影響資產：GOOGL（Waymo 估值折價）、TSLA（FSD 監管比較）、UBER、LYFT、歐洲天然氣 TTF。

### WIDE-5｜強氣旋「阿克萬（Akvan）」逼近印度奧里薩邦八縣高度戒備＋印度 CPI 破 6%＋日銀 12 月升息至 1.50% 預期＋APEC 深圳美中俄宣言（補充印度氣旋實況）
- 事實：強烈氣旋風暴「**阿克萬（Severe Cyclonic Storm Akvan）**」正逼近印度東岸，《印度教徒報》11/19 報導奧里薩邦已將八個沿海縣市列入最高警戒並緊急撤離民眾，預計 **11/20 中午**在 Gopalpur 附近登陸（https://www.thehindu.com/news/national/odisha/odisha-puts-eight-districts-on-high-alert-as-severe-cyclonic-storm-akvan-advances-towards-coast/article71716731.ece ，台北時間 2026-11-19），加上印度 10 月 CPI 升至 **6.09%** 突破央行上限（https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ）。同時日本央行總裁植田和男 11/19 在國會警示日圓偏弱與油價恐推升潛在通膨破 2%，強化 12 月升息至 **1.50%** 預期（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ）；APEC 深圳峰會美中達成「30 對 30 關稅協議」並發布美中俄三方《和平宣言》（https://www.whitehouse.gov/briefings-statements/2026/11/u-s-russia-china-heads-of-state-declaration-toward-peace/ ）。
- 推理：印度東岸天災疊加 6% 以上通膨與沃爾瑪 Flipkart 大促遞延至 Q4，恐進一步擾動印度國內食品通膨與外資流向；而日銀 12 月升息與美中仍未鬆綁半導體出口管制，使亞洲科技供應鏈面臨資金面與合規面雙重考驗。
- 先影響資產：INDA、USD/INR、USD/JPY、日本銀行與工業股、亞股外資流向。

---

### A｜今天的大動（依 `https://wallstreet-sentinel.pages.dev/api/gemini_ask` 台北 2026-11-20 00:32 即時 12 檔題目清單逐題回答；00:39 補充盤中最新報價）

### PDD｜拼多多（PDD）今天 +12.0%（00:39 漲至 +12.3%）：Q3 2026 縮減行銷費用 16.6% 帶動 Non-GAAP EPADS 人民幣 21.04 元大勝共識
- 事實：拼多多於美東 11/19 06:30（台北 19:30）公布 Q3 2026 財報，總營收人民幣 **1,083.4 億元**（年對年持平，遜於市場預期約 1,152 億～1,162 億元），主因交易服務營收年減 12% 至 485.2 億元（線上行銷服務年增 12% 至 598.2 億元）；但銷售與行銷支出年減 **16.6%** 至 **253 億元**，推動營業利益年增 **24.8%** 至 **311.6 億元**、Non-GAAP 淨利 **310 億元**、**Non-GAAP 稀釋每 ADS 盈餘人民幣 21.04 元（3.14 美元）**大幅勝過共識 2.61–2.77 美元，截至 00:39 續漲至 $86.95（+12.27%）（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，且 `11-20 00:31` 線上《美股財報日曆》仍將 PDD 列為「即將公布」。

### WDC｜威騰電子（Western Digital，WDC）今天 +7.2%（00:39 漲至 +7.9%）：與 STX、MU、SNDK 同步受 Anthropic IPO 帶動儲存族群走強（無新進展）
- 事實：11/19 WDC 未見單獨新公司公告（找不到獨立公司來源），隨 Anthropic 創紀錄 IPO 帶動市場對 AI 訓練與推理長記憶儲存需求預期，與 STX、MU、SNDK 同步上漲，00:39 報 $310.85（+7.86%）（https://247wallst.com/investing/2026/11/19/sandisk-and-micron-rise-4-as-anthropics-record-ipo-revives-the-ai-trade-western-digital-gains-5/ ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，屬儲存與記憶體板塊集體上行。

### AMD｜超微（AMD）今天 -6.6%（00:39 報 -5.4%）：遭 Hunterbrook 發表做空報告指控實體清單中企 IEIT 持續取得 AMD 新韌體，由開盤上漲急轉重挫
- 事實（不同意本站早盤標題，因盤中突發做空報告反轉）：本站引用的早盤新聞 `AMD Rises 3%` 僅反映開盤初期（開盤 $543.48，+2.5%）。隨即於美東 11:00 前，調查新聞機構暨做空對沖基金 **Hunterbrook Media / Hunterbrook Capital** 發布報告《*AMD Has Its Own China Problem*》並揭露放空 AMD，指中國伺服器廠 **IEIT Systems** 於 2025 年 3 月列入美國 BIS 實體清單後，仍持續發布內含至少六個較新版本 AMD 韌體的 BIOS 更新（最近一次為 10/19 更新），且關聯廠商 **Maginfra（中國）、Kaytus（新加坡）、Aivres（加州）** 使用幾乎相同的韌體，同時強調 AMD 2025 財年帳單計中國（含香港）營收達 **77.51 億美元**、新加坡 **42.84 億美元**（報告亦聲明尚未直接證明 AMD 違法出口），引發 AMD 盤中一度重挫 8%–10% 至 $487.80，00:39 報 $501.29（-5.44%）（https://newsletter.hntrbrk.com/p/amd-has-its-own-china-problem ；https://247wallst.com/investing/2026/11/19/amd-is-down-8-after-short-seller-hunterbrook-ties-its-firmware-to-blacklisted-chinese-server-maker-resilient-intel-remains-up-5/ ；https://news.cnyes.com/news/id/6668022 ，台北時間 2026-11-20）。
- 本站漏掉的：本站僅抓到開盤前「AMD 上漲 3%」的標題，完全漏掉美東上午盤中 **Hunterbrook 做空報告** 導致股價逆轉大跌的真正觸發事件。

### STX｜希捷科技（Seagate Technology，STX）今天 +6.6%（00:39 漲至 +7.8%）：受 Anthropic IPO 帶動儲存類股集體買盤推升（無新進展）
- 事實：11/19 STX 未見單獨公司公告（找不到獨立公司來源），隨 WDC、SNDK、MU 等 AI 資料中心儲存板塊同步走強，00:39 報 $556.08（+7.79%）（https://247wallst.com/investing/2026/11/19/sandisk-and-micron-rise-4-as-anthropics-record-ipo-revives-the-ai-trade-western-digital-gains-5/ ；https://news.cnyes.com/news/id/6667734 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，屬族群同步走強。

### CRWD｜CrowdStrike（CRWD）今天 +6.5%（00:39 漲至 +6.8%）：受同業 PANW 財報大勝並砸 45 億美元併購 Applied Compute 外溢帶動（無新進展）
- 事實：CRWD 預計 **12 月 1 日盤後**才公布 Q3 FY27 財報，11/19 本身無單獨公司公告或當日新評等調整（找不到 11/19 個別來源）；主要受同業 **PANW** 昨晚公布 Q1 營收年增 39% 至 34.4 億美元、上調全年財測並宣布 **45 億美元**併購 **Applied Compute** 激勵資安類股集體走高，00:39 報 $253.09（+6.78%）（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ；https://www.tradingview.com/news/zacks:3d366f393094b:0-cybersecurity-stocks-gain-on-ai-boom-but-are-valuations-too-high/ ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### PANW｜Palo Alto Networks（PANW）今天 +6.0%（00:39 漲至 +6.4%）：Q1 FY27 營收年增 39%＋上調全年財測＋45 億美元併購＋逾 20 家券商調高價格看法（補充 BofA／Barclays／Citi／JPMorgan 報告）
- 事實：PANW 美東 11/18 盤後公布 Q1 FY27 營收年增 **39%** 至 **34.4 億～34.5 億美元**（優於預期 33.1 億）、Non-GAAP EPS **1.05 美元**、NGS ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 營收指引至 **145.2 億～145.7 億美元**，並宣布斥資 **45 億美元**收購 **Applied Compute**（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ）；今日（11/19）華爾街逾 20 家券商同步調高價格看法，包含 **BofA Securities** 維持 `Buy`（$420→**$430**，https://tw.tradingview.com/news/tradingview:312a99180b922:0/ ）、**Barclays** 維持 `Overweight`（$375→**$385**，https://tw.tradingview.com/news/tradingview:4ef72b5df9756:0/ ）、**Citi** 維持 `Buy`（$440→**$445**）、**JPMorgan**（$384→**$415**）、**Baird**（$420→**$465**）、**Goldman Sachs**（$390→**$440**）、**KeyBanc**（$380→**$450**）及 **Piper Sandler**（$410→**$450**），00:39 報 $361.60（+6.38%）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，且 `c-econ-11` 財報表因採用 Zacks 含股權酬勞口徑（0.46 vs 0.52）誤顯示為 -11.5%。

### UNH｜聯合健康（UnitedHealth，UNH）今天 -5.7%（00:39 報 -5.8%）：開盤微紅後盤中擴大重挫，持續消化聯邦公報今日正式刊登之 CMS「CRUSH」追溯稽核草案與國會拆分壓力
- 事實：UNH 今日開盤價 $351.13（略高於昨收 $349.91）後盤中急殺至 $329.52（-5.83%）。經查今日未見 UNH 單獨公司公告或券商新降評（找不到 11/19 個別公司新訊），但時間上 **美國衛生及公共服務部（HHS）／CMS 的《CRUSH》（CMS-6098-P）擬議規則於今日（2026-11-19）正式刊登聯邦公報**（亦可由本站 `#news` `c-news-4` 確認：醫療保健 ETF 單日 -2.0%），該規則擬取消 FFS 調整因子並將 Medicare Advantage 抽樣外推追討**回溯至 2018 年**，預估十年追回近 **900 億美元**，加上參議員 Elizabeth Warren 本週力推《Break Up Big Medicine Act》拆分垂直整合醫療巨頭（https://www.cms.gov/newsroom/press-releases/cms-crush-proposed-rule-aims-reap-nearly-90-billion-taxpayers-savings-targeting-fraud-across ；https://www.tradingview.com/news/gurufocus:46c8103be094b:0-unitedhealth-shares-sink-as-new-federal-fraud-crackdown-sparks-healthcare-sell-off/ ；https://247wallst.com/investing/etf/2026/11/17/your-safe-health-care-etf-just-got-hit-by-unitedhealth-again/ ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，但本站《政府做了什麼》卡片其實已收錄該規則 2026-11-19 正式刊登公報的紀錄。

### NKE｜耐吉（Nike，NKE）今天 -4.9%（00:39 報 -5.1%）：11/17 投資人日揭露「FY29 前營收難重返市場成長」餘波持續，今日多位分析師維持保守看法
- 事實：耐吉於 **11/17** 投資人日重申 FY27 營收將呈現高個位數衰退、調整後 EPS 僅 $1.15–$1.35，並坦承須等到 **FY2029** 才恢復市場水準營收成長（https://investors.nike.com/news-events/press-releases/detail/578/nike-inc-announces-full-stride-ahead-strategy-and-2031-financial-framework-at-investor-day ）。雖今日無重大負面新公告，但華爾街續發謹慎評論（KeyBanc 維持 `Sector Weight`、Truist 維持 `Sell` 與看法 $29、Telsey 維持 `Market Perform` 與看法 $35），市場續拋售漫長轉型等待期，00:39 報 $34.47（-5.08%）（https://www.fool.com/investing/2026/11/19/nike-s-2031-targets-look-great-on-paper-but-sales-won-t-grow-until-2029-here-s-the-price-i-d-pay/ ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### INTC｜英特爾（Intel，INTC）今天 +4.6%（00:39 漲至 +5.4%）：同意本站，Austin 峰會揭露 18A-P 首位外部客戶與微軟採用 EMIB，且未捲入 Hunterbrook 對 AMD 的出口做空風暴
- 同意本站（24/7 Wall St. 與 MarketWatch 已涵蓋 18A 首位外部客戶進展及半導體早盤反彈，https://247wallst.com/investing/2026/11/19/intel-climbs-7-on-first-18a-customer-nvidia-gains-4-as-trump-floats-blackwell-sales-to-china-and-dan-ives-hails-anthropic-ipo-amd-rises-3/ ）。
- 本站漏掉的：英特爾在 Austin 峰會另與微軟揭露 EMIB 先進封裝合作進展；且在盤中 Hunterbrook 做空對手 AMD 導致 AMD 大跌逾 5%–8% 之際，資金反而更偏好具備美國本土先進製程（18A）與低中國出口稽核風險的 INTC，00:39 續漲至 $57.60（+5.35%）（https://247wallst.com/investing/2026/11/19/amd-is-down-8-after-short-seller-hunterbrook-ties-its-firmware-to-blacklisted-chinese-server-maker-resilient-intel-remains-up-5/ ）。

### FTNT｜飛塔（Fortinet，FTNT）今天 +4.3%（00:39 漲至 +4.6%）：受同業 PANW 財報與 AI 資安併購帶動網安類股集體走強
- 事實：11/19 FTNT 未見單獨公司新聞稿或券商評等調整（找不到獨立來源）；與 CRWD 同步受惠同業 **PANW** 公布 Q1 FY27 營收年增 39%、上調全年財測並宣布 45 億美元併購 **Applied Compute** 帶動資安板塊重估，00:39 報 $137.91（+4.63%）（https://www.tradingview.com/news/zacks:3d366f393094b:0-cybersecurity-stocks-gain-on-ai-boom-but-are-valuations-too-high/ ；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### PM｜菲利普莫里斯（Philip Morris，PM）今天 -4.1%（00:39 報 -3.8%）：今日未見單獨公司利空公告，屬防禦高估值股獲利了結與前期 Zyn 美國利潤率壓力消化（不確定）
- 事實：經查證 **11/19 當日未見 Philip Morris 單獨新公司公告、財報或券商降評報告（找不到 11/19 單日觸發來源）**；近期公司僅於杜拜 Technovation 活動重申無煙產品營收佔比逾 40%（https://www.fool.com/earnings/takeaways/2026/10/21/philip-morris-3-key-takeaways-for-long-term-investors/ 說明 10/21 財報曾預告美國 Zyn 由每罐 15 袋增至 20 袋將壓縮 Q4 美國營益率）。
- 推理（不確定）：在 11/19 無新單獨利空、10 年期美債殖利率居 5.07% 以上且資金回流科技／AI 股之際，較符合前期漲多之必需消費高估值股獲利了結與輪動賣壓，確切觸發原因標註「**不確定**」。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### QCOM｜高通（Qualcomm，QCOM）今天 +3.9%（00:39 漲至 +4.6%）：攜手 Cirrascale 開放「Dragonfly AI200」機架級 AI 推論平台雲端試用，吸引買盤由昨跌 4.1% 強彈
- 事實：高通與 **Cirrascale Cloud Services** 宣布於 SC26 超算展（11/17–18 芝加哥）展示並正式開放特定客戶透過 Cirrascale 的 *AI Innovation Cloud* 雲端評估高通 **Dragonfly AI200** 機架級推論系統（每張加速卡配 **768 GB LPDDR** 記憶體、56 卡液冷機櫃總計 **43 TB**，鎖定 70 億至 10 兆參數大型模型推論，主打以較低功耗與 TCO 挑戰輝達 HBM 架構）（https://www.qualcomm.com/news/releases/2026/11/qualcomm-and-cirrascale-collaborate-to-advance-next-generation-- ；https://finance.biggo.com/news/21027901-c517-4af5-91c6-de974cf87407 ，台北時間 2026-11-19）。（備註：另有搜尋結果顯示高通 2026 年投資人日實為 6 月 24 日召開，非今日事件；亦有部分 AI 自動撰寫快訊混淆時點，本條已排除 AI 自動文章並核對高通官網新聞稿與 BigGo 報導）。在前一日下跌 4.12%（受 Baird 因字節跳動 ASIC 出口管制把價格看法由 $320 調降至 $300 影響）後，今日受 AI 資料中心推論商業化進度帶動強彈至 $167.14（+4.58%）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

---

### AN-1｜過去 3 小時（21:40–00:40 台北／美東 08:40–11:40）：Hunterbrook 發布做空 AMD 報告；PANW 獲逾 20 家券商全面調高價格看法；大摩／高盛／美銀更新 NVDA 財報後看法
- 事實（過去 3 小時及 11/19 當日新增確認）：
  - **AMD（美東 11/19 上午約 10:30–11:00 前）**：做空機構 **Hunterbrook Media / Hunterbrook Capital** 發布調查報告《*AMD Has Its Own China Problem*》並揭露持有 AMD 空頭部位，引發股價由早盤 +2.5% 反轉急殺逾 5%–8%（https://newsletter.hntrbrk.com/p/amd-has-its-own-china-problem ）。
  - **PANW（美東 11/19 盤前至盤中，補齊主流大行報告）**：除 Baird（$420→$465）、Goldman Sachs（$390→$440）、KeyBanc（$380→$450）、Piper Sandler（$410→$450）外，**BofA Securities** 分析師 Tal Liani 維持 `Buy` 看法 $420→**$430**（https://tw.tradingview.com/news/tradingview:312a99180b922:0/ ）；**Barclays** 維持 `Overweight` 看法 $375→**$385**（https://tw.tradingview.com/news/tradingview:4ef72b5df9756:0/ ）；**Citigroup** 維持 `Buy` $440→**$445**；**JPMorgan** $384→**$415**；**Wells Fargo** 維持 `Overweight` **$510**。
  - **NVDA（11/18 財報後～11/19 各行更新）**：**Goldman Sachs** 維持 `Buy` 看法 **$220**；**Bank of America** 維持 `Buy` 看法 **$280**；**Morgan Stanley** 維持 `Overweight` 看法 $267→**$260**（https://www.tradingview.com/news/cnbctv:57f13f9dc094b:0/ ）。另量化系統 Seeking Alpha Quant Rating 今日（11/19）將 NVDA 系統評分由 `Strong Buy` 降至 `Hold`（非人工券商報告）。
- 事實（近期已核對清單，無新進展）：
  - **AVGO**：Goldman Sachs（11/19）維持 `Buy` 看法 $540→**$460**（https://www.tokenpost.com/news/business/61151 ）；Rothschild & Co Redburn（11/13）`Buy`→`Neutral` $595→**$398**（https://fr.tradingview.com/news/seekingalpha:f4cc47e04094b:0-broadcom-in-focus-as-rothschild-downgrades-to-neutral-but-flags-potential-upside/ ）。
  - **MRVL**：BofA `Buy`→`Neutral`（$400→$225）；TD Cowen `Buy`→`Hold`（$350→$175）（https://finance.biggo.com/news/11363615-75b3-4fde-a7f6-069c21673c8c ）。
  - **TSM／2330（11/19）**：Morgan Stanley 維持 `Overweight` 看法 **3,088 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ）。

---

### POL-1｜BIS 遠端算力新規（`2026-23529`）與 CMS「CRUSH」擬議規則同日於 11/19 正式刊登聯邦公報；《金融時報》指新規取消「非 AI 用途」豁免致台積電、三星暫停部分中國晶片出貨（補充 CMS 公報刊登）
- 事實：美國商務部 BIS 暫行最終規則（聯邦公報 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）今日（美東 **2026-11-19**）正式刊登聯邦公報並立即生效（意見徵詢至 2027-01-19），增訂 § 744.24 限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，廢止前政府 AI 擴散規則，並由財政部與國安會（NSC）主導及指示撰寫（https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors ；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ）。《聯合報》與《自由財經》11/19 引述《金融時報》指新規封堵 OSAT 繞道並取消智慧手機「非 AI 用途」豁免，致使**台積電與三星電子已通知中國客戶在申請許可證期間暫停出貨特定先進製程處理器**（https://udn.com/news/story/6811/9889722 ；https://ec.ltn.com.tw/article/breakingnews/5646861 ）。
- 事實：美國衛生及公共服務部（HHS）／CMS 的醫療保險詐欺與 Medicare Advantage 稽核擬議規則《**CRUSH**》（CMS-6098-P）亦於今日（**2026-11-19**）正式刊登聯邦公報（意見徵詢至 2027-01-19），衝擊管理醫療保險板塊（https://www.cms.gov/newsroom/press-releases/cms-crush-proposed-rule-aims-reap-nearly-90-billion-taxpayers-savings-targeting-fraud-across ）。

### POL-2｜白宮發布美中俄三方《和平宣言》；美國財政部 FinCEN 提案、9 月 TIC 淨流入 2,610 億美元、OFAC 制裁與 USTR 談話（無新進展）
- 事實：白宮 11/19 發布川普、普丁與習近平深圳會晤聯合宣言《U.S.-Russia-China Heads of State Declaration toward Peace》（https://www.whitehouse.gov/briefings-statements/2026/11/u-s-russia-china-heads-of-state-declaration-toward-peace/ ）；財政部 FinCEN 發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，https://home.treasury.gov/news/press-releases/sb0691 ）；9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ）；OFAC 制裁真主黨與聖城軍金流（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 大使 Greer 11/18 於 RBA 年會重申美國優先貿易（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）。

---

### TW-1｜台積電與三星電子傳暫停出貨部分中國晶片（波及手機品牌）；11/19 收跌 1,768 點、1.29 億違約交割與限空令 2.0（無新進展）
- 事實：《聯合報》與《自由財經》11/19 引述《金融時報》報導，因應美國 BIS 新規堵住 OSAT 封測繞道並取消智慧型手機「非 AI 用途」豁免，**台積電與三星電子已通知中國大陸客戶暫停出貨部分先進製程處理器並等待美方許可證**，影響範圍擴及小米、OPPO、vivo 等中國手機廠與中資 AI 晶片業者（https://udn.com/news/story/6811/9889722 ；https://ec.ltn.com.tw/article/breakingnews/5646861 ，台北時間 2026-11-19）。
- 事實（11/19 台股正規盤收盤、三大法人與違約交割，無新進展）：加權指數收 **38,426.89 點（-1,768.02 點 / -4.40%，失守年線）**，成交值 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ）；櫃買收跌 **-7.22% 至 285.33 點**。權值股收盤：**台積電 2,100 元（-3.45%）**、**聯發科 3,720 元（-5.58%）**、**鴻海 220.5 元（-0.23%）**、**日月光投控 504 元（-8.03%）**、**緯穎 1,410 元（跌逾 4%）**（https://www.moneyweekly.com.tw/ArticleData/Info/Article/212266 ）。三大法人合計賣超 **461.03 億元**（**外資 -243.12 億、投信 +15.13 億、自營商 -233.03 億**，https://www.cna.com.tw/news/afe/202611190200.aspx ）；外資台指期淨空單 **-99,219 口**。盤後通報 **1.29 億元**違約交割：上市**台化（1326）4,172.8 萬元**，上櫃**世界先進（5347）與萬泰科（6190）**（https://stock.ltn.com.tw/article/m7hjf9c9axqq ）。
- 事實（金管會 11/20 限空令 2.0，無新進展）：今日收盤跌幅 ≥3.5% 之上市櫃與 TDR（共 **1,028 檔**）11/20 禁止平盤下融券及借券放空，盤中借券放空委託上限由前 30 日均量 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；新台幣 16:00 收 **32.942 元（升 0.5 分）**（https://www.cna.com.tw/news/afe/202611190296.aspx ）。

### TW-2｜鴻海與沙國 PIF 合資電動車品牌 Ceer Motors 傳出與當地銀行達成 6.93 億美元（約新台幣 220 億元）融資協議；台積電 2 奈米洩密案定讞與 5 億美元入股 Anthropic（補充 Ceer 融資進展）
- 事實（新增鴻海海外電動車進展）：綜合汽車財經媒體報導，鴻海與沙烏地阿拉伯主權財富基金（PIF）合資的電動車品牌 **Ceer Motors** 近日與沙國阿拉伯國民銀行（ANB）及利雅德銀行（Riyad Bank）簽署總額 **6.93 億美元（約新台幣 220 億元／26 億沙烏地里亞爾）** 聯貸融資協議，加速阿布都拉國王經濟城產線與量產落地（搜尋結果摘要；註：just-auto 原文頁連線遭遠端關閉，仍待《經濟日報》／《工商時報》正式重訊對照）。
- 事實（無新進展）：最高法院 11/19 駁回上訴，台積電 2 奈米／14 埃米洩密案涉案之台灣東京威力科創行銷主管盧怡尹判刑 10 月、緩刑 3 年定讞（https://money.udn.com/money/story/5612/9889323 ）；台積電資深副總張曉強親赴輝達總部穩固長期產能，並公告以每股 **83 美元**認購 Anthropic 普通股 **6,024,096 股（約 5 億美元）**（https://www.cna.com.tw/news/afe/202611190254.aspx ）；日月光旗下福雷電子高雄仁武新廠動土投資 2,489 億元（https://www.cna.com.tw/news/afe/202611190122.aspx ）；廣達田納西廠租約 1,490.8 萬美元（https://news.cnyes.com/news/id/6666244 ）；海龍 2A 綠電轉售台積電（https://www.cna.com.tw/news/afe/202611190102.aspx ）；鴻海 72.4 億日圓收購 Sony 車載相機事業（https://www.ctee.com.tw/news/20261119700316-439901 ）。
- 傳聞（無新進展）：《工商時報》與外媒引述業界指台積電依客戶資產負債表設 AI 信用額度、超額須預付現金（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ）。

### TW-3｜SK 海力士 11/19 收漲 +3.41%、蘋果洽談三星多年期 DRAM 長約；日經收漲 +0.71%（東京威力科創 +2.8%）；耐特與宏偉競拍流標取消 11/19 掛牌（無新進展）
- 事實：11/19 韓股 SK 海力士收漲 **+3.41% 至 1,183,000 韓元**，三星電子漲逾 **+1.1%**（https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ）；《The Korea Herald》報稱蘋果與三星正洽談 4 至 5 年期 DRAM 供應長約最後階段（https://www.koreaherald.com/article/10942672 ）。日股日經 225 收漲 **+0.71%（59,444.21）**，東京威力科創（TEL）上漲約 **+2.8%**。原訂 11/19 台股掛牌之**耐特（8058）**與**宏偉（4565）**前於 11/09–11/10 因競拍合格投標數量不足不予開標並取消本次承銷作業（https://news.cnyes.com/news/id/6653937 ；https://ww2.money-link.com.tw/realtimenews/NewsContent.aspx?SN=2441867002&PU=0009 ）。

---

### EARN-WSM / WMT / PDD / BABA / NTES｜11/19 已公布財報之大型股（無新進展）
- 事實：
  - **WSM（Q3 FY26，美東盤前）**：淨營收 **19.91 億美元（+5.8% YoY）** 符合預期；**全品牌同店銷售 +5.1%**（West Elm +7.0%、Williams Sonoma +6.8%、Pottery Barn +1.8%）；Non-GAAP 營益率 **17.4%**、**Non-GAAP EPS $2.19（+11.7% YoY）** 略優於預期 $2.17–$2.18，並重申 FY26 全年財務展望（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ）。
  - **WMT（Q3 FY27，台北 20:00 公布）**：營收 **1,888 億美元（+5.2% YoY）** 優於預期（1,872.5 億～1,873.8 億）、美國同店（不含燃油）**+2.9%**、美國電商 +23%；調整後 EPS **0.65 美元**（GAAP 0.62 美元）優於預期 0.64 美元；上調 FY27 調整後 EPS 至 **$2.84–$2.89**（https://www.cnbc.com/2026/11/19/walmart-wmt-q3-2026-earnings.html ；https://finance.biggo.com/news/462fcfe0-7cf8-4cdf-b251-332c42101b59 ）。
  - **PDD（Q3 2026，台北 19:30 公布）**：營收人民幣 **1,083.4 億元**（持平，遜預期 1,152 億～1,162 億）；因壓低行銷費用，Non-GAAP 淨利 **310 億元**、**Non-GAAP 每 ADS 盈餘 21.04 元（3.14 美元）**大幅勝過共識 2.61–2.77 美元（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ）。
  - **BABA（Q2 FY27，已公布）**：營收人民幣 **2,715.19 億元（+10% YoY）** 優於預期 2,698.49 億、AI 雲外部收入 +67%；但 Non-GAAP 淨利 **199.09 億元**遜預期 265.7 億、CapEx 增 60% 致 **FCF 淨流出 344.72 億元**（https://investingnews.com/alibaba-group-announces-september-quarter-2026-results-and-interim-results-for-the-six-months-ended-september-30-2026/ ）。
  - **NTES（Q3 2026，已公布）**：營收人民幣 **279 億元（-1.8% YoY）** 遜預期 ~295 億～303 億，Non-GAAP 每 ADS 盈餘 **2.13 美元**遜預期 2.43–2.49 美元（https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ）。

### EARN-INTU / ROST / GAP / KEYS / BSP / HPE / ZM / A / BILI / BURL / DKS / ADI / MDT / BBY / DLTR / DELL / HPQ / ADSK / WDAY / DE｜11/19 盤後～11/25 未來 10 天財報預期（無新進展）
- 事實：
  - **11/19 盤後（台北 11/20 05:00 後）**：**INTU** 共識營收 **43.0 億～43.1 億美元**、Non-GAAP EPS **2.46–2.47 美元**（原財測 2.44–2.48；波動 ±8.9%–10.5%，https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ）；**ROST** 共識營收 **62.0 億～62.3 億美元**、EPS **1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ）；**GAP** 共識營收 **40.1 億～40.2 億美元**、調整後 EPS **0.73–0.78 美元**（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）；**KEYS** 共識營收 **19.5 億美元**、Non-GAAP EPS **3.37–3.38 美元**（原財測 3.34–3.40，https://www.tradingview.com/news/tradingview:dd00407af5aef:0-keys-q4-26-earnings-eps-estimate-is-3-37-usd/ ）。
  - **11/20 盤前（台北 20:00–21:00）**：**BSP（Bending Spoons）** 共識營收 **7.41 億～7.46 億美元**、EPS **0.31–0.32 美元**（本站日曆列 0.25 美元）。
  - **11/23 盤後（台北 11/24 05:00）**：**HPE** 共識營收 **143.9 億～145.5 億美元**、EPS **1.27–1.29 美元**（公司財測 1.20–1.30；波動 ±9.7%，https://es.tradingview.com/news/tradingview:94412243ad242:0-hpe-q4-26-earnings-revenue-estimate-is-14-39b-usd/ ）；**ZM** Zacks 共識營收 **12.8 億美元**、EPS **1.49 美元**（https://www.zacks.com/stock/news/3030700/zoom-communications-zm-falls-more-steeply-than-broader-market-what-investors-need-to-know ）；**A（Agilent）** 共識營收 **19.9 億～20.3 億美元**、EPS 約 **1.73 美元**。
  - **11/24 盤前（台北 20:00–21:00）**：**BILI** 營收 **12.3 億美元**、EPS **0.23–0.27 美元**；**BURL** 營收 **29.7 億～30.0 億美元**、調整後 EPS **1.69–1.72 美元**（https://www.earningswhispers.com/epsdetails/BURL/202607 ）；**DKS** 營收 **50.8 億美元**、EPS **1.38–1.42 美元**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ）；**ADI** FactSet 共識營收 **43.2 億美元**、EPS **3.88 美元**（https://www.tradingview.com/news/tradingview:4441db86105da:0-adi-q4-26-earnings-revenue-estimate-is-4-32b-usd/ ）；**MDT** FactSet 共識營收 **94.8 億美元**、EPS **1.33 美元**（https://es.tradingview.com/news/tradingview:dcc2d0d8b8c99:0-mdt-q2-26-earnings-revenue-estimate-is-9-48b-usd/ ）；**BBY** FactSet 共識營收 **98.8 億美元**、調整後 EPS **1.49 美元**（https://getcompound.ai/news/bby-q3-earnings-preview ）；**DLTR** 營收 **50.4 億美元**、EPS **0.88–0.91 美元**。
  - **11/24 盤後（台北 11/25 05:00）**：**DELL** 共識營收 **492.0 億～502.0 億美元**、EPS **6.41–6.71 美元**（波動 ±14.85%，https://www.tradingview.com/news/tradingview:e525c4bdcb809:0-dell-q3-26-earnings-revenue-estimate-is-49-25b-usd/ ）；**WDAY** 營收 **26.9 億美元**、Non-GAAP EPS **2.74–2.75 美元**（https://www.tradingview.com/news/tradingview:41909f44860e7:0-wday-q3-26-earnings-revenue-estimate-is-2-69b-usd/ ）；**HPQ** FactSet 共識營收 **154.3 億～155.8 億美元**、EPS **0.75–0.76 美元**（https://in.tradingview.com/news/tradingview:2627939d5b773:0-hpq-q4-26-earnings-revenue-estimate-is-15-43b-usd/ ）；**ADSK** 共識營收 **21.3 億美元**、Non-GAAP EPS **3.07 美元**（https://www.marketbeat.com/instant-alerts/upcoming-autodesk-adsk-set-to-announce-quarterly-earnings-on-tuesday-2026-11-17/ ）。
  - **11/25 盤前（台北 21:00）**：**DE** 共識營收 **104.0 億美元**、EPS **4.03–4.07 美元**（https://www.tradingview.com/news/tradingview:669caa286319a:0-de-q4-26-earnings-revenue-estimate-is-10-40b-usd/ ）。

---

### FED-1｜FOMC 10 月會議紀錄：10 比 2 按兵不動、幾乎所有官員預期續升息，並點名 AI 表外租賃與循環融資（無新進展）
- 事實：11/19 03:00 公布 10/27–28 紀要：Cook 與 Hammack 投反對票主張升息 1 碼，幾乎所有官員預期未來數月有必要進一步升息，並點名 AI 表外租賃與循環融資風險（https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm ）。

### FED-2｜聯準會理事 Christopher Waller：主張 12 月應考慮升息 2 碼「震懾市場」（除非明確預告 1 月再升 1 碼）（無新進展）
- 事實：Waller 受訪指出聯準會可能需要一次大幅行動避免 3% 通膨固著，12/8–9 會議應考慮升息 50 基點，除非明確指引 12 月與 1 月各升 1 碼（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ）。

### FED-3｜理事 Barr（偏升息）、紐約聯準總裁 Williams（反對一次升 2 碼）；11/19 美東 08:30 初領失業金升至 20.3 萬、費城聯準製造業指數驟降至 6.3 但支付價格暴升至 58.2；Goolsbee 與 Barkin 即將發言（補充今夜經濟數據）
- 事實：Barr 11/18 演說指通膨仍過高、適合進一步升息（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ）；Williams 反對一次大幅升息 2 碼（https://www.aa.com.tr/en/economy/fed-governor-favors-half-point-rate-hike-in-december-unless-fed-signals-january-increase/4129382 ）。今晨美東 08:30（台北 21:30）公布 **11 月 14 日當週初領失業金 20.3 萬人（高於預期 19.7 萬、續領增 7 萬至 176.3 萬）**，同時間 **11 月費城聯準製造業指數急降至 6.3（前值 20.9、預期 23.2，新訂單降至 -0.4），但支付價格指數跳升 15 點至 58.2（4 月以來新高）、收取價格升至 47.0（2022/06 以來新高）**（https://mlq.ai/news/jobless-claims-edge-up-to-203000-as-the-philadelphia-fed-index-falls-to-a-six-month-low-and-prices-paid-jump/ ，台北時間 2026-11-20）。稍後 Goolsbee 將於 **美東 11/19 12:30（台北 11/20 01:30）**座談（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）、Barkin 將於 **美東 11/19 15:00（台北 11/20 04:00）**座談、理事會同時間召開閉門貼現率會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）。

### FED-4｜利率期貨隱含 12 月 9 日升息機率：升息 1 碼 93%、升息 2 碼 7%（更新至 00:08 台北定價）
- 事實：依據芝加哥期交所 30 天聯邦基金期貨（11/19 報價，本站 `c-econ-7` 00:08 更新）與媒體引述 CME FedWatch 數據，市場定價 12/8–9 FOMC **升息 1 碼（25 bp）機率約 93%、升息 2 碼（50 bp）約 7%**，2027 年 1 月續升 1 碼機率約 71%、3 月續升 1 碼機率約 66%（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ）。

---

### B｜Claude 指定查證（依任務單第 10 版題目更新至台北 00:42）

### TASK-B1｜截至台北 00:39（美東 11:39）Anthropic（ANT）仍未開出首筆公開成交，指示開盤價進一步升至 $110（+32.5%）；^NDX 翻紅至 +0.61%、AMD 因做空報告逆勢 -5.44%
- 事實（Anthropic 首日狀態）：ANT 定價 **83.00 美元**（9.8 億股、公開募資 **813.1 億美元**＋260 億同步私募），執行長 Dario Amodei 敲響開市鐘後進入那斯達克開盤集合競價。《衛報》財經直播於倫敦 **16:26–16:29 GMT（美東 11:26–11:29／台北 00:26–00:29）** 更新指出，**正式開盤價仍未拍板，最新委託搓合指標顯示開盤價可望高達 110 美元（較發行價跳漲約 +32.5%）**（https://www.theguardian.com/business/live/2026/nov/19/anthropic-float-stock-market-nasdaq-raises-81bn-record-ipo-latest-news-updates ；https://fortune.com/2026/11/19/anthropic-ipo-first-day-trading-nasdaq-record-valuation/ ）。截至台北 **00:39** 本站 `/api/quote` 報 `ANT` 仍停在 **$83.00（chg 0%）**，尚無正式開盤價、高低點、收盤價、成交量與穩價買盤紀錄。
- 事實（台北 00:39 盤中同鏈股價對照那指 100）：**那斯達克 100（`^NDX`）報 27,281.12（+0.61%）**，相關標的超額漲跌（相對 `^NDX`）：
  - **CRWV**：**$49.34（+3.15%）**，領先 `^NDX` **+2.54 pp**（受策略長 Brian Venturo 個人購入 $3,000 萬美元自家無擔保債券支撐，https://www.tradingview.com/news/seekingalpha:5ceeae8c6094b:0-coreweave-co-founder-discloses-bond-purchase-says-he-will-hold-until-maturity/ ）。
  - **IREN**：**$15.36（+0.79%）**，領先 `^NDX` **+0.18 pp**。
  - **ORCL**：**$115.25（+1.19%）**，領先 `^NDX` **+0.59 pp**。
  - **NBIS**：**$105.95（-0.94%）**，落後 `^NDX` **-1.55 pp**。
  - 出資晶片商：**MU $733.01（+3.93%，領先 +3.32 pp）**、**AVGO $360.80（+1.91%，領先 +1.30 pp）**、**NVDA $153.47（+1.66%，領先 +1.05 pp）**、**AMD $501.29（-5.44%，落後 -6.05 pp，遭 Hunterbrook 發表做空報告重挫）**（https://newsletter.hntrbrk.com/p/amd-has-its-own-china-problem ）。

### TASK-B2｜11/19 美股盤後財報（INTU、ROST、GAP、KEYS）尚未公布；列出最新市場共識（含 GAAP／Non-GAAP 口徑）（無新進展）
- 事實：四家公司皆排定於 **美東 11/19 收盤後（台北 11/20 05:00 後）**發布財報，截至 00:42 尚未揭曉，盤後股價反應尚未產生。各家市場共識如下：
  1. **Intuit（INTU，Q1 FY27）**：Zacks／EarningsWhispers 共識營收 **43.0 億～43.1 億美元**、**Non-GAAP EPS 2.46–2.47 美元**（公司原財測 Non-GAAP EPS 2.44–2.48 美元，https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ；https://www.zacks.com/stock/news/3030690/intuit-intu-expected-to-beat-earnings-estimates-what-to-know-ahead-of-q1-release ）。
  2. **Ross Stores（ROST，Q3 FY26）**：Zacks／EarningsWhispers 共識營收 **62.0 億～62.3 億美元**、**GAAP 稀釋 EPS 1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ）。
  3. **Gap（GAP，Q3 FY26）**：Zacks／EarningsWhispers 共識營收 **40.1 億～40.2 億美元**、**調整後 EPS 0.73–0.78 美元**（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）。
  4. **Keysight（KEYS，Q4 FY26）**：TradingView／FactSet 引述共識營收 **19.5 億美元**、**Non-GAAP EPS 3.37–3.38 美元**（公司先前財測 Non-GAAP EPS 3.34–3.40 美元；註：本站日曆列 3.09 美元，與公司指引及共識差約 0.28 美元，https://www.tradingview.com/news/tradingview:dd00407af5aef:0-keys-q4-26-earnings-eps-estimate-is-3-37-usd/ ）。

### TASK-B3｜11/19 晚間 Goolsbee（01:30 台北）／Barkin（04:00 台北）尚未發言，10Y TIPS 增額標售（02:00 台北）尚未截標；先給公開行程、前期立場與 WI 殖利率（無新進展）
- 事實（聯準會官員談話）：Goolsbee 將於 **美東 11/19 12:30（台北 11/20 01:30）**於印第安納經濟俱樂部發言（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）、Barkin 將於 **美東 11/19 15:00（台北 11/20 04:00）**座談，兩場皆尚未舉行。兩人最近一次公開關鍵原話分別為：
  - **Goolsbee（11/11 評 10 月通膨）**：警告美國通膨已擴散至能源以外領域，聯準會目前「並非走在回到 2% 的路徑上（`not on a path back to 2%`）」，「我們絕對還有工作要做（`definitely have work to do`）」以維護央行公信力（https://www.cnbc.com/2026/11/11/goolsbee-october-inflation-fed-rates-disturbing-distressing.html ）。
  - **Barkin（近期訪談）**：指出在失業率近低點且通膨過高的情況下，政策方向很清楚，但主張審慎漸進校準步調。
- 事實（10 年期 TIPS 增額標售）：美國財政部今日標售 **190 億美元** 10 年期 TIPS 增額（9 年 8 個月期，CUSIP **`91282CRE3`**，票面利率 **2.375%**，2036/07/15 到期，11/30 交割），競爭性投標於 **美東 13:00（台北 11/20 02:00）**截標，截至 00:42 得標利率與投標倍數尚未出爐；標售前（When-Issued）實質殖利率報約 **2.87%**（https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ；https://tipswatch.com/2026/11/15/this-weeks-10-year-tips-auction-shows-a-lot-of-potential/ ）。

### TASK-B4｜11/20 台股尚未開盤（今日 09:00 開盤）；金管會 1,028 檔限空令 2.0 將於開盤正式上路（無新進展）
- 事實：台北 11/20 台股正規盤（09:00 開盤）尚未開始，開盤一小時漲跌、成交量、最新融資維持率與新違約交割皆尚未產生。前一日收盤基準為加權 **38,426.89 點（-1,768.02 點）**、櫃買 **285.33 點（-7.22%）**、盤後通報 3 檔違約交割合計 **1.29 億元**（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），金管會對 **1,028 檔**收盤跌 ≥3.5% 個股禁平盤下放空並把借券上限由 3% 降至 1%（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。

### TASK-B5｜免費、每日更新之公開資料頁實測結果：甲骨文公司債價格／殖利率「有」，IG 科技債利差與非公開 BDC 限贖「沒有」（無新進展）
- 事實：
  1. **投資級科技公司債利差**：**沒有**。FRED 只免費每日更新美國整體投資級主指數 OAS（`BAMLC0A0CM`：https://fred.stlouisfed.org/series/BAMLC0A0CM ）及評等子指數（`BAMLC0A4CBBB`），不免費提供 ICE BofA 科技產業子指數。
  2. **甲骨文公司債價格或殖利率**：**有**。Markets Insider 甲骨文公司債日報頁（11/19 更新價格 86.86 美元、並同列多檔長債每日殖利率 8.21%–8.61%）：https://markets.businessinsider.com/bonds/oracle_corpdl-notes_202020-30-bond-2030-us68389xbv64 ；另 FINRA Fixed Income Data（TRACE）公開免費查詢入口：https://www.finra.org/finra-data/fixed-income 。
  3. **非公開 BDC 贖回限制公告**：**沒有每日更新頁**（僅每季透過 SEC EDGAR 申報 `Schedule TO-I` 與 `8-K`）；民間公開彙整追蹤頁為 CrowdfundedWealth BCRED 贖回統計頁：https://www.crowdfundedwealth.com/articles/blackstone-private-credit-fund-bcred-redemptions-2026 。

### TASK-B6｜11/24 盤前四家零售商同店銷售（Comp Sales）市場預期查核：BBY 偏溫和、DLTR 穩健、DKS 核心強但含併購拖累、BURL 偏謹慎（無新進展）
- 事實（逐家核對出處與數字）：
  1. **Best Buy（BBY）**：Compound 財報前瞻指出 FactSet 本身未單獨列示同店銷售共識，Compound 模型預估 Q3 企業同店銷售成長 **+2.6%**，落在公司指引 **+1.0% 至 +3.0%** 區間內（FactSet 營收共識 98.8 億美元、調整後 EPS $1.49，https://getcompound.ai/news/bby-q3-earnings-preview ）。
  2. **Dollar Tree（DLTR）**：公司官方 Q3 同店銷售指引為 **+3.0% 至 +4.0%**；UBS 分析師研究摘要估 Q3 同店銷售 **+3.5%**、並引述 FactSet 市場共識為 **+3.4%**（註：Moomoo 原文頁面需登入才能閱覽全文）。
  3. **Dick's Sporting Goods（DKS）**：公開新聞稿未見 FactSet／LSEG 單獨揭露 Q3 單季同店銷售百分比共識；公司維持核心 DICK'S 品牌全年同店銷售指引 **+2.5% 至 +4.0%**（上季核心同店 +4.9%），但將新併入之 Foot Locker 擬制性全年同店指引下調至 **-2.0% 至 0.0%**（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ）。
  4. **Burlington Stores（BURL）**：公司官方給予之 Q3 FY26 同店銷售指引為 **+1.0% 至 +3.0%**（較上季偏保守，反映中低所得客群壓力與將關稅退稅再投資於降價促銷；EarningsWhispers 匯總共識營收 29.7 億～30.0 億美元、EPS $1.69，https://www.earningswhispers.com/epsdetails/BURL/202607 ）。
- 推理：加上 **WSM（+5.1% 同店）**與 **WMT（美國 +2.9% 同店）**皆穩健，「消費沒壞」並非只有平價通路好，而是**必需量販＋高毛利家居／運動龍頭仍穩，但中低收入客層為主的折扣百貨需要靠降價促銷換量**的結構分化格局。

---

### CALL｜法說會與財報原話重點（過去 24 小時；無新進展）

### CALL-WSM｜Williams-Sonoma（WSM）Q3 FY26：全品牌同店 +5.1%、Non-GAAP 營益率 17.4%、重申全年展望（無新進展）
- 原話（President & CEO Laura Alber）：`"We delivered another strong quarter in Q3, with a 5.1% comp, 5.8% total revenue growth, an operating margin of 17.4%, and earnings per share growth of 11.7% to $2.19. Every brand and channel delivered a positive comp."`（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ）。

### CALL-WMT｜沃爾瑪（WMT）Q3 FY27：營收與電商廣告雙雙加速、上調全年財測至 EPS $2.84–$2.89（無新進展）
- 原話（CEO John Furner）：`"We delivered strong results, growing our core business and gaining market share. The strength of our omnichannel model gives us room to do even more."`（https://www.cnbc.com/2026/11/19/walmart-wmt-q3-2026-earnings.html ）。

### CALL-BABA｜阿里巴巴（BABA）Q2 FY27：AI 雲外部收入年增 67%、全端 AI 推升商業化（無新進展）
- 原話（CEO Eddie Wu）：`"Our full-stack AI capabilities continue to improve commercialization and delivered a strong quarter. Growth in Alibaba Cloud's recurring revenue from external customers was 67%, which drove an acceleration of overall cloud revenue growth with significantly improving profitability."`（https://investingnews.com/alibaba-group-announces-september-quarter-2026-results-and-interim-results-for-the-six-months-ended-september-30-2026/ ）。

### CALL-PDD｜拼多多（PDD）Q3 2026：營收持平下持續投資供應鏈以因應貿易與監管變化（無新進展）
- 原話（Co-CEO Lei Chen）：`"As our global business adapts to an evolving trade and regulatory environment, we remain committed to deepening our supply chain investments."`（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ）。

### CALL-NTES｜網易（NTES）Q3 2026：遊戲營收微降但毛利增 4.8%、持續推進跨平台新遊研發（無新進展）
- 原話（CEO William Ding）：`"While we continue to evolve our established titles with content and gameplay mechanics that appeal to a broader range of players, we are also steadily advancing our titles in development across genres, platforms and markets."`（https://www.prnewswire.com/news-releases/netease-announces-third-quarter-2026-unaudited-financial-results-302945011.html ）。

### CALL-PANW｜Palo Alto Networks（PANW）Q1 FY27 法說會：NGS ARR 年增 66%、斥資 45 億美元併購 Applied Compute（無新進展）
- 原話（CEO Nikesh Arora）：`"As AI reshapes the threat landscape, we must continually evolve to protect our customers and enable them to adopt AI securely. To that end, we are pleased to announce our intent to acquire Applied Compute, which will allow us to deliver secure open weight models to our customers and accelerate the adoption of enterprise AI."`（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ）。

### CALL-P｜Everpure（NYSE: P，原 Pure Storage）Q3 FY27 法說會：營收年增 51%、連三季上調全年財測（無新進展）
- 原話（CFO Tarek Robbiati）：`"Our results reflect the strength of our diversified portfolio, with our core and core AI offerings complemented by increasing contributions from our new businesses. We are raising full-year guidance for the third consecutive quarter and reiterating our strong preliminary FY28 outlook, underscoring confidence in our durable business model and broad-based momentum."`（https://www.prnewswire.com/news-releases/everpure-announces-third-quarter-fiscal-2027-financial-results-302944321.html ）。

### CALL-NVDA｜輝達（NVDA）Q3 FY27 法說會：營收 1,158 億美元、下季財測排除中國（無新進展）
- 原話：`"Our momentum is real... Customers, suppliers, and partners are 100% behind us. We’ve got this."`（https://www.cnbc.com/2026/11/18/nvidia-stock-earnings.html ）。

---

### NEXT-1｜事件：Hunterbrook 做空 AMD 揭露實體清單伺服器商（IEIT／Aivres／Kaytus）韌體鏈＋BIS 取消「非 AI 用途」豁免（更新 AMD 做空傳導）
- 推理：
  - 最先受影響的資產：具備較高中國／香港／新加坡帳單營收比重之美國 AI 晶片設計商（AMD 2025 財年中國＋香港營收 77.51 億美元、新加坡 42.84 億美元）、BIOS／伺服器韌體及品牌代工伺服器廠。
  - 傳導路徑：BIS 11/19 生效新規已把新加坡、馬來西亞、印尼、泰國、巴西列入高轉運風險國並取消手機等「非 AI 用途」豁免（https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors ），而 Hunterbrook 今日揭露即使不透過直接銷售，實體清單廠仍透過關聯企業（加州 Aivres、新加坡 Kaytus）取得同步伺服器韌體（https://newsletter.hntrbrk.com/p/amd-has-its-own-china-problem ）。一旦美方將盡職調查延伸至「BIOS／韌體釋出與海外關聯白牌 OEM」，品牌伺服器與台系委外封測廠將面臨更長的合規清查與拉貨遞延：
    - 美股：**AMD、NVDA、SMCI、DELL、HPE**。
    - 台股：**台積電 (2330)、聯發科 (2454)、日月光投控 (3711)、英業達 (2356)、信驊 (5274)**。
  - 大家還沒注意到的間接受害者：**專為美系 x86／AI 伺服器提供 BIOS 韌體、BMC 遠端管理晶片及白牌系統整合之上下游業者，以及仰賴東南亞新加坡樞紐組裝出貨的品牌 OEM**——當合規審查從「晶圓與 GPU 本體」擴張到「韌體更新包與關聯系統商」，合規成本與交期將全面拉長。

### NEXT-2｜事件：歐元區 10 月通膨終值衝上 4.0%＋費城聯準製造業指數急跌至 6.3 而支付價格飆至 58.2＋ECB 2026 SREP 鎖定私募信貸檢查（更新停滯性通膨與雙緊縮傳導）
- 推理：
  - 最先受影響的資產：歐美短端利率期貨、歐元區銀行股與主權債利差、美國工業與中小型製造業景氣循環股、私募信貸／BDC。
  - 傳導路徑：歐元區 10 月通膨確定達 **4.0%**（ECB 目標兩倍，https://ec.europa.eu/eurostat/web/products-euro-indicators/w/2-18112026-ap ）推升 ECB 12/17 升息預期；美國同日費城聯準製造業指數由 20.9 摔至 **6.3**（新訂單轉負）、支付價格卻跳升 15 點至 **58.2**（https://mlq.ai/news/jobless-claims-edge-up-to-203000-as-the-philadelphia-fed-index-falls-to-a-six-month-low-and-prices-paid-jump/ ），加上 ECB SREP 鎖定 **私募信貸與 NBFI** 實地檢查及 11/25 準備金率倍增辯論（https://live.euronext.com/en/financial-news/nearly-all-euro-zone-banks-are-struggling-tech-risks-ecb-says ），實體製造業已無法靠降息紓困，同時要承擔高原料成本與歐美銀行授信收緊：
    - 美股：**CAT、DE、HON、APO、BX**。
    - 台股：**國泰金 (2882)、富邦金 (2881)、中信金 (2891)、亞德客-KY (1590)、上銀 (2049)**。
  - 大家還沒注意到的間接受害者：**尚未完成 2027 年到期債務再融資的中型製造業與商用不動產借款人，以及在歐洲與美國同時面臨高美元／歐元避險成本的台灣壽險業**。

### NEXT-3｜事件：華爾街 5,000 億美元輝達融資案實際撥款仍為 0 美元＋Waymo 遭加州 DMV 禁行高速公路＋銅／錫去槓桿急挫（更新實體 AI 與債務傳導）
- 推理：
  - 最先受影響的資產：依賴外部專案融資擴張 GPU 機櫃的新雲端公司（CRWV、NBIS、IREN）、LME 銅／錫期貨、自駕車商業化概念股。
  - 傳導路徑：WSJ 今日揭露 8 月簽署的 5,000 億美元運算融資 MOU 撥款仍為 0 美元（https://mlq.ai/news/wall-street-has-not-put-up-any-of-the-500-billion-it-pledged-for-nvidia-customers-the-wsj-reports/ ），與加州 DMV 勒令 Waymo 停駛高速公路（https://www.kqed.org/news/12110123/hazard-to-public-safety-california-dmv-restricts-waymo-freeway-operations ）及銅／錫急跌（https://www.tradingview.com/news/seekingalpha:cb0deccc9094b:0-copper-extends-slide-to-lowest-level-since-april-on-firm-dollar-ai-doubts/ ）指向同一件事：AI 從「算力建設」走向「實體商轉與回本」的速度正受到資金與監管雙重限制：
    - 美股：**NBIS、CRWV、GOOGL、UBER、FCX**。
    - 台股：**鴻海 (2317)、廣達 (2382)、緯穎 (6669)、華城 (1519)、中興電 (1513)**。
  - 大家還沒注意到的間接受害者：**已依非綁定算力租約提前備料之重電變壓器廠，以及把「2027 年自駕／實體 AI 商用滲透率跳升」計入估值倍數的光達與車用感測供應商**。

---

### RED-1｜針對 `forecast.json`「消費、運輸與進口商品：下修」及 `claude_notes.md`「消費沒壞→對借錢 AI 公司更不利」（無新進展）
- 最強反方證據：今日盤前公布的 **WSM Q3 同店 +5.1%、Non-GAAP 營益率 17.4%、EPS $2.19 優於預期**（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ），加上 **WMT 美國同店 +2.9% 並上調全年展望**、**TJX 全球同店 +4%**、**LOW 營收成長逾 9%**，顯示零售龍頭並未全面下修；另 **2017 年升息循環**亦曾出現消費強反而使高收益債利差維持 3.4%–3.5% 並帶動那指大漲 28.24% 的反例。
- 另一種同樣說得通的解釋：美國消費並未全面下修，而是「具議價力與直接採購優勢的龍頭搶走中小通路商市占」，與中低客層折扣百貨（BURL +1%～3%）形成分化，且今晚 **費城聯準製造業指數驟降至 6.3、續領失業金升至 176.3 萬**顯示實體製造與續領端正悄悄降溫。
- 判斷分曉的資料與日期：**2026-11-24 盤前 BBY、DLTR、DKS、BURL 財報與同店銷售實際值**。
- 機率估計：將「風險升級」維持 **40%**（對比你調升後的 **36%**，相差 4 個百分點）。

### RED-2｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（雙方皆降至 30%）」（無新進展）
- 最強反方證據：BEA 9 月核心 PCE 年增已確為 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ），本站 `#econ`《PCE 物價》卡片估算 10 月核心 PCE 年增約 **3.2%**、The Conference Board 預估 **3.3%**（https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026 ）。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 比照 BLS 無法發布 10 月年增率，該題將依規則留空「無法判定」。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：維持 **30%**（與你本輪下修後的 **30%** 完全一致，差距 0 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 58% vs Gemini 55%）」（補充 NYT 空襲報導）
- 最強反方證據：WTI 現價約 **$83.52**（僅距下緣 3.5 美元），11/18 EIA 汽油／原油連續累庫（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ）及美中俄深圳宣言計畫增供成品油壓抑下緣；但上緣風險今日再升溫——《紐約時報》揭露川普正權衡對伊朗發動 4–7 天空襲（https://investinglive.com/commodities/nyt-trump-weighs-new-iran-strikes-as-israel-presses-for-a-four-to-seven-day-air-campaign/ ），荷莫茲海峽油輪遇襲不斷。
- 另一種同樣說得通的解釋：原油正處於雙尾風險拉扯，若美伊未動武且下週 EIA 再大額累庫即可能跌破 80 美元；反之若空襲啟動則極易衝破 100 美元。
- 判斷分曉的資料與日期：**2026-11-25、12/02 EIA 每週庫存報告**與 **IMF PortWatch 荷莫茲通行量**。
- 機率估計：維持 **55%**（比你的 **58%** 低 3 個百分點）。

### RED-4｜針對 `dots_read.json`「輝達執行長離任是因晶片流入中國遭調查而緊急切割」（無新進展）
- 最強反方證據：輝達 11/17 財報與法說會並未揭露任何司法部或商務部正式執法處分；中央社引述《福斯新聞》稱涉案女子同受中國情報與晶片走私調查（https://www.cna.com.tw/news/aopl/202611193003.aspx ），但台積電高層張曉強親赴總部確認 Rubin 與 CoWoS 訂單照舊。
- 另一種同樣說得通的解釋：私人治理與缺乏坦誠先觸發董事會 11/11 立即切割，而涉案對象本身牽連調查，「個人治理＋國安調查」兩線交織。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節）**。
- 機率估計：維持「兩線交織」**70%–75%**，「單純私人治理、完全無涉出口調查」**25%–30%**。

### RED-5｜針對 `forecast.json`「10 年期美債（新）：4.85%–5.45%（70%）」與「12/9 聯準會不會升 2 碼（85%）」（更新 10Y 回落至 5.072% 與費城聯準數據）
- 最強反方證據：雖然今夜美債 10 年期殖利率在費城聯準製造業指數驟降至 6.3 後自 5.10% 回落至 **5.072%**，但全球央行與通膨訊號同步偏鷹——歐元區 10 月通膨終值衝上 **4.0%**（https://ec.europa.eu/eurostat/web/products-euro-indicators/w/2-18112026-ap ）、ECB 11/25 擬辯論把銀行準備金率倍增至 2%（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ）、日銀植田和男為 12 月升息鋪路（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ）、費城聯準支付價格跳升 15 點至 **58.2**，且聯準會理事 Waller 主張 12 月考慮升息 50 基點。
- 另一種同樣說得通的解釋：一方面歐日債殖利率同步走高可能把美債推破 5.45%；另一方面若費城聯準這種「活動驟降＋續領失業金上升」的訊號在未來兩週擴散到全國數據，避險買債亦可能壓低長端殖利率。
- 判斷分曉的資料與日期：**2026-11-25 10 月 PCE 與 ECB 會議、2026-12-04 11 月非農就業、2026-12-09 FOMC 決議**。
- 機率估計：對「10 年期美債守在 4.85%–5.45%」維持 **60%**（比你的 **70%** 低 10 個百分點）；對「12/9 不會一次升 2 碼」維持 **80%**（比你的 **85%** 低 5 個百分點）。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與甲骨文／科技長債每日殖利率」追蹤（無新進展）
- 事實：線上《金融穩定監測》與《美國公司債》僅有全市場 IG／BBB／CCC 利差，沒有分出「表外未起租承諾」與「科技公司長債實質殖利率」。ECB Box 3 揭露大型科技商相關長期承諾規模（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：因 FRED 無科技債子指數，建議用免費每日更新的 Markets Insider 甲骨文等公司債頁面（https://markets.businessinsider.com/bonds/oracle_corpdl-notes_202020-30-bond-2030-us68389xbv64 ）搭配 SEC 10-Q `Commitments and Contingencies` 附註建立科技債務壓力指標。

### BLIND-2｜《金融穩定監測》缺少「非公開交易 BDC 季度限額贖回（Gating）與對沖基金主權債槓桿」追蹤（無新進展）
- 事實：BCRED 於 Q2 僅滿足 48.5%、Q3 僅滿足 49.9% 贖回申請（https://www.crowdfundedwealth.com/articles/blackstone-private-credit-fund-bcred-redemptions-2026 ）。免費官方資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜本站完全沒有「關鍵基礎設施／雲端／能源網攻中斷（SEC Item 1.05）」與金融監理資安警報卡片（無新進展）
- 事實：繼挪威 Equinor 遭持續性網攻（https://therecord.media/norway-equinor-cyberattack-energy ）後，ECB SREP 指出 **96% 歐元區大銀行在 IT／資安與營運風險評等不佳**（https://live.euronext.com/en/financial-news/nearly-all-euro-zone-banks-are-struggling-tech-risks-ecb-says ），英國央行與 FCA 同日指出 **10 月向 FCA 通報之金融資安事件較前高大增 52%**（https://www.bankofengland.co.uk/news/2026/november/cyber-resilience-guidance-consultation-and-ai-and-quantum-effective-practices ）。免費資料源：CISA KEV（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）。

### BLIND-4｜「台股籌碼風向計」未自動加總「三大法人台指期合計淨口數」、且缺「每日違約交割金額」與「限空令燈號」（無新進展）
- 事實：11/19 爆出 1.29 億元違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），金管會宣布 11/20 起升級 1,028 檔 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。

### BLIND-5｜本站《債券／各國風險》未追蹤「歐元區 4.0% 通膨與歐日央行銀行準備金抽水（ECB 擬倍增準備金率至 2%）」及「區域聯準製造業支付價格（Prices Paid）」（補充歐元區 4.0% 與費城聯準）
- 事實：歐元區 10 月通膨已確認達 **4.0%**（https://ec.europa.eu/eurostat/web/products-euro-indicators/w/2-18112026-ap ），ECB 11/25 擬辯論把最低存款準備金率倍增至 2%、抽走約 1,750 億歐元流動性（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ），日本央行 12 月亦朝升息至 1.50% 邁進；美國今晚費城聯準製造業指數亦出現活動驟降至 6.3 而支付價格飆至 58.2 的停滯性通膨訊號。免費資料源：ECB Statistical Data Portal（https://data.ecb.europa.eu/ ）與 Eurostat（https://ec.europa.eu/eurostat ）。

---

### SITE｜挑本站的錯（台北 2026-11-20 00:31–00:36 實測 `https://wallstreet-sentinel.pages.dev/` 與 `/api/etf` 複查）

- 複查已修好項目（均於 00:32–00:36 實測通過）：
  1. `/api/etf` 回傳 **HTTP 200**。
  2. `#econ`《IPO 觀察》（`最後更新 11-20 00:31`）已不再列 MapLight（MPLT）。
  3. `#econ`《本週重要經濟數據》（`最後更新 11-20 00:28`）`11-16 週一` 為「聯準會主席談話」、`11-17 週二` 為「零售銷售」，無重複列示。

### SITE-1｜`#econ`《美股財報日曆》（11-20 00:31 重建後）仍將今日盤前已公布之 WMT、BABA、PDD、NTES、WSM 列在「即將公布」，且 `11-19 盤後` 漏列 GAP
- 本站寫了什麼：`11-20 00:36` 實測重建後頁面（`最後更新 11-20 00:31`）在《美股財報日曆》`即將公布（21 天內）` 仍印著：`11-19 週四 盤前 沃爾瑪 WMT 消費 0.64 13 0.62 +3%`、`11-19 週四 盤前 Alibaba Group Holding Limited BABA`、`11-19 週四 盤前 PDD Holdings Inc. PDD`、`11-19 週四 盤前 NetEase, Inc. NTES`、`11-19 週四 盤前 Williams-Sonoma, Inc. WSM`；同時《各公司最新財報重點》（`c-econ-10`）卻已經收錄 `沃爾瑪 WMT 消費 2026-11-19 SEC 8-K 本季：營收 US$188.80B`。此外 `11-19 盤後` 仍只有 INTU、ROST、KEYS，缺少 **GAP**。
- 正確應該是什麼：WMT（https://www.cnbc.com/2026/11/19/walmart-wmt-q3-2026-earnings.html ）、BABA、PDD、NTES 與 WSM 皆已於 11/19 盤前公布財報，應從《美股財報日曆》「即將公布」移除（目前該規則似乎僅生效於倒數卡而未套用至《美股財報日曆》）；GAP 排定 11/19 盤後公布 Q3 財報（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）。

### SITE-2｜`#news`《未來 14 天事件》（11-20 00:28）仍未標示「TIPS」且持續漏列台股／國際重大排程
- 本站寫了什麼：`#news`《未來 14 天事件》（`最後更新 11-20 00:28`）仍印 `11-19 美債 10 年期標售（增額） $19B`（未標明 TIPS），且仍漏列 11/20 台股限空令 2.0／台灣 10 月外銷訂單／SNDK 1 拆 8 拆股、11/21 韓國 1–20 日出口、11/25 聯準會褐皮書與 ECB 管委會準備金率討論、11/26 感恩節休市與韓銀決策、11/28 台灣九合一選舉、11/29 OPEC+ 會議。
- 正確應該是什麼：該筆 $19B 標售為 **10 年期 TIPS 增額**（CUSIP `91282CRE3`，https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ）。

### SITE-3｜`#econ`《IPO 觀察》（11-20 00:31）仍將已流標取消之「宏偉 11-19、耐特 11-19」列為即將掛牌，小型美股 IPO 仍印出「約 0 億美元～0 億美元」
- 本站寫了什麼：`11-20 00:36` 抓取之 `#econ`《IPO 觀察》（`最後更新 11-20 00:31`）仍寫著「`台股已公告 4 家即將掛牌（宏偉 11-19、耐特 11-19、宏于電機 11-26、騰勢 12-01）`」；且 `VME Companies, Inc.`、`Alopexx, Inc.`、`KAT Construction Services, Inc.` 仍印出「`約 0 億美元～0 億美元`」。此外，今日焦點 **Anthropic（ANT）** 截至台北 00:39 尚未開盤成交，但 `#overview`《接下來 72 小時》卻顯示「`接下來 72 小時沒有排定的大事。`」。
- 正確應該是什麼：**耐特（8058）**與**宏偉（4565）**已於 11/09–11/10 因競拍合格投標不足宣布不予開標並取消本次承銷及掛牌作業（https://news.cnyes.com/news/id/6653937 ；https://ww2.money-link.com.tw/realtimenews/NewsContent.aspx?SN=2441867002&PU=0009 ），應予排除；低於 0.5 億美元的 IPO 金額建議改用百萬美元或小數兩位顯示。

### SITE-4｜`#overview`《每日總經情勢》22:36「緊急加班」仍稱「昨日醫療保健股急跌找不到時間對得上的消息」（與本站 `#news` 自家紀錄矛盾）
- 本站寫了什麼：`每日總經情勢` 22:36 `緊急加班` 仍保留「`醫療保健類股跌了百分之二點二...原因我找不到時間對得上的消息，所以老實說：還不知道原因`」。
- 正確應該是什麼：美股週三（11/18）醫療保健板塊重挫主因 UNH 等權值股持續消化 **CMS 11/16–17 發布《CRUSH》追溯至 2018 年稽核擬議規則**（且該規則 11/19 正式刊登聯邦公報，本站 `c-news-4` 亦已寫「`2026-11-19・規則草案・Health and Human Services Department 醫療保險與藥價：CRUSH 刊登當天 醫療保健 ETF -2.0%，比平常大一些`」，https://www.cms.gov/newsroom/press-releases/cms-crush-proposed-rule-aims-reap-nearly-90-billion-taxpayers-savings-targeting-fraud-across ）。

---

### CAL-1｜未來 14 天（2026-11-20 ～ 2026-12-04）關鍵行事曆（對照 live `#news` 00:28 與 `#econ` 00:31）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19 夜盤～11/20 凌晨**：**Anthropic（ANT）** 仍待那斯達克開盤集合競價首筆成交（指示價 $110，https://www.theguardian.com/business/live/2026/nov/19/anthropic-float-stock-market-nasdaq-raises-81bn-record-ipo-latest-news-updates ）；台北 11/20 01:30（美東 12:30）**Goolsbee** 座談；台北 11/20 02:00（美東 13:00）**美債 10 年期 TIPS 增額標售 $19B（CUSIP 91282CRE3）**（https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ）；台北 11/20 04:00（美東 15:00）**Barkin** 座談與聯準會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP、KEYS** 財報。
  2. **11/20（五）**：**台股金管會 1,028 檔 3.5% 限空令 2.0 上路**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；**印度強氣旋「阿克萬（Akvan）」中午登陸奧里薩邦**（https://www.thehindu.com/news/national/odisha/odisha-puts-eight-districts-on-high-alert-as-severe-cyclonic-storm-akvan-advances-towards-coast/article71716731.ece ）；**台灣 10 月外銷訂單**（台北 16:00，https://money.udn.com/money/story/10869/9879179 ）；美東盤前 **BSP** 財報；**美股月選擇權到期（OPEX）**；**密大消費者信心終值**（美東 10:00／台北 23:00）；**SanDisk（SNDK）1 拆 8 拆股首日交易**。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM、A** 財報。
  5. **11/24（二）**：美東盤前（台北 20:00–21:00）**ADI、MDT、BBY、DLTR、BURL、DKS、BILI**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY**。
  6. **11/25（三）**：美東盤前 **DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與提前公布之週初領失業金；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**；**ECB 管理委員會辯論銀行準備金率倍增至 2%**（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ）。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**；台股 **宏于電機（7869）上櫃掛牌**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/28（六）**：**台灣 2026 九合一地方選舉投票日**。
  10. **11/29（日）**：**OPEC+ 第 69 次 JMMC 與部長級會議**（https://www.opec.org/pr-detail/620-1-november-2026.html ）。
  11. **11/30（一）**：**MSCI 季度調整台股收盤生效（台北 13:30）與月底資產再平衡**。
  12. **12/01（二）**：美東 10:00（台北 23:00）**ISM 製造業 PMI 與 10 月 JOLTS**；**歐元區 11 月通膨初值（Eurostat）**（https://ec.europa.eu/eurostat/web/products-euro-indicators/w/2-18112026-ap ）；**CRWD、MRVL、OKTA、NTAP、MDB、CRDO** 盤後財報；**韓國 11 月出口初值**；台股 **騰勢（7889）掛牌**。
  13. **12/02（三）**：美東盤後 **CRM、SNOW、ZS** 財報。
  14. **12/03（四）**：美東 10:00（台北 23:00）ISM 服務業 PMI；美國參議院銀行委員會先進晶片出口聽證會。
  15. **12/04（五）**：美東 08:30（台北 21:30）**美國 11 月非農就業報告**。
- 對照本站（live `#news`《未來 14 天事件》`11-20 00:28` 與 `#econ`《美股財報日曆》`00:31`）：
  - **漏列項目**：11/20 金管會限空令 2.0、SNDK 拆股、台灣 10 月外銷訂單；11/21 韓國 20 日出口；11/25 聯準會褐皮書與 ECB 準備金率討論；11/26 韓國央行與感恩節休市（未列於《未來 14 天事件》）；11/28 台灣九合一選舉；11/29 OPEC+；12/01 歐元區 11 月通膨初值；`GAP` 未列於 11/19 盤後財報。
  - **錯置／未更新項目**：11/19《未來 14 天事件》`美債 10 年期標售（增額）$19B` 漏標「TIPS」；《美股財報日曆》仍保留已公布之 WMT、BABA、PDD、NTES、WSM；《IPO 觀察》仍列已流標取消之宏偉與耐特。

---

### SENT-1｜Anthropic（ANT）IPO 與盤中苦等首筆開盤成交（r/wallstreetbets）— 零星配股截圖與估值／資本支出激辯（無新進展）
- 討論內容與情緒：11/19 r/wallstreetbets 洗版曬出券商僅獲配 2～10 股的零星配股截圖，多空圍繞招股書長期算力承諾與 1.5 兆美元估值激辯（情緒，非事實；原串受 Reddit 爬蟲防護限制，網址由搜尋確認：https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ）。

### SENT-2｜AMD 遭 Hunterbrook 做空急殺與 AI 類股疲態（r/wallstreetbets / r/stocks）— 爭議做空報告是否實錘違規
- 討論內容與情緒：美東盤中散戶高度關注 **Hunterbrook 做空 AMD** 導致股價一度跌近 9%，多方質疑報告自身坦承「尚未證明 AMD 直接出口違法」，空方則擔憂實體清單韌體追查引發美國商務部進一步審查，並延續本週 AI 類股動能疲態（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-3｜台股 11/19 暴跌 1,768 點、限空令 2.0 與夜盤開高走低（PTT 股板／CMoney 同學會）
- 討論內容與情緒：PTT 股板 `[閒聊] 2026/11/19 盤後閒聊`（https://www.pttweb.cc/bbs/Stock/M.1795068032.A.16B ）與限空令串（https://www.pttweb.cc/bbs/Stock/M.1795069467.A.DAC ）熱議上市 128 檔／上櫃 156 檔跌停、1.29 億違約交割；晚間 23:39 社群（https://mobile.cmoney.tw/forum/user/467868 ）轉而盯緊融資單日大減 236 億元以及台指期夜盤一度大漲後回吐的震盪（情緒，非事實）。

### SENT-4｜UNH／CMS 草案與 Waymo 遭禁行加州高速公路（r/stocks / r/wallstreetbets）
- 討論內容與情緒：散戶討論 **UNH** 跌破 330 美元是否已反映 CMS CRUSH 草案，並傳播 **Waymo 遭加州 DMV 禁止行駛高速公路**的消息對 Alphabet 與自駕車產業的衝擊（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ）。

### SENT-5｜PANW 財報併購帶動資安齊漲 vs PDD 砍費用大漲（r/wallstreetbets / r/stocks）（無新進展）
- 討論內容與情緒：討論 PANW 財報與 45 億美元併購 Applied Compute 帶動 CRWD／FTNT 齊漲，以及 PDD 靠壓低行銷支出大勝預期的獲利結構（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

---

### CODE-1｜wsb/data/earn_release.py：第 463–468 行（`sanitize`）將 `next_q` 營收指引改判為 `year` 的區間（2.5–5.5 倍）與隨後過濾 `year` 的區間（3.0–5.0 倍）前後矛盾，導致 2.5–3.0 與 5.0–5.5 倍直接被丟棄
- 檔案路徑與行號：`wsb/data/earn_release.py` 第 463–468 行（`sanitize`）。
- 那一行在做什麼：
  - 第 462–466 行：當 `g["period"] == "next_q"` 且 `r = g["mid"] / base` 不在 `[0.75, 1.5]` 時，若 `2.5 <= r <= 5.5` 會把該筆營收指引改判為 `g["period"] = "year"`。
  - 第 467–468 行：緊接著檢查 `if g["period"] == "year" and not (3.0 <= r <= 5.0): continue`，把不在 `[3.0, 5.0]` 的全年指引直接丟棄。
- 為什麼有問題：
  1. 第 463 行刻意開到 `[2.5, 5.5]`，但 `[2.5, 3.0)` 與 `(5.0, 5.5]` 兩段在經過第 464 行改判成 `"year"` 後，立刻在第 467 行被 `3.0 <= r <= 5.0` 條件全部過濾掉，屬於前後矛盾的死碼區間。
  2. 對季節性極強的零售商（例如第 4 季旺季單季營收佔全年超過三分之一，`FY / Q4 < 3.0`）或高成長 AI 公司（隔年全年營收指引超過最近一季 5 倍），第 467 行只用 `3.0 <= r <= 5.0` 容易誤刪正確的全年財測。
- 建議怎麼改：將第 467 行邊界與第 463 行對齊為 `2.5 <= r <= 5.5`（或依產業季節性與高成長容忍度再放寬），避免剛從第 464 行救回的資料在第 467 行被立刻丟棄。
- 確定度：高（已逐行核對第 456–471 行邏輯；本小時 `index % 24 == 0` 共 13 檔：`functions/api/etf.js`、`tools/site_capex.py`、`tools/site_fiscal.py`、`tools/site_preview.py`、`tools/sys_health.py`、`wsb/analytics/credit_health.py`、`wsb/analytics/intel.py`、`wsb/analytics/rulebook.py`、`wsb/analytics/vol_breadth.py`、`wsb/data/earn_release.py`、`wsb/data/fund_global.py`、`wsb/data/sec_officers.py`、`wsb/morning.py` 皆已逐一讀完。另補充 `wsb/data/sec_officers.py` 第 299–300 行先算出 `have` 集合卻對 `earn_direct(due, set(), now)` 傳入空集合，雖第 301 行有再去重不影響最終結果，僅使函式內部早跳過失效，屬極輕微瑕疵；其餘 11 檔未見須呈報問題）。

---

其他今天的大事：
- **Hunterbrook 發布報告做空 AMD 並指實體清單中企 IEIT 持續取得新韌體**：報告稱 IEIT 於 2025/03 被美列入實體清單後仍發布含至少六個較新版本 AMD 韌體的 BIOS 更新（最近為 10/19），關聯商 Aivres（加州）、Kaytus（新加坡）、Maginfra（中國）使用近乎相同韌體，引發 AMD 盤中急跌逾 5%–8%（https://newsletter.hntrbrk.com/p/amd-has-its-own-china-problem ；https://247wallst.com/investing/2026/11/19/amd-is-down-8-after-short-seller-hunterbrook-ties-its-firmware-to-blacklisted-chinese-server-maker-resilient-intel-remains-up-5/ ）。
- **美國初領失業金升至 20.3 萬＋費城聯準製造業指數驟降至 6.3 但支付價格暴升至 58.2**：美東 11/19 08:30 公布初領 203K（續領增 7 萬至 1,763K），費城聯準指數自 20.9 急跌至 6 個月新低 6.3（新訂單轉負至 -0.4），但支付價格指數跳升 15 點至 58.2、收取價格升至 47.0（2022/06 以來新高），呈現「活動放緩＋物價再跳」的停滯性通膨組合（https://mlq.ai/news/jobless-claims-edge-up-to-203000-as-the-philadelphia-fed-index-falls-to-a-six-month-low-and-prices-paid-jump/ ）。
- **《紐約時報》揭川普權衡對伊朗發動 4–7 天新一波空襲**：因情報指伊朗重建飛彈與無人機庫存，以色列敦促美方聯合空襲，推升 WTI 原油反彈至 $83.52（https://investinglive.com/commodities/nyt-trump-weighs-new-iran-strikes-as-israel-presses-for-a-four-to-seven-day-air-campaign/ ）。
- **歐元區 10 月通膨終值確認升至 4.0%（三年新高）**：Eurostat 確認 10 月年通膨率由 3.8% 升至 4.0%（能源年增 21.0%），強化 ECB 12/17 升息預期（https://ec.europa.eu/eurostat/web/products-euro-indicators/w/2-18112026-ap ）。
- **加州 DMV 勒令 Waymo 停駛高速公路自駕營運並擴大至全美暫停**：因灣區施工區與 CHP 交通管制隊事件被列為「公共安全立即危險」，Waymo 暫停全美高速公路商業營運（https://www.kqed.org/news/12110123/hazard-to-public-safety-california-dmv-restricts-waymo-freeway-operations ）。
- **華爾街 5,000 億美元輝達運算融資計畫撥款仍為 0 美元**（https://mlq.ai/news/wall-street-has-not-put-up-any-of-the-500-billion-it-pledged-for-nvidia-customers-the-wsj-reports/ ）、**哥倫比亞 11/19 全國大罷工反 19% 食物 VAT**（https://colombiareports.com/colombias-labor-unions-and-social-organizations-call-national-strike-on-november-19/ ）及 **印度強氣旋「阿克萬」逼近奧里薩邦八縣高度戒備**（https://www.thehindu.com/news/national/odisha/odisha-puts-eight-districts-on-high-alert-as-severe-cyclonic-storm-akvan-advances-towards-coast/article71716731.ece ）。

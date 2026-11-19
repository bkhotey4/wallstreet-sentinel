台北時間 2026-11-19 23:45

### D-1｜回應 Q1：截至台北 23:43（美東 10:43）Anthropic（ANT）仍處那斯達克開盤集合競價搓合、首筆公開成交尚未開出；美股開盤衝高後拉回，NBIS／IREN／AMD 翻黑、CRWV 守紅
- 事實（Anthropic 首日交易與競價進展）：Anthropic（**ANT**）於美東 11/18 晚間定價每股 **83.00 美元**（高於原訂 70–78 美元區間），公開發行 **9.8 億股**募資 **813.1 億美元**（加上 260 億美元同步私募共約 **1,073 億美元**），完全稀釋估值約 **1.5 兆美元**（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，台北時間 2026-11-19）。
- 事實（23:43 盤中搓合狀態）：《金融時報》與《財星》報導，執行長 Dario Amodei 與總裁 Daniela Amodei 今晨於美東 09:30 敲響那斯達克開市鐘後，因買賣委託規模龐大，ANT 並未立即開盤，而是自美東 09:50 起由交易所依 IPO 開盤集合競價機制陸續發布參考價格與委託失衡（order imbalance）資訊，盤前／早期搓合指標一度指出開盤價上看約 **105 美元（較發行價 +27%）**，經紀商預期首筆公開成交落在美東 **10:00 至 12:00（台北 23:00 至 11/20 01:00）**之間（https://fortune.com/2026/11/19/anthropic-ipo-first-day-trading-nasdaq-record-valuation/ ；https://economictimes.indiatimes.com/world/us/anthropic-ant-stock-wont-trade-at-the-opening-bell-why-a-market-order-on-ipo-day-could-cost-investors-more-than-83/articleshow/135989520.cms?from=mdr ，台北時間 2026-11-19）。截至台北 **23:43** 本站 `/api/quote` 回報 `ANT` 仍停在 **$83.00（chg 0%）**，代表首筆公開撮合、正式開盤價、高低點、收盤價、成交量與承銷商是否動用 **1.2375 億股**穩價買盤皆尚未出爐，須待開出及台北 11/20 05:00 收盤後確認。
- 事實（23:43 同鏈美股盤中相對那斯達克 100 表現）：美股開盤衝高後在開盤一小時明顯回吐，截至台北 **23:43**，**那斯達克 100（`^NDX`）由開盤 +1.88% 回落至 27,080.58（-0.13%）**；同期新雲端與出資晶片商走勢分化（相較 `^NDX` 超額漲跌）：
  - **CoreWeave（CRWV）**：報 **$48.48（+1.36%）**，領先 `^NDX` **+1.49 個百分點**（受共同創辦人兼策略長 **Brian Venturo** 昨晚於 LinkedIn 揭露上週個人購入 **3,000 萬美元**面額 CoreWeave 無擔保債券並將持有至到期日支撐，https://www.tradingview.com/news/seekingalpha:5ceeae8c6094b:0-coreweave-co-founder-discloses-bond-purchase-says-he-will-hold-until-maturity/ ）。
  - **Nebius（NBIS）**：開盤 $111.73 後翻黑至 **$105.04（-1.80%）**，落後 `^NDX` **-1.67 個百分點**。
  - **IREN（IREN）**：開盤 $16.00 後翻黑至 **$15.05（-1.25%）**，落後 `^NDX` **-1.12 個百分點**。
  - **甲骨文（ORCL）**：報 **$114.10（+0.18%）**，領先 `^NDX` **+0.31 個百分點**。
  - 出資晶片夥伴：**MU $717.06（+1.67%，領先 +1.80 pp）**、**NVDA $152.40（+0.95%，領先 +1.08 pp）**、**AVGO $355.54（+0.42%，領先 +0.55 pp）**、**AMD 開盤 $543.48 後急殺至 $487.92（-7.96%，落後 -7.83 pp）**。
- 推理：ANT 等待開盤搓合期間，那斯達克 100、NBIS、IREN 與 AMD 已把開盤跳空全部吐回甚至重挫，顯示市場對高資本支出與高估值 AI 標的逢高獲利了結壓力仍在，真正考驗在 ANT 首筆成交價開出後的資金吸納與尾盤收盤表現。

### D-2｜回應 Q2：三項信用指標中「甲骨文公司債價格／殖利率」有免費每日更新頁；IG 科技債利差與非公開 BDC 均無每日公開頁（無新進展）
- 事實（三項指標逐一實測結果）：
  1. **投資級科技公司債利差**：**沒有**免費、每天更新的公開資料頁。FRED 免費提供的 ICE BofA 公司債選擇權調整利差（OAS）僅涵蓋美國整體投資級主指數（`BAMLC0A0CM`，https://fred.stlouisfed.org/series/BAMLC0A0CM ）及各信評分層（`BAMLC0A1CAAA` 至 `BAMLC0A4CBBB`），**未公開發布「科技產業（Information Technology）」子指數**；ICE BofA US Technology Corporate Index OAS 屬 ICE Data Services 付費商業指數。
  2. **甲骨文（ORCL）等公司債價格與殖利率**：**有免費、每日更新的公開資料頁**：
     - Markets Insider 個別公司債報價頁每日更新價格與殖利率，例如甲骨文 2030 年到期 2.95% 債券（ISIN `US68389XBV64`）11/19 報價 **86.86 美元（+0.20%）**，同一頁面並列出 2034–2044 年到期多檔甲骨文長債每日殖利率（約 **8.21%–8.61%**）：https://markets.businessinsider.com/bonds/oracle_corpdl-notes_202020-30-bond-2030-us68389xbv64 （HTTP 200 實測）。
     - 美國金融業監管局 FINRA Fixed Income Data / TRACE 官方入口（可依發行人或 CUSIP 查詢場外公司債每日實際成交價格與殖利率）：https://www.finra.org/finra-data/fixed-income （HTTP 200 實測）。
  3. **非公開交易 BDC 的贖回限制／按比例配發（Gating / Proration）**：**沒有**每日更新的公開資料頁。Blackstone Private Credit Fund（BCRED，CIK `0001803498`）與 Blue Owl（OCIC）等非公開 BDC 屬**按季**辦理要約買回，僅於每季結束後在 SEC EDGAR 申報 `Schedule TO-I` 與 `Form 8-K`；第三方公開整理如 CrowdfundedWealth 追蹤頁面顯示 BCRED 於 Q2 2026 僅滿足 **48.5%** 贖回申請、Q3 滿足 **49.9%**（https://www.crowdfundedwealth.com/articles/blackstone-private-credit-fund-bcred-redemptions-2026 ，HTTP 200 實測）。

### D-3｜回應 Q3：找齊 Claude 第 3 點推理的歷史反例——升息循環中「消費強＋利差收窄＋成長股上漲」確實發生過（2017、2004–2006、1999）（無新進展）
- 事實（歷史升息循環的反例實證）：
  1. **2017 年升息循環（最貼近的反例）**：聯準會於 2017 年升息 3 次各 1 碼並啟動縮表，當時美國失業率走低、實質薪資與消費支出穩健擴張，高收益債利差（`BAMLH0A0HYM2`）全年並未擴大，反而壓縮至 **3.4%–3.5%** 歷史低檔區間（https://www.federalreserve.gov/monetarypolicy/fomcpresconf20171213.htm ），同時**那斯達克綜合指數 2017 全年大漲 28.24%**。
  2. **2004–2006 年升息循環（信用利差反例，但那指漲幅溫和）**：聯準會自 2004 年 6 月至 2006 年 6 月連續 17 次升息，利率由 **1.00% 升至 5.25%**；受惠全球流動性與強勁消費／房市景氣，高收益債利差（`BAMLH0A0HYM2`）反而一路收窄至 300 基點以下低檔（https://www.newyorkfed.org/medialibrary/media/research/epr/07v13n1/0703klee.pdf ），惟當時剛走出網路泡沫的科技股僅溫和上行，並未出現爆發性重估。
  3. **1999–2000 年升息循環（成長股暴漲，但信用利差並未一路收窄）**：聯準會自 1999 年 6 月至 2000 年 5 月將基準利率由 **4.75% 升至 6.50%**，美國消費靠財富效應維持強勁，那斯達克 1999 全年飆升 **85.6%**；然而高收益債利差在 1999 年中後段其實隨投機債發行過剩而波動走寬（https://www.imf.org/external/pubs/ft/weo/2000/01/index.htm ）。
- 推理（反例對 Claude 本輪結論的真正意義）：
  - **2017 年證明了你第 3 條鏈結並非絕對成立**：當消費強代表「名目營收與償債能力同步變強」而非純粹通膨失控時，強消費反而壓低違約預期、讓利差維持低檔並支撐成長股。
  - **但 2026 年 11 月和 2017 年有一個關鍵結構差異**：2017 年 10 年期美債殖利率僅約 2.3%–2.4%，企業舉債成本遠低於現在的 **5.10%**；且 2017 年大型科技股（FAANG）是靠高自由現金流自給自足，而 2026 年多家雲端巨頭自由現金流已轉負。因此**2017 年的反例提醒我們不要把「消費強＝信用市場一定惡化」當成鐵律，但對「高負債算力廠」而言，5% 以上無風險利率仍限制了估值容錯空間**。

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

### D-5｜對 Claude 第 4 輪六條主線的逐一表態（補充 23:45 新外部資訊）
- 推理：
  1. **主線 1（AI 的錢：市場開始按現金流分好壞）— 同意且新證據顯示監管與內部人同時把焦點鎖定「AI／私募信貸鏈」**：除昨日 WSJ 揭露華爾街 5,000 億美元輝達融資備忘錄**實際撥款仍為 0 美元**外（https://www.tradingview.com/news/gurufocus:d68ae5e48094b:0-michael-burry-sounds-alarm-on-nvidia-s-500-billion-wall-street-financing-plan/ ），今日歐洲央行（ECB）發布 2026 年監理審查（SREP）與 2027–2029 年監理優先事項，也正式點名將對歐元區銀行**私募信貸基金融資、非銀行金融機構（NBFI）及資料中心曝險**啟動專案實地檢查（https://live.euronext.com/en/financial-news/nearly-all-euro-zone-banks-are-struggling-tech-risks-ecb-says ）；同時 CoreWeave 策略長 Brian Venturo 不得不親自購入 3,000 萬美元自家無擔保債券穩信心，而 **NBIS（-1.80%）與 IREN（-1.25%）開盤漲幅一小時內全數吐回翻黑**，進一步印證市場對重資產負債算力廠的耐心極為脆弱。
  2. **主線 2（輝達治理＋出口管制）— 部分同意，今日 BIS 衝擊已實質外溢到台積電與三星出貨，且最高法院今日定讞東京威力洩密案**（https://udn.com/news/story/6811/9889722 ；https://money.udn.com/money/story/5612/9889323 ）。
  3. **主線 3（利率是主壓力）— 同意，歐美日監管與貨幣緊縮持續共振**：10 年期美債殖利率升至 **5.10%（+2.9 bp）**，ECB 下週 11/25 擬辯論把銀行最低準備金率倍增至 2%（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ），南非央行 4 比 3 鷹派分歧，日銀 12 月升息預期升溫。
  4. **主線 4（10 月核心 PCE 區間機率降至 30%）— 完全同意，雙方已對齊 30%**。
  5. **主線 5（油價 WTI 80–100 美元：Claude 58% vs 我 55%）— 部分同意，差距維持 3 個百分點**。
  6. **主線 6（Anthropic 掛牌受影響順序＋1.2375 億股穩價額度）— 同意你補上的穩價額度風險**：截至 23:43 ANT 仍處開盤集合競價搓合中，而那指 100 已先行由 +1.88% 翻黑至 -0.13%，須緊盯首筆開盤價開出後能否守住漲勢。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題
- 1. 《金融時報》與《聯合報》11/19 揭露「BIS 新規取消『非 AI 用途』豁免後，台積電與三星已通知中國客戶（含小米、OPPO、vivo 等手機晶片）暫停出貨部分先進製程晶片並等待許可證」。目前本站 `dots_read.json` 的假設仍主要把 BIS 11/16 新規框在「堵第三國遠端算力與輝達中國業務」，請問下一輪是否應在供應鏈追蹤裡把「非 AI 中國手機／消費電子先進製程暫停出貨」獨立拉成一條風險分支？
- 2. 今日美媒再揭「華爾街六大機構 8 月對輝達客戶承諾的 **5,000 億美元晶片融資計畫實際撥款至今為 0**，卡在輝達僅願承擔 25% 信用擔保、貸款方要求更強風險分攤」，加上今日 **ECB 2026 SREP 宣布 2027–2029 年啟動銀行對私募信貸與資料中心融資實地檢查**。本站 `forecast.json`「風險升級」正追蹤「新雲端融資成本升高」，這兩項銀行端與表外信貸收緊訊號是否應納入下輪主線 1 的主要證據？
- 3. 我們剛在 23:31 實測線上 `#econ`《IPO 觀察》仍印著「`台股已公告 4 家即將掛牌（宏偉 11-19、耐特 11-19…）`」——但實際上 **宏偉（4565）與耐特（8058）已於 11/09–11/10 因競拍合格投標量不足宣布不開標並取消本次承銷作業**（且 11/19 台股已收盤），請問 `site_ipo.py` 抓取台股即將掛牌清單時，是否沒有過濾「競拍流標／取消開標」或「已逾掛牌日」的狀態？

---

### WIDE-1｜荷莫茲海峽東側油輪觸水雷＋IEA 警告 400 億美元繞道管線脆弱＋胡塞碎片擊中沙國 PIF 總部（無新進展）
- 事實：11/19 伊朗與中東媒體報稱荷莫茲海峽東側接連傳出油輪疑觸水雷受損（另有阿聯 ADNOC 關聯油輪遇襲致船員受傷失蹤）；同日 IEA 於《2026 世界能源展望》警告海峽衝突已累計中斷 **28 億桶原油與 600 億立方公尺天然氣**，就算波灣產油國斥資 **400 億美元**興建替代輸油管線，仍高度暴露於飛彈與無人機襲擊風險中（https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ）；同日下午胡塞飛彈攔截碎片損及利雅德沙國主權基金（PIF）80 層總部大樓（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ）。
- 推理：美股盤前停在 EIA 累庫帶來的油價小跌，忽視了「航道水雷化」與「陸路繞道管線同樣脆弱」對遠月原油曲線與海運戰爭險保費的結構性風險。
- 先影響資產：布蘭特原油遠月價差、油輪運價與戰爭險保費、波灣主權債 CDS。

### WIDE-2｜ECB 2026 SREP 揭露 96% 歐元區大銀行 IT／資安風險評等不佳並鎖定私募信貸實地檢查＋11/25 擬辯論準備金率倍增；英國央行聯合發布 AI 與量子資安諮詢（更新今日監管報告）
- 事實：歐洲央行（ECB）11/19 公布 **2026 年監理審查（SREP）結果**，雖然歐元區銀行 2027 年平均 CET1 資本要求維持 **11.3%**（ROE 近 11%），但指出 **近 96% 的大型受監理銀行在營運與 IT／資安風險管理僅獲得普通或不佳評等**，並已向 78 家銀行開出質化改善要求；ECB 同步宣布 2027–2029 年監理重點將啟動針對**私募信貸基金融資、資產抵押放款與非銀行金融機構（NBFI）曝險的專案實地檢查**（https://live.euronext.com/en/financial-news/nearly-all-euro-zone-banks-are-struggling-tech-risks-ecb-says ）。同日（無新進展）路透指 ECB 管委會將於 **11/25** 辯論把最低存款準備金率從 1% 倍增至 2%（回收約 1,750 億歐元，https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ），德國央行警告 2027 年初通膨急升（https://www.newsquawk.com/headlines/bundesbank-monthly-report-expects-relatively-strong-german-economic-growth-in-q4-but-warns-inflation-will-rise-sharply-at-the-beginning-of-2027 ）。同日**英國央行（BoE）、審慎監理局（PRA）與金融行為監理總署（FCA）**聯合發布網路韌性諮詢文件（PRA CP17/26／FCA GC26/9）及 **AI 與量子運算加密風險**實務指引，指出 2026 年 10 月向 FCA 通報的資安事件創五年來次高單月紀錄（較 2025 年 5 月高點大增 **52%**，https://www.bankofengland.co.uk/news/2026/november/cyber-resilience-guidance-consultation-and-ai-and-quantum-effective-practices ）。
- 推理：美股緊盯 Fed 12/9 升息與企業財報，卻忽略歐洲與英國監理機構同一天把「銀行 IT 脆弱度＋AI 資安＋私募信貸表外曝險」同步列為 2027–2029 年最高檢查優先級，加上 ECB 11/25 準備金率討論，將收緊歐系銀行對美國新雲端與私募信貸的授信額度。
- 先影響資產：歐元區銀行股（SX7E）、私募信貸基金與商業放款 BDC、歐系資安股、EUR/USD。

### WIDE-3｜挪威國營能源巨頭 Equinor 證實遭持續性網攻＋歐盟妥協延後油氣煤進口商甲烷申報規定 2 年（無新進展）
- 事實：挪威國營油氣巨頭 **Equinor** 證實自 11/17 起偵測到企業 IT 與內部郵件系統遭持續性網路攻擊並通報挪威國家安全局（NSM），目前油氣產出與出口未中斷但全面復原無時間表（https://therecord.media/norway-equinor-cyberattack-energy ，台北時間 2026-11-19）；歐洲議會與理事會談判代表同日達成臨時協議，將原油／天然氣／煤炭進口商**甲烷監測與申報規範（MRV）延後兩年至 2029 年 1 月 1 日**、甲烷強度申報延至 **2030 年 8 月 5 日**，以降低中東戰事下的能源供應斷鏈風險（https://europeansting.com/2026/11/19/methane-deal-to-delay-reporting-and-monitoring-for-energy-importers/ ，台北時間 2026-11-19）。
- 推理：歐洲能源安全脆弱度逼使布魯塞爾在減碳合規上讓步，短期有利 LNG 供應穩定，但關鍵能源商 IT 遭駭凸顯基礎設施網路風險升溫。
- 先影響資產：歐洲天然氣期貨（TTF）、挪威克朗（NOK）、歐系資安與能源基礎設施類股。

### WIDE-4｜銅價重挫至 4 月以來新低（錫價單日急殺 8%）衝擊智利／秘魯礦業預期；南非央行 4 比 3 鷹派分歧＋巴西財政緊縮案（補充工業金屬急殺）
- 事實：受強美元、美國升息預期、中國 10 月工業生產與零售數據遜於預期，以及宏觀投資人 Stan Druckenmiller 轉為看空 AI 銅需求交易影響，**倫敦金屬交易所（LME）三個月期銅急挫至 4 月以來新低（盤中一度跌 4% 至每公噸 12,727.50 美元）、AI 焊料關鍵金屬錫價單日重挫高達 8%**（https://www.tradingview.com/news/seekingalpha:cb0deccc9094b:0-copper-extends-slide-to-lowest-level-since-april-on-firm-dollar-ai-doubts/ ）。另方面，南非央行（SARB）11/19 以 **4 票維持、3 票主張升息 1 碼**驚險維持基準利率 **7.25%**（https://www.moneyweb.co.za/news/economy/sarb-holds-rates-steady/ ）；巴西參院通過 500–600 億雷亞爾緊縮案（PLP 299/2026），並被美 BIS 11/19 生效之遠端算力新規列入高轉運風險國（https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors ）。
- 推理：銅與錫同時回吐代表「AI 電網／資料中心＋關稅囤貨」的商品多頭正在去槓桿，即便智利／秘魯礦山供給吃緊與精煉銅加工費（TC/RC）為負，金融面去槓桿仍先壓抑南美資源國貨幣與工業金屬類股。
- 先影響資產：LME 銅／錫期貨、智利披索（USD/CLP）、秘魯／南非礦業股（FCX、SCCO、BHP）、USD/ZAR。

### WIDE-5｜APEC 深圳美中俄三方《和平宣言》與「30 對 30 關稅協議」＋日銀 12 月升息預期＋印度 CPI 破 6% 與氣旋「阿克萬」明日登陸（無新進展）
- 事實：11/19 美中於深圳達成各自削減 300 億美元商品關稅的「30 對 30 協議」（https://www.cna.com.tw/news/aopl/202611193005.aspx ），白宮官網公布美中俄三方元首《和平宣言》（https://www.whitehouse.gov/briefings-statements/2026/11/u-s-russia-china-heads-of-state-declaration-toward-peace/ ），三國並計畫增加精煉石油產品供應（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ）。日本央行總裁植田和男 11/19 在國會警示日圓偏弱與油價恐推升潛在通膨破 2%，強化 12 月升息至 **1.50%** 預期；熊本清晨 M5.7 餘震暫無 JASM 重大停工回報（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ）。印度 10 月 CPI 升至 **6.09%** 突破央行上限，強氣旋「阿克萬」將於 11/20 中午登陸奧里薩邦（已撤離逾 10 萬人，https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ；https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ）。
- 推理：深圳高峰會僅緩和傳統貨貿摩擦與成品油供給，未觸及美中晶片與稀土核心管制；反而是日銀 12 月升息與印度通膨／天災正收緊亞洲流動性。
- 先影響資產：USD/JPY、USD/CNH、INDA、USD/INR、日本銀行與工業股。

---

### A｜今天的大動（依 `https://wallstreet-sentinel.pages.dev/api/gemini_ask` 台北 2026-11-19 23:32 即時 12 檔題目清單逐題回答；23:43 補充盤中最新報價）

### PDD｜拼多多（PDD）今天 +10.3%（23:43 漲至 +11.0%）：Q3 2026 縮減行銷費用 16.6% 帶動 Non-GAAP EPADS 人民幣 21.04 元大勝共識
- 事實：拼多多於美東 11/19 06:30（台北 19:30）公布 Q3 2026 財報，總營收人民幣 **1,083.4 億元**（年對年持平，遜於市場共識約 1,152 億～1,162 億元），主因交易服務營收年減 12% 至 485.2 億元（線上行銷服務營收則年增 12% 至 598.2 億元）；但銷售與行銷支出年減 **16.6%** 至 **253 億元**，推動營業利益年增 **24.8%** 至 **311.6 億元**、Non-GAAP 淨利 **310 億元**、**Non-GAAP 稀釋每 ADS 盈餘人民幣 21.04 元（3.14 美元）**大幅勝過共識 2.61–2.77 美元，截至 23:43 盤中續漲至 $85.99（+11.0%）（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，且 23:31 線上《美股財報日曆》仍將 PDD 列為「即將公布」。

### STX｜希捷科技（Seagate Technology，STX）今天 +6.1%（23:43 報 +4.9%）：與 WDC、MU 同受 Anthropic 創紀錄 IPO 帶動儲存與記憶體族群反彈（無新進展）
- 事實：11/19 STX 未見單獨公司公告（找不到獨立公司來源），隨 SNDK、WDC、MU 等 AI 資料中心儲存與記憶體板塊受 Anthropic 今日以 83 美元掛牌與早盤晶片情緒回溫同步反彈（https://247wallst.com/investing/2026/11/19/sandisk-and-micron-rise-4-as-anthropics-record-ipo-revives-the-ai-trade-western-digital-gains-5/ ；https://news.cnyes.com/news/id/6667734 ，台北時間 2026-11-19）。
- 本站漏掉的：屬 AI 儲存與記憶體族群集體反彈，非 STX 個別新消息。

### WDC｜威騰電子（Western Digital，WDC）今天 +5.8%（23:43 報 +4.9%）：與 STX、MU、SNDK 同步受 Anthropic IPO 提振反彈（無新進展）
- 同意本站（24/7 Wall St. 11/19 09:11 ET 報導已涵蓋 Anthropic IPO 帶動儲存股反彈，https://247wallst.com/investing/2026/11/19/sandisk-and-micron-rise-4-as-anthropics-record-ipo-revives-the-ai-trade-western-digital-gains-5/ ，台北時間 2026-11-19）。
- 本站漏掉的：與 STX、SNDK 屬同一儲存板塊集體反彈，11/19 無 WDC 個別新公司公告。

### CRWD｜CrowdStrike（CRWD）今天 +5.4%（23:43 報 +5.8%）：受同業 PANW Q1 FY27 財報優於預期並斥資 45 億美元併購 Applied Compute 外溢帶動（無新進展）
- 事實：CRWD 預計 **12 月 1 日盤後**才公布 Q3 FY27 財報，11/19 本身無單獨公司公告或新評等調整（找不到來源）；上漲主因同業 PANW 美東 11/18 盤後公布營收年增 39% 至 34.4 億美元（Non-GAAP EPS $1.05）並宣布 45 億美元併購 Applied Compute，帶動 CRWD 與 FTNT 等資安股同步走強（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ；https://www.tradingview.com/news/zacks:3d366f393094b:0-cybersecurity-stocks-gain-on-ai-boom-but-are-valuations-too-high/ ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，屬資安族群財報外溢效應。

### INTC｜英特爾（Intel，INTC）今天 +4.4%（23:43 報 +3.1%）：同意本站，Austin 峰會揭露 18A-P 首位外部客戶與微軟採用 EMIB＋川普談 Blackwell 輸陸可能性（無新進展）
- 同意本站（24/7 Wall St. 11/19 報導已涵蓋 18A 首位外部客戶進展及川普深圳談話，https://247wallst.com/investing/2026/11/19/intel-climbs-7-on-first-18a-customer-nvidia-gains-4-as-trump-floats-blackwell-sales-to-china-and-dan-ives-hails-anthropic-ipo-amd-rises-3/ ，台北時間 2026-11-19）。
- 本站漏掉的：英特爾另在 Austin 峰會與微軟宣布 EMIB 先進封裝合作進展，惟開盤大漲後隨 `^NDX` 翻黑（23:43 轉為 -0.13%）收斂至 +3.1%。

### UNH｜聯合健康（UnitedHealth，UNH）今天 -4.2%（23:43 報 -4.6%）：消化 CMS「CRUSH」追溯至 2018 年的 Medicare Advantage 稽核草案與政治拆分呼聲之延續賣壓
- 事實：11/19 本身未見 UNH 單獨新財報或監管突發公告（找不到 11/19 新公告），但管理醫療保險板塊本週持續承壓於美國聯邦醫療保險與補助服務中心（**CMS**）於 **11/16** 發布之 **《CRUSH》（CMS-6098-P）擬議規則**：該草案擬透過樣本外推（extrapolation）且不設 FFS 調整因子，將 Medicare Advantage（RADV）溢付款項追討**回溯至 2018 給付年度**，CMS 估計未來十年（2027–2036）可追回近 **900 億美元**（每年約 90 億美元），公眾意見徵詢至 2027/01/19（https://www.cms.gov/newsroom/press-releases/cms-crush-proposed-rule-aims-reap-nearly-90-billion-taxpayers-savings-targeting-fraud-across ；https://www.tradingview.com/news/gurufocus:46c8103be094b:0-unitedhealth-shares-sink-as-new-federal-fraud-crackdown-sparks-healthcare-sell-off/ ，台北時間 2026-11-19）。另本週參議員 Elizabeth Warren 亦推動拆解垂直整合醫療巨頭的立法訴求（https://247wallst.com/investing/etf/2026/11/17/your-safe-health-care-etf-just-got-hit-by-unitedhealth-again/ ）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。時間軸核對：CMS CRUSH 草案發布於 11/16–17，UNH 本週連續下挫屬該重大監管衝擊的延續定價，而非今日才出現的新事件。

### PM｜菲利普莫里斯（Philip Morris，PM）今天 -3.9%（23:43 報 -4.0%）：今日未見單獨公司利空公告，屬必需消費防禦高估值股獲利了結與對前期 Zyn 加量不加價壓縮 Q4 美國利潤率之消化
- 事實：經查證 **11/19 當日未見 Philip Morris 單獨新公司公告、財報或華爾街券商調降評等報告（找不到 11/19 單日觸發來源）**。時間軸核對：市場近期對 PM 美國市場獲利壓力的討論，原始出處來自 **10/21 Q3 2026 法說會**——公司為防禦競爭對手（如 Velo），將美國主力 Zyn 尼古丁袋每罐由 **15 袋免費增至 20 袋（相當於單袋變相降價約 25%）**，並預告 Q4 美國市場營業利益將因促銷與擴產投資接近零或小幅負值（https://www.fool.com/earnings/takeaways/2026/10/21/philip-morris-3-key-takeaways-for-long-term-investors/ ，台北時間 2026-10-22）。
- 推理（不確定）：消息發生在一個月前而非今日，PM 11/19 在無單獨利空公告下逆勢重挫 -4.0%，在 10 年期美債殖利率升至 5.10% 下較符合高倍數防禦型消費股獲利了結與資金輪動，確切觸發原因標註「**不確定**」。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### PANW｜Palo Alto Networks（PANW）今天 +3.7%（23:43 報 +3.5%）：Q1 FY27 營收年增 39% 優於預期＋上調全年財測＋45 億美元併購 Applied Compute＋多家券商調高看法（無新進展）
- 事實：PANW 美東 11/18 盤後公布 Q1 FY27 營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億）、Non-GAAP EPS **1.05 美元**（優於預期 0.97 美元）、NGS ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**，並宣布以 **45 億美元**收購 **Applied Compute**（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19）；今日美東盤前 Baird、Goldman Sachs、KeyBanc、Piper Sandler 等多家券商同步調高價格看法（https://tw.tradingview.com/news/tradingview:2f38ae38a6f7e:0/ ）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### FTNT｜飛塔（Fortinet，FTNT）今天 +3.6%（23:43 報 +4.2%）：隨同業 PANW 財報與 AI 資安併購帶動網安類股集體走強
- 事實：11/19 FTNT 未見單獨公司新聞稿或券商評等調整（找不到獨立來源）；與 CRWD 同步受惠同業 **PANW** 昨晚公布 Q1 FY27 營收大增 39%、上調全年指引並砸 45 億美元併購 AI 模型安全廠 **Applied Compute**，帶動企業 AI 資安預算樂觀情緒外溢至網安族群（https://www.tradingview.com/news/zacks:3d366f393094b:0-cybersecurity-stocks-gain-on-ai-boom-but-are-valuations-too-high/ ；https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，屬同業財報帶動之資安類股齊漲。

### NKE｜耐吉（Nike，NKE）今天 -3.5%（23:43 報 -4.5%）：11/17 投資人日預告「FY29 前營收難重返成長」餘波未歇，今日多家華爾街分析師重申保守評等
- 事實：耐吉（Nike）於 **11/17** 投資人日發表《Full Stride Ahead》策略與 FY2031 長期架構，雖預期 FY31 調整後 EPS 達 **$3.00–$3.50**、營益率擴至 **12%–14%**，但重申 FY27 營收將呈現高個位數衰退、調整後 EPS 僅 **$1.15–$1.35**，且坦言**直到 FY2029 才會恢復市場水準的營收成長**（https://investors.nike.com/news-events/press-releases/detail/578/nike-inc-announces-full-stride-ahead-strategy-and-2031-financial-framework-at-investor-day ，台北時間 2026-11-18）。時間軸核對：投資人日召開於兩天前（11/17），**11/19 今日股價續挫至 $34.67（-4.5%）**，伴隨華爾街報告消化——**KeyBanc** 維持 `Sector Weight`、**Truist** 維持 `Sell` 與看法 **$29.00**、**Telsey Advisory Group** 維持 `Market Perform` 與看法 **$35.00**，Motley Fool 今日晨間亦專文點出 2029 年前無營收成長的漫長復甦等待期（https://www.fool.com/investing/2026/11/19/nike-s-2031-targets-look-great-on-paper-but-sales-won-t-grow-until-2029-here-s-the-price-i-d-pay/ ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### ACN｜埃森哲（Accenture，ACN）今天 -3.4%（23:43 報 -2.8%）：今日宣布因 Meta 轉向 AI 效率而在葡萄牙裁撤約 950 名外包審核人力，抵銷 BofA 恢復追蹤 Buy 評等
- 事實：路透／CNA 於 **11/19** 報導，埃森哲（Accenture）宣布向里斯本團隊啟動自願離職方案，預計明年 1 月前裁減約 **950 個職位（佔葡萄牙員工總數約 16%）**，主因大客戶 **Meta Platforms** 推動 AI 驅動效率整頓導致 Trust & Safety 內容審核外包需求大幅變動（https://www.channelnewsasia.com/business/accenture-launches-plan-cut-950-meta-linked-jobs-in-portugal-6565761 ，台北時間 2026-11-19）。同日 **BofA Securities** 恢復追蹤 ACN 給予 `Buy` 評等與價格看法 **$288.00**（搜尋摘要，Investing.com 原文頁面擋爬蟲返回 403，轉引需留意），惟股價昨日已先跌 4.9% 至 $227.49、今日續跌約 2.8% 至 $221.19，反映市場對「AI 取代傳統人工外包與企業 IT 諮詢預算放緩」的擔憂蓋過券商看多報告。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### UBER｜優步（Uber，UBER）今天 -3.3%（23:43 報 -2.8%）：11/19 未見單獨公司新利空公告，屬本週 Zoox 上線後「自駕車隊商業化規模與資本開支」多空拉鋸延續（不確定）
- 事實：經查證 **11/19 當日未見 Uber 單獨公司利空公告或券商調降評等報告（找不到 11/19 新觸發來源）**。時間軸核對：亞馬遜旗下 Zoox 無人計程車已於 **11/16** 在拉斯維加斯透過 Uber App 正式上線（初期車隊規模有限），當時 11/17 UBER 股價即已收跌 -2.87% 至 $67.98（https://www.tradingview.com/news/gurufocus:877ed9690094b:0-uber-stocks-fall-2-87-even-as-zoox-robotaxis-go-live-on-its-vegas-app/ ，台北時間 2026-11-18）；本週 11/19 另有 Kohl's 與 Uber Eats 節慶配送合作等例行業務消息，無重大新負面事件。
- 推理（不確定）：11/19 續跌約 2.8% 至 $66.83 與近幾日圍繞自駕車合作車隊規模有限及重資產投資討論延續時間重疊，無單日突發利空可證實，主因標註「**不確定**」。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

---

### AN-1｜過去 3 小時（20:45–23:45 台北／美東 07:45–10:45）AI 供應鏈與前 20 大未見新增人工券商調評；Seeking Alpha 量化評等將 NVDA 調為 Hold；清單外見 ACN 與 NKE 報告
- 事實（過去 3 小時）：
  - **AI 供應鏈與美國市值前 20 大**：截至台北 23:45，未見華爾街投行分析師對該清單發布新的正式評等調整報告（找不到投行分析師來源）。僅自動化量化模型 **Seeking Alpha Quant Rating** 今日（11/19）將 **NVDA** 評等由 `Strong Buy` 下調至 `Hold`（量化總分由 4.92 降至 3.48，主因股價動能分項由 `C-` 降至 `D+`，成長與獲利分項仍維持 `A+`；屬量化系統自動評分，非投行分析師報告）。
  - **名單外同日重要券商報告（11/19）**：**BofA Securities** 恢復追蹤 **ACN** 給予 `Buy` 評等、價格看法 **$288**；**KeyBanc** 維持 **NKE** `Sector Weight`、**Truist** 維持 `Sell` 看法 **$29**、**Telsey Advisory Group** 維持 `Market Perform` 看法 **$35**。
- 事實（今日稍早 PANW 報告與近期已核對清單，無新進展）：
  - **PANW（美東 11/19 盤前）**：**Baird** 維持 `Outperform` 看法 $420→**$465**（https://tw.tradingview.com/news/tradingview:2f38ae38a6f7e:0/ ）；**Goldman Sachs** `Buy` $390→**$440**；**KeyBanc** `Overweight` $380→**$450**；**Piper Sandler** `Buy` $410→**$450**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ）。
  - **AVGO**：Goldman Sachs（11/19）`Buy` 看法 $540→**$460**（https://www.tokenpost.com/news/business/61151 ）；Rothschild & Co Redburn（11/13）`Buy`→`Neutral` 看法 $595→**$398**（https://fr.tradingview.com/news/seekingalpha:f4cc47e04094b:0-broadcom-in-focus-as-rothschild-downgrades-to-neutral-but-flags-potential-upside/ ）。
  - **MRVL**：BofA `Buy`→`Neutral`（$400→$225）；TD Cowen `Buy`→`Hold`（$350→$175）（https://finance.biggo.com/news/11363615-75b3-4fde-a7f6-069c21673c8c ）。
  - **HCA（11/18）**：JPMorgan `Neutral` 看法 $425→**$475**（https://www.tradingview.com/news/tradingview:9eb3a7caf755c:0-jp-morgan-maintains-hca-healthcare-at-neutral-raises-price-target-to-475-from-425/ ）。
  - **TSM／2330（11/19）**：Morgan Stanley 維持 `Overweight` 看法 **3,088 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ）。
  - **NVDA（日前）**：HSBC `Hold`（$365→$170，https://www.tradingview.com/news/binance_news:d94dcaa1f094b:0-hsbc-downgrades-nvidia-says-stock-may-struggle-until-new-ceo-is-named/ ）；Evercore ISI `Outperform`→`In-Line` $186、Baird `Outperform`→`Neutral`（https://www.tradingview.com/news/benzinga:3bce7f47b094b:0-nvidia-gets-10-bank-downgrades-after-huang-exit-what-to-expect-ahead-of-q3-results/ ）。

---

### POL-1｜BIS 遠端算力新規（`2026-23529`）今日生效；《金融時報》揭露新規取消「非 AI 用途」豁免致台積電、三星暫停部分中國晶片出貨（無新進展）
- 事實：美國商務部 BIS 暫行最終規則（聯邦公報 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）今日（美東 **2026-11-19**）正式刊登聯邦公報並立即生效（意見徵詢至 2027-01-19），增訂 § 744.24 限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，廢止前政府 AI 擴散規則，並由財政部與國安會（NSC）主導及指示撰寫（https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors ；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ）。
- 事實：《聯合報》與《自由財經》11/19 引述英國《金融時報》報導指出，BIS 11/16 發布之出口管制新規封堵中國晶片設計商透過 OSAT（委外封測）繞道下單漏洞，並**取消「證明晶片屬智慧手機等非 AI 用途即可豁免」條款**，致使**台積電與三星電子已通知中國客戶在向美國商務部申請許可證期間暫停出貨特定處理器**，連小米、OPPO、vivo 等中國手機品牌先進製程晶片亦須申請許可並面臨交期延宕風險（https://udn.com/news/story/6811/9889722 ；https://ec.ltn.com.tw/article/breakingnews/5646861 ，台北時間 2026-11-19）。

### POL-2｜白宮發布美中俄三方《和平宣言》；美國財政部 FinCEN 提案、9 月 TIC 淨流入 2,610 億美元、OFAC 制裁與 USTR 談話（無新進展）
- 事實：白宮 11/19 發布川普、普丁與習近平深圳會晤聯合宣言《U.S.-Russia-China Heads of State Declaration toward Peace》（https://www.whitehouse.gov/briefings-statements/2026/11/u-s-russia-china-heads-of-state-declaration-toward-peace/ ）；財政部 FinCEN 發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，https://home.treasury.gov/news/press-releases/sb0691 ）；9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ）；OFAC 制裁真主黨與聖城軍金流（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 大使 Greer 11/18 於 RBA 年會重申美國優先貿易（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）。

---

### TW-1｜台積電與三星電子傳暫停出貨部分中國晶片（波及手機品牌）；11/19 收跌 1,768 點、1.29 億違約交割與限空令 2.0（無新進展）
- 事實：《聯合報》與《自由財經》11/19 引述《金融時報》報導，因應美國 BIS 新規堵住 OSAT 封測繞道並取消智慧型手機「非 AI 用途」豁免，**台積電與三星電子已通知中國大陸客戶暫停出貨部分先進製程處理器並等待美方許可證**，影響範圍擴及小米、OPPO、vivo 等中國手機廠與中資 AI 晶片業者（https://udn.com/news/story/6811/9889722 ；https://ec.ltn.com.tw/article/breakingnews/5646861 ，台北時間 2026-11-19）。台指期夜盤反彈逾 **800 點**攻防 39,000 點。
- 事實（11/19 台股正規盤收盤、三大法人與違約交割，無新進展）：加權指數收 **38,426.89 點（-1,768.02 點 / -4.40%，失守年線 39,368 點）**，成交值 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ）；櫃買收跌 **-7.22% 至 285.33 點**。權值股收盤：**台積電 2,100 元（-3.45%）**、**聯發科 3,720 元（-5.58%）**、**鴻海 220.5 元（-0.23%）**、**日月光投控 504 元（-8.03%）**、**緯穎 1,410 元（跌逾 4%）**（https://www.moneyweekly.com.tw/ArticleData/Info/Article/212266 ）。三大法人合計賣超 **461.03 億元**（**外資 -243.12 億、投信 +15.13 億、自營商 -233.03 億**，https://www.cna.com.tw/news/afe/202611190200.aspx ）；外資台指期淨空單 **-99,219 口**。盤後通報 **1.29 億元**違約交割：上市**台化（1326）4,172.8 萬元**，上櫃**世界先進（5347）與萬泰科（6190）**（https://stock.ltn.com.tw/article/m7hjf9c9axqq ）。
- 事實（金管會 11/20 限空令 2.0，無新進展）：今日收盤跌幅 ≥3.5% 之上市櫃與 TDR（共 **1,028 檔**）11/20 禁止平盤下融券及借券放空，盤中借券放空委託上限由前 30 日均量 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；新台幣 16:00 收 **32.942 元（升 0.5 分）**（https://www.cna.com.tw/news/afe/202611190296.aspx ）。

### TW-2｜台積電 2 奈米洩密案東京威力主管湮滅證據判緩刑 3 年今日定讞；張曉強固鏈與 5 億美元入股 Anthropic（補充最高法院定讞）
- 事實（新增今日司法定讞）：最高法院 11/19 駁回上訴，台積電 2 奈米／14 埃米核心營業秘密外洩案中，涉嫌刪除翻拍圖檔湮滅證據的**台灣東京威力科創行銷主管盧怡尹**判刑 10 月、緩刑 3 年（支付公庫 100 萬元）**全案定讞**（主謀陳力銘先前已判 10 年、東京威力法人罰金 1.5 億元緩刑 3 年並須賠台積電 1 億元確定，https://money.udn.com/money/story/5612/9889323 ，台北時間 2026-11-19）。
- 事實（無新進展）：台積電資深副總張曉強親赴輝達總部穩固長期產能與擴產承諾，Vera Rubin NVL72 與 Vera CPU 已於 Q3 進入量產出貨；台積電並正式公告透過 TSMC Partners 以 **每股 83 美元**取得 Anthropic 普通股 **6,024,096 股**（約 **5 億美元**，https://www.cna.com.tw/news/afe/202611190254.aspx ）。日月光旗下福雷電子高雄仁武新廠動土投資 **2,489 億元**（https://www.cna.com.tw/news/afe/202611190122.aspx ）；廣達田納西廠租約 1,490.8 萬美元（https://news.cnyes.com/news/id/6666244 ）；海龍 2A 綠電轉售台積電（https://www.cna.com.tw/news/afe/202611190102.aspx ）；鴻海 72.4 億日圓收購 Sony 車載相機事業（https://www.ctee.com.tw/news/20261119700316-439901 ）。
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

### FED-3｜理事 Barr（偏升息）、紐約聯準總裁 Williams（反對一次升 2 碼）；稍後 Goolsbee、Barkin 談話與貼現率閉門會議（無新進展）
- 事實：Barr 11/18 演說指通膨仍過高、適合進一步升息（https://www.federalreserve.gov/newsevents/speech/barr20261118a.htm ）；Williams 反對一次大幅升息 2 碼（https://www.aa.com.tr/en/economy/fed-governor-favors-half-point-rate-hike-in-december-unless-fed-signals-january-increase/4129382 ）。Goolsbee 將於 **美東 11/19 12:30（台北 11/20 01:30）**於印第安納經濟俱樂部座談（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）；Barkin 將於 **美東 11/19 15:00（台北 11/20 04:00）**經濟座談；聯準會理事會同時間召開閉門貼現率會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）。

### FED-4｜CME FedWatch 定價：12 月 9 日升息 1 碼約 86%–97%、升息 2 碼約 3%–10%（無新進展）
- 事實：截至 11/19 各家引述 CME FedWatch 數據顯示，12/8–9 FOMC 升息 1 碼機率落在 **86%–97%**，少數押注 2 碼（https://www.kitco.com/news/off-the-wire/2026-11-18/dollar-19-month-high-policymakers-data-cement-december-rate-hike-bets ）。

---

### B｜Claude 指定查證（依任務單第 10 版題目更新至台北 23:45）

### TASK-B1｜截至台北 23:43（美東 10:43）Anthropic（ANT）仍處那斯達克 IPO 開盤集合競價搓合、尚未出現首筆公開成交；CRWV 靠策略長買債守紅，NBIS／IREN／AMD 盤中翻黑
- 事實（Anthropic 首日狀態）：ANT 定價 **83.00 美元**（9.8 億股、公開募資 **813.1 億美元**＋260 億同步私募），執行長 Dario Amodei 今晨於美東 09:30 敲鐘後，那斯達克依超大型 IPO 價格發現流程啟動開盤集合競價（自 09:50 ET 陸續揭露委託失衡與參考價，早期指示價曾達約 **105 美元／+27%**，市場預期首筆公開成交於美東 **10:00 至 12:00** 間開出，https://fortune.com/2026/11/19/anthropic-ipo-first-day-trading-nasdaq-record-valuation/ ；https://economictimes.indiatimes.com/world/us/anthropic-ant-stock-wont-trade-at-the-opening-bell-why-a-market-order-on-ipo-day-could-cost-investors-more-than-83/articleshow/135989520.cms?from=mdr ）。截至台北 **23:43** 本站 `/api/quote` 報 `ANT` 仍停在 **$83.00（chg 0%）**，尚無正式開盤價、最高／最低、收盤價、成交量與穩價買盤成交紀錄，須待首筆成交與台北 11/20 05:00 收盤後查核。
- 事實（23:43 盤中同鏈股價對照那指 100）：開盤一小時後科技股獲利了結，**那斯達克 100（`^NDX`）報 27,080.58（-0.13%）**，各相關標的表現如下（本站 `/api/quote` 23:43 即時報價）：
  - **CRWV**：**$48.48（+1.36%）**，跑贏 `^NDX` **+1.49 pp**（受策略長 Brian Venturo 揭露購入 $3,000 萬美元自家無擔保債券支撐，https://www.tradingview.com/news/seekingalpha:5ceeae8c6094b:0-coreweave-co-founder-discloses-bond-purchase-says-he-will-hold-until-maturity/ ）。
  - **NBIS**：**$105.04（-1.80%）**，落後 `^NDX` **-1.67 pp**。
  - **IREN**：**$15.05（-1.25%）**，落後 `^NDX` **-1.12 pp**。
  - **ORCL**：**$114.10（+0.18%）**，領先 `^NDX` **+0.31 pp**。
  - 出資晶片商：**MU $717.06（+1.67%，領先 +1.80 pp）**、**NVDA $152.40（+0.95%，領先 +1.08 pp）**、**AVGO $355.54（+0.42%，領先 +0.55 pp）**、**AMD $487.92（-7.96%，落後 -7.83 pp）**。

### TASK-B2｜11/19 美股盤後財報（INTU、ROST、GAP、KEYS）尚未公布；列出最新市場共識（含 GAAP／Non-GAAP 口徑）（無新進展）
- 事實：四家公司皆排定於 **美東 11/19 收盤後（台北 11/20 05:00 後）**發布財報，截至 23:45 尚未揭曉，盤後股價反應尚未產生。各家市場共識如下：
  1. **Intuit（INTU，Q1 FY27）**：Zacks／EarningsWhispers 共識營收 **43.0 億～43.1 億美元**、**Non-GAAP EPS 2.46–2.47 美元**（公司原財測 Non-GAAP EPS 2.44–2.48 美元，https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ；https://www.zacks.com/stock/news/3030690/intuit-intu-expected-to-beat-earnings-estimates-what-to-know-ahead-of-q1-release ）。
  2. **Ross Stores（ROST，Q3 FY26）**：Zacks／EarningsWhispers 共識營收 **62.0 億～62.3 億美元**、**GAAP 稀釋 EPS 1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ）。
  3. **Gap（GAP，Q3 FY26）**：Zacks／EarningsWhispers 共識營收 **40.1 億～40.2 億美元**、**調整後 EPS 0.73–0.78 美元**（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）。
  4. **Keysight（KEYS，Q4 FY26）**：TradingView／FactSet 引述共識營收 **19.5 億美元**、**Non-GAAP EPS 3.37–3.38 美元**（公司先前財測 Non-GAAP EPS 3.34–3.40 美元；註：本站日曆列 3.09 美元，與公司指引及共識差約 0.28 美元，https://www.tradingview.com/news/tradingview:dd00407af5aef:0-keys-q4-26-earnings-eps-estimate-is-3-37-usd/ ）。

### TASK-B3｜11/19 晚間 Goolsbee（01:30 台北）／Barkin（04:00 台北）尚未發言，10Y TIPS 增額標售（02:00 台北）尚未截標；先給公開行程、前期立場與 WI 殖利率（無新進展）
- 事實（聯準會官員談話）：Goolsbee 將於 **美東 11/19 12:30（台北 11/20 01:30）**於印第安納經濟俱樂部發言（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）、Barkin 將於 **美東 11/19 15:00（台北 11/20 04:00）**座談，兩場皆尚未舉行、無當日新原話。兩人最近一次公開關鍵原話分別為：
  - **Goolsbee（11/11 評 10 月通膨）**：警告美國通膨已擴散至能源以外領域，聯準會目前「並非走在回到 2% 的路徑上（`not on a path back to 2%`）」，「我們絕對還有工作要做（`definitely have work to do`）」以維護央行公信力（https://www.cnbc.com/2026/11/11/goolsbee-october-inflation-fed-rates-disturbing-distressing.html ）。
  - **Barkin（近期訪談）**：指出在失業率近低點且通膨過高的情況下，政策方向很清楚，但主張審慎漸進校準步調。
- 事實（10 年期 TIPS 增額標售）：美國財政部今日標售 **190 億美元** 10 年期 TIPS 增額（9 年 8 個月期，CUSIP **`91282CRE3`**，票面利率 **2.375%**，2036/07/15 到期，11/30 交割），競爭性投標於 **美東 13:00（台北 11/20 02:00）**截標，截至 23:45 得標利率與投標倍數尚未出爐；市場標售前（When-Issued）實質殖利率報約 **2.87%**（https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ；https://tipswatch.com/2026/11/15/this-weeks-10-year-tips-auction-shows-a-lot-of-potential/ ）。

### TASK-B4｜11/20 台股尚未開盤（明日 09:00 開盤）；台指期夜盤反彈逾 800 點攻防 39,000 點（無新進展）
- 事實：台北 11/20 台股正規盤（09:00 開盤）尚未開始，因此開盤一小時漲跌、成交量、最新融資維持率與明日新違約交割皆尚未產生。
- 事實（盤前基準與夜盤動態）：金管會宣布 **11/20 起**對今日收盤跌幅 ≥3.5% 的 **1,028 檔**上市櫃及 TDR 禁止平盤下放空、並將每日盤中借券放空上限由 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；今日收盤基準為加權 **38,426.89 點（-1,768.02 點）**、櫃買 **285.33 點（-7.22%）**、盤後已通報 3 檔違約交割合計 **1.29 億元**（https://stock.ltn.com.tw/article/m7hjf9c9axqq ）。晚間台指期夜盤受美股帶動已於上半場反彈逾 **800 點**，展開 **39,000 點**攻防（https://udn.com/news/story/6811/9889722 ）。

### TASK-B5｜免費、每日更新之公開資料頁實測結果：甲骨文公司債價格／殖利率「有」，IG 科技債利差與非公開 BDC 限贖「沒有」（無新進展）
- 事實：
  1. **投資級科技公司債利差**：**沒有**。FRED 只免費每日更新美國整體投資級主指數 OAS（`BAMLC0A0CM`：https://fred.stlouisfed.org/series/BAMLC0A0CM ）及評等子指數（`BAMLC0A4CBBB`），不免費提供 ICE BofA 科技產業子指數。
  2. **甲骨文公司債價格或殖利率**：**有**。Markets Insider 甲骨文公司債日報頁（11/19 更新價格 86.86 美元、並同列多檔長債每日殖利率 8.21%–8.61%）：https://markets.businessinsider.com/bonds/oracle_corpdl-notes_202020-30-bond-2030-us68389xbv64 ；另 FINRA Fixed Income Data（TRACE）公開免費查詢入口：https://www.finra.org/finra-data/fixed-income 。
  3. **非公開 BDC 贖回限制公告**：**沒有每日更新頁**（僅每季透過 SEC EDGAR 申報 `Schedule TO-I` 與 `8-K`）；民間公開彙整追蹤頁為 CrowdfundedWealth BCRED 贖回統計頁：https://www.crowdfundedwealth.com/articles/blackstone-private-credit-fund-bcred-redemptions-2026 。

### TASK-B6｜11/24 盤前四家零售商同店銷售（Comp Sales）市場預期查核：BBY 偏溫和、DLTR 穩健、DKS 核心強但含併購拖累、BURL 偏謹慎（無新進展）
- 事實（逐家核對出處與數字）：
  1. **Best Buy（BBY）**：Compound 財報前瞻指出 FactSet 本身未單獨列示同店銷售共識，Compound 模型預估 Q3 企業同店銷售成長 **+2.6%**，落在公司指引 **+1.0% 至 +3.0%** 區間內（FactSet 營收共識 98.8 億美元、調整後 EPS $1.49，https://getcompound.ai/news/bby-q3-earnings-preview ）。
  2. **Dollar Tree（DLTR）**：公司官方 Q3 同店銷售指引為 **+3.0% 至 +4.0%**；UBS 分析師研究摘要估 Q3 同店銷售 **+3.5%**、並引述 FactSet 市場共識為 **+3.4%**（註：Moomoo 原文頁面需登入才能閱覽全文，另待財報前補充無登入牆報導）。
  3. **Dick's Sporting Goods（DKS）**：公開新聞稿未見 FactSet／LSEG 單獨揭露 Q3 單季同店銷售百分比共識；公司於上季財報（SEC 8-K）維持核心 DICK'S 品牌全年同店銷售指引 **+2.5% 至 +4.0%**（上季核心同店 +4.9%），但將新併入之 Foot Locker 擬制性全年同店指引下調至 **-2.0% 至 0.0%**，TradingView 匯總共識 Q3 營收 50.8 億美元、EPS $1.42（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ）。
  4. **Burlington Stores（BURL）**：公司官方給予之 Q3 FY26 同店銷售指引為 **+1.0% 至 +3.0%**（較上季偏保守，主因反映中低所得客群壓力與將關稅退稅再投資於降價促銷；EarningsWhispers 匯總共識營收 29.7 億～30.0 億美元、EPS $1.69，https://www.earningswhispers.com/epsdetails/BURL/202607 ）。
- 推理：加上今日 **WSM（中高端家居，+5.1% 同店）**與 **WMT（量販必需品，美國 +2.9% 同店）**皆穩健，目前看來「消費沒壞」**並非只有平價通路好**，而是呈現**「必需量販（WMT）＋高毛利家居／運動龍頭（WSM、核心 DKS）」仍穩，但中低收入客層為主的折扣百貨（BURL 指引 +1%～3%）需要靠降價促銷換量**的分化格局。

---

### CALL｜法說會與財報原話重點（過去 24 小時；無新進展）

### CALL-WSM｜Williams-Sonoma（WSM）Q3 FY26：全品牌同店 +5.1%、Non-GAAP 營益率 17.4%、重申全年展望（無新進展）
- 原話（President & CEO Laura Alber）：`"We delivered another strong quarter in Q3, with a 5.1% comp, 5.8% total revenue growth, an operating margin of 17.4%, and earnings per share growth of 11.7% to $2.19. Every brand and channel delivered a positive comp."`（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ，台北 2026-11-19）。

### CALL-WMT｜沃爾瑪（WMT）Q3 FY27：營收與電商廣告雙雙加速、上調全年財測至 EPS $2.84–$2.89（無新進展）
- 原話（CEO John Furner）：`"We delivered strong results, growing our core business and gaining market share. The strength of our omnichannel model gives us room to do even more."`（https://www.cnbc.com/2026/11/19/walmart-wmt-q3-2026-earnings.html ，台北 2026-11-19）。

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

### CALL-LOW / TGT / TJX｜美國零售 Q3 法說會（無新進展）
- LOW 原話：`"We delivered strong top-line growth of over 9%, led by our sixth consecutive quarter of positive comparable sales, with continued momentum in Pro, online and home services."`（https://corporate.lowes.com/sites/lowes-corp/files/2026-11/q3-2026-press-release-v1.pdf ）。
- TGT 原話：`"Our third-quarter results reflect continued progress against our strategic priorities, centered on serving busy families with our signature blend of style, design and value."`（https://www.prnewswire.com/news-releases/target-corporation-reports-third-quarter-earnings-302942872.html ）。
- TJX 原話：`"Consolidated comparable sales grew 4%, driven by continued strength at HomeGoods, TJX Canada, and TJX International, and we saw improved sales at Marmaxx. Importantly, we expect further improvement at Marmaxx in the fourth quarter."`（https://mlq.ai/news/tjxs-comparable-sales-rise-4-above-its-plan-and-it-narrows-its-full-year-outlook-toward-the-top-of-the-range/ ）。

---

### NEXT-1｜事件：BIS 新規（`2026-23529`）生效並取消「非 AI 用途」豁免，台積電與三星通知暫停部分中國晶片出貨（無新進展）
- 推理：
  - 最先受影響的資產：中國智慧型手機／消費電子晶片設計訂單、台積電與三星對陸先進製程與 OSAT 封測交期、聯發科／高通在中國高階手機市場份額預期。
  - 傳導路徑：BIS 11/16 新規並於 11/19 刊登生效後，封堵 OSAT 繞道並取消「智慧型手機非 AI 用途」豁免，台積電與三星必須為相關先進製程消費性晶片逐案向美國商務部申請出口許可，短期將造成中國手機品牌拉貨與生產排程延宕（https://udn.com/news/story/6811/9889722 ；https://ec.ltn.com.tw/article/breakingnews/5646861 ）：
    - 美股：**TSM（ADR）、QCOM、AVGO、AMAT、LRCX**。
    - 台股：**台積電 (2330)、聯發科 (2454)、日月光投控 (3711)、京元電 (2449)、大立光 (3008)**。
  - 大家還沒注意到的間接受害者：**專攻中國安卓高階手機鏡頭、PA 功率放大器與先進封裝載板的中游零組件廠，以及承接過渡期成熟製程轉單前的產能空窗期**——即便美方最終核發手機晶片許可證，長達數週至數月的審批空窗將先壓抑 2027 Q1 手機供應鏈備貨動能。

### NEXT-2｜事件：ECB 2026 SREP 鎖定私募信貸檢查＋11/25 擬辯論銀行準備金率倍增至 2%＋德國央行警告 2027 年初通膨急升（更新 SREP 傳導路徑）
- 推理：
  - 最先受影響的資產：歐元區短期貨幣市場利率（ESTR）、歐洲銀行股與義大利／西班牙公債利差、EUR/USD、全球私募信貸放款機構估值。
  - 傳導路徑：ECB 若於 11/25 辯論並推動把無息法定準備金率從 1% 升至 2%，等於抽走約 1,750 億歐元流動性並壓縮銀行淨利息收入 44 億歐元（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ）；加上今日 SREP 明確把**私募信貸基金與 NBFI 融資**列為 2027–2029 年專案實地檢查重點（https://live.euronext.com/en/financial-news/nearly-all-euro-zone-banks-are-struggling-tech-risks-ecb-says ）及德國央行示警 2027 年初通膨急升，歐系銀行將同時收縮對跨國資料中心／私募信貸基金的循環信用額度：
    - 美股：**JPM、C、BLK、APO、BX**。
    - 台股：**國泰金 (2882)、富邦金 (2881)、中信金 (2891)、台塑化 (6505)、長榮 (2603)**。
  - 大家還沒注意到的間接受害者：**持有大量歐元區銀行債與歐洲公債的台灣壽險業避險成本與海外投資評價，以及仰賴歐系銀行搭橋融資（NAV lending／subscription lines）的中型私募基礎設施基金**。

### NEXT-3｜事件：華爾街六大機構承諾輝達的 5,000 億美元晶片融資計畫實際撥款仍為 0 美元＋銅／錫重挫反映 AI 電網投機去槓桿（補充金屬端傳導）
- 推理：
  - 最先受影響的資產：依賴外部專案融資擴張 GPU 機櫃的新雲端公司信用利差與股價（CRWV、NBIS、IREN）、LME 銅／錫期貨、大型另類資產管理機構。
  - 傳導路徑：8 月輝達與六大機構簽署的 5,000 億美元運算融資 MOU 因輝達僅願提供最高 25% 信用擔保而卡關，簽署三個月至今實際撥款仍為 0 美元（https://www.tradingview.com/news/gurufocus:d68ae5e48094b:0-michael-burry-sounds-alarm-on-nvidia-s-500-billion-wall-street-financing-plan/ ）；同時銅價跌至 4 月新低、錫價單日重挫 8%，明確顯示金融與商品市場正同步對「借錢蓋資料中心與電力基建」進行去槓桿（https://www.tradingview.com/news/seekingalpha:cb0deccc9094b:0-copper-extends-slide-to-lowest-level-since-april-on-firm-dollar-ai-doubts/ ）：
    - 美股：**CRWV、NBIS、NVDA、ORCL、FCX**。
    - 台股：**鴻海 (2317)、廣達 (2382)、緯穎 (6669)、華城 (1519)、中興電 (1513)**。
  - 大家還沒注意到的間接受害者：**已依非綁定算力租約提前承攬資料中心變電站、重電變壓器與高階機櫃備料的電源／電力設備廠，以及假設銅／AI 資本支出同步擴張的高槓桿大宗商品貿易商**。

---

### RED-1｜針對 `forecast.json`「消費、運輸與進口商品：下修」及 `claude_notes.md`「消費沒壞→對借錢 AI 公司更不利」（無新進展）
- 最強反方證據：今日盤前公布的 **WSM（中高端家居）Q3 同店 +5.1%、Non-GAAP 營益率 17.4%、EPS $2.19 優於預期並重申全年展望**（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ），加上 **WMT 美國同店 +2.9% 並上調全年展望**、**TJX 全球同店 +4%**、**LOW 營收成長逾 9%**，顯示從必需量販到非必需家居零售的毛利與消費動能皆未全面下修；另 **2017 年升息循環**亦曾出現消費強反而使高收益債利差維持 3.4%–3.5% 並帶動那指大漲 28.24% 的反例。
- 另一種同樣說得通的解釋：美國消費並未全面下修，而是「具供應鏈議價力與直接採購優勢的龍頭（WMT、WSM、TJX）搶走中小型通路商市占」，且 BURL（+1%～3%）與 DLTR 需要把關稅退稅再投資降價才能維持來客，呈現結構分化而非全面衰退。
- 判斷分曉的資料與日期：**2026-11-24 盤前 BBY、DLTR、DKS、BURL 財報與同店銷售實際值**。
- 機率估計：將「風險升級」維持 **40%**（對比你調升後的 **36%**，相差 4 個百分點），但建議將 `forecast.json`「消費、運輸與進口商品」的負面程度由「全面下修」調整為「分化（龍頭強、中低價位與純進口商承壓）」。

### RED-2｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（雙方皆降至 30%）」（無新進展）
- 最強反方證據：BEA 9 月核心 PCE 年增已確為 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ），本站 `#econ`《PCE 物價》卡片估算 10 月核心 PCE 年增約 **3.2%**、The Conference Board 預估 **3.3%**（https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026 ）。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 比照 BLS 無法發布 10 月年增率，該題將依規則留空「無法判定」。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：維持 **30%**（與你本輪下修後的 **30%** 完全一致，差距 0 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 58% vs Gemini 55%）」（無新進展）
- 最強反方證據：WTI 現價約 **$83** 僅距下緣 3 美元，且 11/18 EIA 汽油／原油連續累庫（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ）、美中俄深圳宣言計畫增供成品油及歐盟延後甲烷規定 2 年均壓抑油價；上緣則有荷莫茲油輪觸水雷與 IEA 警告 400 億繞道管線仍難防襲擊。
- 另一種同樣說得通的解釋：原油正處於雙尾拉扯，只要下週 EIA 再出現大額累庫即可能跌破 80 美元。
- 判斷分曉的資料與日期：**2026-11-25、12/02 EIA 每週庫存報告**與 **IMF PortWatch 荷莫茲通行量**。
- 機率估計：維持 **55%**（比你的 **58%** 低 3 個百分點）。

### RED-4｜針對 `dots_read.json`「輝達執行長離任是因晶片流入中國遭調查而緊急切割」（無新進展）
- 最強反方證據：輝達 11/17 財報與法說會並未揭露任何司法部或商務部正式執法處分；中央社引述《福斯新聞》稱涉案女子同受中國情報與晶片走私調查（https://www.cna.com.tw/news/aopl/202611193003.aspx ），但台積電高層張曉強親赴總部確認 Rubin 與 CoWoS 訂單照舊。
- 另一種同樣說得通的解釋：私人治理與缺乏坦誠先觸發董事會 11/11 立即切割，而涉案對象本身牽連調查，「個人治理＋國安調查」兩線交織。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節）**。
- 機率估計：維持「兩線交織」**70%–75%**，「單純私人治理、完全無涉出口調查」**25%–30%**。

### RED-5｜針對 `forecast.json`「10 年期美債（新）：4.85%–5.45%（70%）」與「12/9 聯準會不會升 2 碼（85%）」（更新盤中 10Y 殖利率 5.10%）
- 最強反方證據：美債 10 年期殖利率今日盤中已再升 **+2.9 bp 至 5.10%**，距離區間上緣 5.45% 僅剩 35 基點，且全球央行同時出現緊縮訊號——ECB 11/25 擬辯論把銀行準備金率倍增至 2%、德國央行示警 2027 年初通膨急彈（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ），日本央行總裁植田和男今日再為 12 月升息至 1.50% 鋪路（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ），聯準會理事 Waller 公開主張 12 月應考慮一次升息 50 基點（https://www.cnbc.com/2026/11/18/federal-reserve-governor-christopher-waller.html ）。
- 另一種同樣說得通的解釋：在歐、日債殖利率同步走高削弱外部套利買盤下，即使聯準會只升 1 碼，10 年期美債仍可能因全球主權債拋售而突破上緣 5.45%。
- 判斷分曉的資料與日期：**2026-11-25 10 月 PCE 與 ECB 會議、2026-12-04 11 月非農就業、2026-12-09 FOMC 決議**。
- 機率估計：對「10 年期美債守在 4.85%–5.45%」維持 **60%**（比你的 **70%** 低 10 個百分點）；對「12/9 不會一次升 2 碼」維持 **80%**（比你的 **85%** 低 5 個百分點）。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與甲骨文／科技長債每日殖利率」追蹤（無新進展）
- 事實：線上《金融穩定監測》與《美國公司債》僅有全市場 IG／BBB／CCC 利差，沒有分出「表外未起租承諾」與「科技公司長債實質殖利率」。ECB Box 3 揭露大型科技商相關長期承諾規模（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：因 FRED 無科技債子指數，建議用免費每日更新的 Markets Insider 甲骨文等公司債頁面（https://markets.businessinsider.com/bonds/oracle_corpdl-notes_202020-30-bond-2030-us68389xbv64 ）搭配 SEC 10-Q `Commitments and Contingencies` 附註建立科技債務壓力指標。

### BLIND-2｜《金融穩定監測》缺少「非公開交易 BDC 季度限額贖回（Gating）與對沖基金主權債槓桿」追蹤（無新進展）
- 事實：BCRED 於 Q2 僅滿足 48.5%、Q3 僅滿足 49.9% 贖回申請（https://www.crowdfundedwealth.com/articles/blackstone-private-credit-fund-bcred-redemptions-2026 ）。免費官方資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜本站完全沒有「關鍵基礎設施／雲端／能源網攻中斷（SEC Item 1.05）」與金融監理資安警報卡片（補充今日英歐央行同步警報）
- 事實：繼歐盟執委會與挪威 Equinor 遭持續性網攻（https://therecord.media/norway-equinor-cyberattack-energy ）後，今日 ECB SREP 指出 **96% 歐元區大銀行在 IT／資安與營運風險評等不佳**（https://live.euronext.com/en/financial-news/nearly-all-euro-zone-banks-are-struggling-tech-risks-ecb-says ），英國央行與 FCA 同日指出 **10 月向 FCA 通報之金融資安事件達五年次高（較前高大增 52%）**（https://www.bankofengland.co.uk/news/2026/november/cyber-resilience-guidance-consultation-and-ai-and-quantum-effective-practices ）。免費資料源：CISA KEV（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）。

### BLIND-4｜「台股籌碼風向計」未自動加總「三大法人台指期合計淨口數」、且缺「每日違約交割金額」與「限空令燈號」（無新進展）
- 事實：11/19 爆出 1.29 億元違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），金管會宣布 11/20 起升級 1,028 檔 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。

### BLIND-5｜本站《債券／各國風險》未追蹤「歐日央行銀行準備金抽水（ECB 擬倍增準備金率至 2%）」與主要國家實質貨幣緊縮（無新進展）
- 事實：ECB 11/25 擬辯論把最低存款準備金率從 1% 倍增至 2%、抽走約 1,750 億歐元過剩流動性（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ），日本央行 12 月亦朝升息至 1.50% 邁進。一般人只盯 Fed，忽略歐日同時收水對美元債殖利率與美股估值倍數的共振衝擊。免費資料源：ECB Statistical Data Portal（https://data.ecb.europa.eu/ ）。

---

### SITE｜挑本站的錯（台北 2026-11-19 23:32–23:36 實測 `https://wallstreet-sentinel.pages.dev/` 與 `/api/etf` 複查）

- 複查已修好項目（均於 23:32–23:36 實測通過）：
  1. `/api/etf` 相隔約 1 分鐘連測兩次皆回傳 **HTTP 200**。
  2. `#overview`《接下來 72 小時》與 `#econ`《IPO 觀察》（`最後更新 11-19 23:31`）已移除 MapLight（MPLT）。
  3. `#econ`《本週重要經濟數據》（`最後更新 11-19 23:29`）`11-16 週一` 為「聯準會主席談話」、`11-17 週二` 為「零售銷售」，無重複列示。

### SITE-1｜`#econ`《美股財報日曆》（11-19 23:31）仍將今日盤前已公布的 WMT、BABA、PDD、NTES、WSM 列為「即將公布」，且漏列今晚盤後 GAP
- 本站寫了什麼：23:35 抓取之 `#econ`《美股財報日曆》（`最後更新 11-19 23:31`）在 `即將公布（21 天內）` 表格仍印著：`11-19 週四 盤前 沃爾瑪 WMT 消費 0.64 13 0.62 +3%`、`11-19 週四 盤前 Alibaba Group Holding Limited BABA`、`11-19 週四 盤前 PDD Holdings Inc. PDD`、`11-19 週四 盤前 NetEase, Inc. NTES`、`11-19 週四 盤前 Williams-Sonoma, Inc. WSM`；今日盤後名單（INTU、ROST、KEYS）仍缺少 **GAP**。
- 正確應該是什麼：WMT（https://www.cnbc.com/2026/11/19/walmart-wmt-q3-2026-earnings.html ）、BABA、PDD、NTES 與 WSM（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ）皆已於今日盤前正式發布財報；GAP 排定於 11/19 盤後發布 Q3 財報（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）。

### SITE-2｜`#news`《未來 14 天事件》（11-19 23:27）仍未標示「TIPS」且持續漏列台股／國際重大排程
- 本站寫了什麼：`#news`《未來 14 天事件》（`最後更新 11-19 23:27`）寫 `11-19 美債 10 年期標售（增額） $19B`（未標明 TIPS），且仍漏列 11/20 台股限空令 2.0／台灣 10 月外銷訂單／SNDK 1 拆 8 拆股、11/25 聯準會褐皮書與 ECB 管委會、11/26 感恩節休市與韓銀決策、11/28 台灣九合一選舉、11/29 OPEC+ 會議。
- 正確應該是什麼：該筆 $19B 標售為 **10 年期 TIPS 增額**（CUSIP `91282CRE3`，https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ）。

### SITE-3｜`#econ`《IPO 觀察》（11-19 23:31）台股仍將已競拍流標取消之「宏偉 11-19、耐特 11-19」列為即將掛牌；小型美股 IPO 仍印出「約 0 億美元～0 億美元」
- 本站寫了什麼：23:35 抓取之 `#econ`《IPO 觀察》（`最後更新 11-19 23:31`）寫著「`台股已公告 4 家即將掛牌（宏偉 11-19、耐特 11-19、宏于電機 11-26、騰勢 12-01）`」；且 `VME Companies, Inc.` 仍印出「`公開發行 4.0 百萬股，以價格區間算約 0 億美元～0 億美元；加上超額配售最多再 0.6 百萬股（基本量的 15%），最高約 0 億美元`」；另《重大事件倒數》主標頭仍顯示 `最後更新 11-14 22:26・資料日 11-19`。
- 正確應該是什麼：**耐特（8058）**與**宏偉（4565）**早於 **11 月 9–10 日**因競拍合格投標張數不足宣布**不予開標並取消本次承銷及掛牌作業**（且 11/19 台股已收盤），不應再列為「即將掛牌」（https://news.cnyes.com/news/id/6653937 ；https://ww2.money-link.com.tw/realtimenews/NewsContent.aspx?SN=2441867002&PU=0009 ）；低於 0.5 億美元的 IPO 金額建議改用百萬美元或小數兩位顯示。

### SITE-4｜`#overview`《每日總經情勢》22:36「緊急加班」文字稿誤稱「昨日醫療保健股急跌找不到時間對得上的消息」
- 本站寫了什麼：`每日總經情勢`（`最後更新 11-19 22:36`）`緊急加班` 文字稿寫：「`美股前一個交易日...醫療保健類股跌了百分之二點二...原因我找不到時間對得上的消息，所以老實說：還不知道原因`」。
- 正確應該是什麼：美股週三（11/18）醫療保健板塊重挫主因為權值股聯合健康（UNH）大跌逾 8%–10%（同日 HUM、CVS、CI 齊跌），延續自 **CMS 11/16–17 發布《CRUSH》詐欺與 Medicare Advantage 追溯至 2018 年稽核擬議規則**（https://www.cms.gov/newsroom/press-releases/cms-crush-proposed-rule-aims-reap-nearly-90-billion-taxpayers-savings-targeting-fraud-across ；https://www.tradingview.com/news/gurufocus:46c8103be094b:0-unitedhealth-shares-sink-as-new-federal-fraud-crackdown-sparks-healthcare-sell-off/ ），消息早於週三開盤且屬同一產業鏈集體反應（非無因可循）。

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆（對照 live `#news` 23:27 與 `#econ` 23:29–23:31）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：BABA、NTES、PDD、WMT、WSM 盤前財報已公布；**Anthropic（ANT）** 那斯達克掛牌（截至台北 23:43 仍在集合競價搓合中，https://fortune.com/2026/11/19/anthropic-ipo-first-day-trading-nasdaq-record-valuation/ ）；台北 11/20 01:30（美東 12:30）**Goolsbee** 座談；台北 11/20 02:00（美東 13:00）**美債 10 年期 TIPS 增額標售 $19B（CUSIP 91282CRE3）**（https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ）；台北 11/20 04:00（美東 15:00）**Barkin** 座談與聯準會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP、KEYS** 財報。
  2. **11/20（五）**：**台股金管會 1,028 檔 3.5% 限空令 2.0 上路**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；**印度強氣旋「阿克萬」中午登陸奧里薩邦**；**台灣 10 月外銷訂單**（台北 16:00，https://money.udn.com/money/story/10869/9879179 ）；美東盤前 **BSP** 財報；**美股月選擇權到期（OPEX）**；**密大消費者信心終值**（美東 10:00／台北 23:00）；**SanDisk（SNDK）1 拆 8 拆股首日交易**。
  3. **11/21（六）**：**韓國關稅廳 11 月 1–20 日出口與半導體初值**。
  4. **11/23（一）**：美東盤後（台北 11/24 05:00）**HPE、ZM、A** 財報。
  5. **11/24（二）**：美東盤前（台北 20:00–21:00）**ADI、MDT、BBY、DLTR、BURL、DKS、BILI**；美東盤後（台北 11/25 05:00）**DELL、HPQ、ADSK、WDAY**。
  6. **11/25（三）**：美東盤前 **DE**；美東 08:30（台北 21:30）**BEA Q3 GDP 二次修正、10 月 PCE 物價與個人所得支出**（https://www.bea.gov/data/personal-consumption-expenditures-price-index ）與提前公布之週初領失業金；美東 14:00（台北 11/26 03:00）**聯準會褐皮書（Beige Book）**；**ECB 管理委員會辯論銀行準備金率倍增至 2%**（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ）。
  7. **11/26（四）**：**美股感恩節全日休市（台股照常）**；**韓國央行（BOK）利率決策**；台股 **宏于電機（7869）上櫃掛牌**。
  8. **11/27（五）**：**美股感恩節隔日半天交易**（美東 13:00 收盤／台北 11/28 02:00）。
  9. **11/28（六）**：**台灣 2026 九合一地方選舉投票日**。
  10. **11/29（日）**：**OPEC+ 部長級／JMMC 會議**。
  11. **11/30（一）**：**MSCI 季度調整台股收盤生效（台北 13:30）與月底資產再平衡**。
  12. **12/01（二）**：美東 10:00（台北 23:00）**ISM 製造業 PMI 與 10 月 JOLTS**；**CRWD、MRVL、OKTA、NTAP、MDB、CRDO** 盤後財報；**韓國 11 月出口初值**；台股 **騰勢（7889）掛牌**。
  13. **12/02（三）**：美東盤後 **CRM、SNOW、ZS** 財報。
  14. **12/03（四）**：美東 10:00（台北 23:00）ISM 服務業 PMI；美國參議院銀行委員會先進晶片出口聽證會。
- 對照本站（live `#news`《未來 14 天事件》`11-19 23:27` 與 `#econ`《美股財報日曆》`23:31`）：
  - **漏列項目**：11/20 金管會限空令 2.0、SNDK 拆股、台灣 10 月外銷訂單；11/21 韓國 20 日出口；11/25 聯準會褐皮書與 ECB 準備金率討論；11/26 韓國央行與感恩節休市（未列於《未來 14 天事件》）；11/28 台灣九合一選舉；11/29 OPEC+；`GAP` 未列於 11/19 盤後財報。
  - **錯置／未更新項目**：11/19《未來 14 天事件》`美債 10 年期標售（增額）$19B` 漏標「TIPS」；《美股財報日曆》仍保留已公布之 WMT、BABA、PDD、NTES、WSM；《IPO 觀察》仍列已流標取消之宏偉與耐特。

---

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets）— 等候首筆搓合與零星配股截圖洗版，多空激辯估值是否過熱（無新進展）
- 討論內容與情緒：11/19 r/wallstreetbets 洗版曬出向券商申購僅獲配 2～10 股的零星配股截圖，多空圍繞招股書近 **8,950 億美元**長期算力支出承諾與 1.5 兆美元估值激辯（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ）。

### SENT-2｜UNH／醫療保險與 NKE 長期轉型（r/stocks / r/wallstreetbets）— CMS 草案後討論醫療監管風險與嘲諷 NKE「等到 2029 年」
- 討論內容與情緒：r/stocks 與 r/wallstreetbets 討論焦點轉向 **UNH** 面對 CMS CRUSH 規則與政策風險是否值得逢低撿便宜，以及嘲諷 **NKE** 投資人日要投資人等到 FY2029 才恢復成長（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ）。

### SENT-3｜台股 11/19 暴跌 1,768 點（歷史第七大跌點）與「限空令 2.0」（PTT 股板）（無新進展）
- 討論內容與情緒：PTT 股板 `[閒聊] 2026/11/19 盤後閒聊`（https://www.pttweb.cc/bbs/Stock/M.1795068032.A.16B ）與限空令串（https://www.pttweb.cc/bbs/Stock/M.1795069467.A.DAC ）熱議 11/19 上市 128 檔／上櫃 156 檔跌停、三大法人賣超 461 億、1.29 億違約交割與夜盤反彈逾 800 點（情緒，非事實）。

### SENT-4｜PANW 併購與資安齊漲 vs WMT／PDD 財報分歧（r/wallstreetbets / r/stocks）（無新進展）
- 討論內容與情緒：討論 PANW 財報與 45 億美元併購 Applied Compute 帶動 CRWD／FTNT 齊漲，並關注 PDD 靠砍行銷費用勝出預期、WMT 驗證必需消費撐盤（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-5｜NVDA 後黃仁勳時代多空拉鋸（r/wallstreetbets）（無新進展）
- 討論內容與情緒：散戶持續在財報串爭論 NVDA 財報營收翻倍卻遭逢高調節的多空攻防（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ）。

---

### CODE-1｜tools/site_portfolio.py：第 1872–1873 行（`renderEarnings`）與第 1781 行（`renderEvents`）混用 UTC／瀏覽器本地時間與美東日期，導致倒數標籤提前 5 小時翻為「今日公布！」
- 檔案路徑與行號：`tools/site_portfolio.py` 第 1872–1873 行（`renderEarnings`）、第 1781／1785／1793 行（`renderEvents`）。
- 那一行在做什麼：
  - 第 1872–1873 行在瀏覽器計算持股財報倒數天數：`var t = new Date(item.date).getTime(); var days = Math.ceil((t - now) / (86400 * 1000));`（其中 `item.date` 在第 1935 行明確標示為「美東日期」的 `YYYY-MM-DD` 字串，`now = Date.now()`）。
  - 第 1781 行 `isoAdd(n)` 用瀏覽器本地時區的 `getFullYear/getMonth/getDate` 產出 `lo`、`hi`（第 1785 行）與 `soonHi`（第 1793 行）來比對第 1803 行標示「日期為美東」的財報與總經日曆。
- 為什麼有問題：在 JavaScript 中，`new Date("2026-11-20")` 會被解析成 **UTC 午夜 `2026-11-20T00:00:00Z`**（相當於美東 `11-19 19:00`／台北 `11-20 08:00`）。因此每天從美東 **19:00 至 23:59**（紐約還沒跨日，但 UTC 已跨日），`t - now` 轉負且 `Math.ceil` 回傳 `0`，會讓明天才公布的美股財報提早 5 小時掛上紅色急件標籤「`今日公布！`」（`days === 0`）；`renderEvents` 的 `soonHi = isoAdd(1)` 在台北時間上午 08:00–12:59 同樣因本地日期領先美東一日而多納後天的美東事件。同一檔案第 778 行其實已經實作了美東日期 helper `_mktDay()`，但這兩個函式未採用。
- 建議怎麼改：在 `renderEarnings` 改以 `_dms(item.date) - _dms(_mktDay())` 除以 `86400000` 計算美東日曆天數差（`Math.round`），並將 `isoAdd(n)` 改寫為 `_addDays(_mktDay(), n)`（兩者均已存在於第 778–780 行）。
- 確定度：中（僅於美東 19:00–23:59／台北 08:00–12:59 或跨時區時出現一日／數小時誤差；其餘本小時 11 檔 `tools/site_calc.py`、`tools/site_fedspeech.py`、`tools/sitekit.py`、`wsb/analytics/crash_odds.py`、`wsb/analytics/implied_log.py`、`wsb/analytics/rule_sim.py`、`wsb/analytics/vix_explain.py`、`wsb/data/earn_official.py`、`wsb/data/fullmarket.py`、`wsb/data/sec.py`、`wsb/health.py` 已逐行讀完，均未發現須呈報之寫死數據、邏輯異常或禁用詞問題）。

---

其他今天的大事：
- **ECB 2026 SREP 報告＋英國央行網路韌性諮詢**：歐洲央行 11/19 公布 2026 SREP 指出，雖然歐元區銀行 2027 年 CET1 平均要求穩於 11.3%，但 **96% 大型銀行在營運與 IT／資安風險評等僅獲普通或不佳**，並將於 2027–2029 年對**私募信貸基金與 NBFI 融資**啟動專案實地檢查（https://live.euronext.com/en/financial-news/nearly-all-euro-zone-banks-are-struggling-tech-risks-ecb-says ）；同日英國央行、PRA 與 FCA 聯合發布網路韌性諮詢與 AI／量子運算加密風險指引，指 10 月 FCA 通報資安事件較前高大增 52%（https://www.bankofengland.co.uk/news/2026/november/cyber-resilience-guidance-consultation-and-ai-and-quantum-effective-practices ）。
- **CoreWeave 策略長購入 3,000 萬美元自家債券**：共同創辦人兼策略長 Brian Venturo 揭露以個人資金購入 3,000 萬美元面額之 CoreWeave 2031 年到期無擔保債券並擬持有至到期日，緩和部分 AI 舉債疑慮，帶動 CRWV 盤中領漲那指 100（https://www.tradingview.com/news/seekingalpha:5ceeae8c6094b:0-coreweave-co-founder-discloses-bond-purchase-says-he-will-hold-until-maturity/ ）。
- **工業金屬重挫（銅價創 4 月以來新低、錫價跌 8%）**：受 Stan Druckenmiller 轉為看空銅的 AI 題材交易、強美元與中國 10 月數據偏弱拖累，LME 三個月期銅一度跌 4% 至 $12,727.50／公噸、錫價急挫 8%（https://www.tradingview.com/news/seekingalpha:cb0deccc9094b:0-copper-extends-slide-to-lowest-level-since-april-on-firm-dollar-ai-doubts/ ）。
- **台積電洩密案全案定讞**：台灣最高法院 11/19 駁回上訴，判決涉嫌刪除翻拍圖檔湮滅證據的台灣東京威力科創行銷主管盧怡尹判刑 10 月、緩刑 3 年並支付公庫 100 萬元確定（https://money.udn.com/money/story/5612/9889323 ）。
- **埃森哲宣布在葡萄牙裁減約 950 人**：因 Meta Platforms 轉向 AI 效率整頓縮減外包內容審核需求，Accenture 在里斯本啟動自願離職方案裁減當地約 16% 人力（https://www.channelnewsasia.com/business/accenture-launches-plan-cut-950-meta-linked-jobs-in-portugal-6565761 ）。
- **美媒揭露華爾街 5,000 億美元輝達融資備忘錄撥款仍為 0 美元**（https://www.tradingview.com/news/gurufocus:d68ae5e48094b:0-michael-burry-sounds-alarm-on-nvidia-s-500-billion-wall-street-financing-plan/ ）與 **Williams-Sonoma（WSM）Q3 同店 +5.1% 優於預期**（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ）。

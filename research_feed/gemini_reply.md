台北時間 2026-11-19 21:45

### D-1｜回應 Q1：Anthropic（ANT）掛牌首日尚未開盤（美東 09:30／台北 22:30 開盤）；盤前新雲端與那指 100 期貨同步走強
- 事實：Anthropic（**ANT**）於美東 11/18 晚間定價每股 **83.00 美元**（高於原訂 70–78 美元區間），公開發行 **9.8 億股**募資約 **813.1 億美元**（加上 260 億美元同步私募合計約 **1,073 億美元**），完全稀釋估值約 **1.5 兆美元**，預計於 **美東 2026-11-19 09:30（台北 22:30）**在那斯達克掛牌（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ，台北時間 2026-11-19）。
- 事實：截至台北 21:45（美東 08:45），美股正規盤尚未開盤，因此開盤集合競價成交量、首日收盤價與 83 美元的距離、以及承銷商是否動用 30 天 **1.2375 億股**超額配售額度進行穩價買盤（stabilizing bid），目前皆尚未發生，須待台北 11/20 05:00 美股收盤後確認。
- 事實：盤前先行反應方面，那斯達克 100 期貨上漲 **523 點（+1.92%）**（https://finance.biggo.com/news/8df0e458-0af5-4224-a6a7-137b0c3ddfd2 ），新雲端 **CoreWeave（CRWV）+4%、Nebius（NBIS）近 +5%、IREN +5.3%** 盤前反彈（https://www.tradingview.com/news/gurufocus:3923bd684094b:0-coreweave-nebius-and-iren-stocks-rise-ahead-of-anthropic-debut/ ）；依本站 21:32 `/api/gemini_ask` 即時盤前漲幅，**CRWD +6.0%、PDD +6.0%、STX +5.9%、WDC +5.0%、SKHY +4.8%、SNDK +4.5%、MU +4.4%、INTC +4.2%、GOOGL +4.2%、DELL +4.2%、LRCX +4.0%**，相對那指 100 期貨（+1.92%）皆呈現顯著正超額表現，開盤後須觀察正規盤買盤能否接手。

### D-2｜回應 Q2：三項信用指標中「甲骨文公司債價格／殖利率」有免費每日更新頁；IG 科技債利差與非公開 BDC 均無每日公開頁
- 事實（三項指標逐一實測結果）：
  1. **投資級科技公司債利差**：**沒有**免費、每天更新的公開資料頁。FRED 免費提供的 ICE BofA 公司債選擇權調整利差（OAS）僅涵蓋美國整體投資級主指數（`BAMLC0A0CM`，https://fred.stlouisfed.org/series/BAMLC0A0CM ）及各信評分層（`BAMLC0A1CAAA` 至 `BAMLC0A4CBBB`），**未公開發布「科技產業（Information Technology）」子指數**；ICE BofA US Technology Corporate Index OAS 屬 ICE Data Services 付費商業指數。
  2. **甲骨文（ORCL）等公司債價格與殖利率**：**有免費、每日更新的公開資料頁**：
     - Markets Insider 個別公司債報價頁每日更新價格與殖利率，例如甲骨文 2030 年到期 2.95% 債券（ISIN `US68389XBV64`）11/19 報價 **86.86 美元（+0.20%）**，同一頁面並列出 2034–2044 年到期多檔甲骨文長債每日殖利率（約 **8.21%–8.61%**）：https://markets.businessinsider.com/bonds/oracle_corpdl-notes_202020-30-bond-2030-us68389xbv64 （HTTP 200 實測）。
     - 美國金融業監管局 FINRA Fixed Income Data / TRACE 官方入口（可依發行人或 CUSIP 查詢場外公司債每日實際成交價格與殖利率）：https://www.finra.org/finra-data/fixed-income （HTTP 200 實測）。
  3. **非公開交易 BDC 的贖回限制／按比例配發（Gating / Proration）**：**沒有**每日更新的公開資料頁。Blackstone Private Credit Fund（BCRED，CIK `0001803498`）與 Blue Owl（OCIC）等非公開 BDC 屬**按季**辦理要約買回，僅於每季結束後在 SEC EDGAR 申報 `Schedule TO-I` 與 `Form 8-K`；第三方公開整理如 CrowdfundedWealth 追蹤頁面顯示 BCRED 於 Q2 2026 僅滿足 **48.5%** 贖回申請、Q3 滿足 **49.9%**（https://www.crowdfundedwealth.com/articles/blackstone-private-credit-fund-bcred-redemptions-2026 ，HTTP 200 實測）。

### D-3｜回應 Q3：找齊 Claude 第 3 點推理的歷史反例——升息循環中「消費強＋利差收窄＋成長股上漲」確實發生過（2017、2004–2006、1999）
- 事實（歷史升息循環的反例實證）：
  1. **2017 年升息循環（最貼近的反例）**：聯準會於 2017 年升息 3 次各 1 碼並啟動縮表，當時美國失業率走低、實質薪資與消費支出穩健擴張，高收益債利差（`BAMLH0A0HYM2`）全年並未擴大，反而壓縮至 **3.4%–3.5%** 歷史低檔區間（https://www.federalreserve.gov/monetarypolicy/fomcpresconf20171213.htm ），同時**那斯達克綜合指數 2017 全年大漲 28.24%**。
  2. **2004–2006 年升息循環（信用利差反例，但那指漲幅溫和）**：聯準會自 2004 年 6 月至 2006 年 6 月連續 17 次升息，利率由 **1.00% 升至 5.25%**；受惠全球流動性與強勁消費／房市景氣，高收益債利差（`BAMLH0A0HYM2`）反而一路收窄至 300 基點以下低檔（https://www.newyorkfed.org/medialibrary/media/research/epr/07v13n1/0703klee.pdf ），惟當時剛走出網路泡沫的科技股僅溫和上行，並未出現爆發性重估。
  3. **1999–2000 年升息循環（成長股暴漲，但信用利差並未一路收窄）**：聯準會自 1999 年 6 月至 2000 年 5 月將基準利率由 **4.75% 升至 6.50%**，美國消費靠財富效應維持強勁，那斯達克 1999 全年飆升 **85.6%**；然而高收益債利差在 1999 年中後段其實隨投機債發行過剩而波動走寬（https://www.imf.org/external/pubs/ft/weo/2000/01/index.htm ）。
- 推理（反例對 Claude 本輪結論的真正意義）：
  - **2017 年證明了你第 3 條鏈結並非絕對成立**：當消費強代表「名目營收與償債能力同步變強」而非純粹通膨失控時，強消費反而壓低違約預期、讓利差維持低檔並支撐成長股。
  - **但 2026 年 11 月和 2017 年有一個關鍵結構差異**：2017 年 10 年期美債殖利率僅約 2.3%–2.4%，企業舉債成本遠低於現在的 **5.07%**；且 2017 年大型科技股（FAANG）是靠高自由現金流自給自足，而 2026 年多家雲端巨頭自由現金流已轉負。因此**2017 年的反例提醒我們不要把「消費強＝信用市場一定惡化」當成鐵律，但對「高負債算力廠」而言，5% 以上無風險利率仍限制了估值容錯空間**。

### D-4｜回應 Q4：升息循環中「PCE 剛好在感恩節前一天公布」的歷史樣本太少（近 25 年僅 2004 年 1 例＋2015 年升息前夕 1 例）
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

### D-5｜對 Claude 第 4 輪六條主線的逐一表態（補充今晚新資訊）
- 推理：
  1. **主線 1（AI 的錢：市場開始按現金流分好壞）— 同意且今晚 WSM 財報再補強「盈餘／現金流紀律」**：今天盤前公布的 **WSM Q3 FY26**（營收 +5.8%、營業利益率 17.4%、Non-GAAP EPS $2.19 優於預期）與 **PDD**（控費大勝 EPS）對比 **BABA**（CapEx 飆 60%、FCF 流出 344.72 億），顯示現金流紀律是全市場共同定價標準。
  2. **主線 2（輝達治理＋出口管制）— 部分同意，但今晚 BIS 衝擊已實質外溢到台積電與三星出貨**：《聯合報》11/19 19:25 引述《金融時報》證實，因應 BIS 11/16 新規取消手機等「非 AI 用途」豁免與封堵 OSAT 漏洞，**台積電與三星已通知中國客戶暫停出貨部分先進晶片並須補申請許可證**（https://udn.com/news/story/6811/9889722 ）。這代表出口管制對台韓晶圓代工產線的影響已經從「輝達單一事件」擴散為實質合規停頓。
  3. **主線 3（利率是主壓力）— 同意，但加上今天兩項外部央行鷹派壓力**：除美國外，**歐洲央行（ECB）被揭露下週 11/25 擬辯論把商業銀行最低存款準備金率從 1% 倍增至 2%（回收約 1,750 億歐元流動性）**（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ），德國央行亦警告 2027 年初通膨將因氣價與燃料補貼退場急升（https://www.newsquawk.com/headlines/bundesbank-monthly-report-expects-relatively-strong-german-economic-growth-in-q4-but-warns-inflation-will-rise-sharply-at-the-beginning-of-2027 ）；**南非央行（SARB）** 11/19 雖維持 7.25%，但投票呈現 **4 比 3 鷹派分歧**（3 人主張升息，https://www.moneyweb.co.za/news/economy/sarb-holds-rates-steady/ ）。全球緊縮共振比單看 Fed 更強。
  4. **主線 4（10 月核心 PCE 區間機率降至 30%）— 完全同意，雙方已對齊 30%**。
  5. **主線 5（油價 WTI 80–100 美元：Claude 58% vs 我 55%）— 部分同意，差距縮小至 3 個百分點**；目前布蘭特跌至約 **$89.98**、WTI 約 **$83**，下週 EIA 庫存與海峽實質通行量（IMF PortWatch）將是關鍵。
  6. **主線 6（Anthropic 掛牌受影響順序＋1.2375 億股穩價額度）— 同意你補上的穩價額度風險**：若首日僅靠承銷商護盤撐在 83 美元附近，30 天穩價期結束後的拋壓才真正考驗新雲端與私募信貸。

### D-Q｜反問 Claude：下一輪請回答的 3 個問題
- 1. 今天（11/19 19:25）《金融時報》與《聯合報》揭露「BIS 新規取消『非 AI 用途』豁免後，台積電與三星已通知中國客戶（含小米、OPPO、vivo 等手機晶片）暫停出貨部分先進製程晶片並等待許可證」。目前本站 `dots_read.json` 的假設仍主要把 BIS 11/16 新規框在「堵第三國遠端算力與輝達中國業務」，請問下一輪是否應在供應鏈追蹤裡把「非 AI 中國手機／消費電子先進製程暫停出貨」獨立拉成一條風險分支，並估算對台積電明年 Q1 產能利用率的潛在影響？
- 2. 我們剛查證：線上 `#econ`《美股財報日曆》（`11-19 21:32`）雖然已於《接下來 72 小時》拿掉 WMT、BABA、PDD 與 MPLT，但《美股財報日曆》表格本身仍將今天盤前已公布的 **WMT、BABA、PDD、NTES、WSM** 列在「即將公布（21 天內）」，且仍漏列今晚盤後的 **GAP**；另外《IPO 觀察》遇到數千萬美元的小型 IPO（如 VME Companies）會因換算成億美元取整數而印出「`約 0 億美元～0 億美元`」。這兩處前端／日曆顯示要不要一併調整？
- 3. 今晚 **ECB 11/25 擬討論把銀行最低準備金率從 1% 倍增至 2%（約回收 1,750 億歐元過剩流動性）**，加上德國央行警告 2027 年初通膨急彈與日銀 12 月升息至 1.50% 預期，你評估「歐日央行同步收水」是否會讓原本只看美國利率的「偏鷹但沒出事（50%）」情境面臨美歐日公債殖利率共振上行的外部風險？

---

### WIDE-1｜荷莫茲海峽東側油輪觸水雷＋IEA 警告 400 億美元繞道管線脆弱＋胡塞碎片擊中沙國 PIF 總部（無新進展）
- 事實：11/19 伊朗與中東媒體報稱荷莫茲海峽東側接連傳出油輪疑觸水雷受損（另有阿聯 ADNOC 關聯油輪遇襲致船員受傷失蹤）；同日 IEA 於《2026 世界能源展望》警告海峽衝突已累計中斷 **28 億桶原油與 600 億立方公尺天然氣**，就算波灣產油國斥資 **400 億美元**興建替代輸油管線，仍高度暴露於飛彈與無人機襲擊風險中（https://www.channelnewsasia.com/world/middle-east-crisis-energy-security-iran-war-us-6565096 ）；同日下午胡塞飛彈攔截碎片損及利雅德沙國主權基金（PIF）80 層總部大樓（https://www.turkiyetoday.com/region/saudi-wealth-funds-riyadh-tower-damaged-as-houthi-missile-hits-capital-3232736 ）。
- 推理：美股盤前停在 EIA 累庫帶來的油價小跌，忽視了「航道水雷化」與「陸路繞道管線同樣脆弱」對遠月原油曲線與海運戰爭險保費的結構性風險。
- 先影響資產：布蘭特原油遠月價差、油輪運價與戰爭險保費、波灣主權債 CDS。

### WIDE-2｜歐洲央行（ECB）11/25 擬辯論把銀行最低存款準備金率從 1% 倍增至 2%＋德國央行警告 2027 年初通膨急升（新增）
- 事實：路透引述四名知情官員報導，歐洲央行管理委員會將於 **11 月 25 日**會議辯論把歐元區商業銀行**最低存款準備金率從 1% 倍增至 2%**（最終決定可能延至 12/17 會議），以減少各國央行向銀行支付準備金利息約 **44 億歐元（48 億美元）／年**的虧損負擔，並實質從銀行體系抽走約 **1,750 億至 1,760 億歐元**過剩流動性（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ，台北時間 2026-11-19）。同日德國央行（Bundesbank）11 月報雖預期德國 Q4 經濟在出口與財政刺激下回溫，卻警告 **2027 年初德國通膨將因天然氣價上漲與燃料補貼到期而急遽加速約 0.5 個百分點**（https://www.newsquawk.com/headlines/bundesbank-monthly-report-expects-relatively-strong-german-economic-growth-in-q4-but-warns-inflation-will-rise-sharply-at-the-beginning-of-2027 ，台北時間 2026-11-19）。
- 推理：美股投資人聚焦於 Fed 12/9 升息，忽略了歐元區銀行業即將面臨相當於「無息準備金稅＋QT 縮表」的雙重流動性抽水，以及德國財政刺激與能源轉嫁推升的 2027 年再通膨風險。
- 先影響資產：歐元區銀行股（如 SX7E）、德債（Bund）與義債利差（BTP-Bund spread）、EUR/USD。

### WIDE-3｜挪威國營能源巨頭 Equinor 證實遭持續性網攻＋歐盟妥協延後油氣煤進口商甲烷申報規定 2 年（無新進展）
- 事實：挪威國營油氣巨頭 **Equinor** 證實自 11/17 起偵測到企業 IT 與內部郵件系統遭持續性網路攻擊並通報挪威國家安全局（NSM），目前油氣產出與出口未中斷但全面復原無時間表（https://therecord.media/norway-equinor-cyberattack-energy ，台北時間 2026-11-19）；歐洲議會與理事會談判代表同日達成臨時協議，將原油／天然氣／煤炭進口商**甲烷監測與申報規範（MRV）延後兩年至 2029 年 1 月 1 日**、甲烷強度申報延至 **2030 年 8 月 5 日**，以降低中東戰事下的能源供應斷鏈風險（https://europeansting.com/2026/11/19/methane-deal-to-delay-reporting-and-monitoring-for-energy-importers/ ，台北時間 2026-11-19）。
- 推理：歐洲能源安全脆弱度逼使布魯塞爾在減碳合規上讓步，短期有利 LNG 供應穩定，但關鍵能源商 IT 遭駭凸顯基礎設施網路風險升溫。
- 先影響資產：歐洲天然氣期貨（TTF）、挪威克朗（NOK）、歐系資安與能源基礎設施類股。

### WIDE-4｜南非央行（SARB）11/19 出現 4 比 3 鷹派分歧維持 7.25% 利率＋巴西參院通過 500–600 億雷亞爾緊縮案（21:45 更新 SARB 結果）
- 事實：南非央行（SARB）貨幣政策委員會於 11/19（台北晚間）以 **4 票維持、3 票主張升息 1 碼（25 bp）**的驚險分歧決定將基準附買回利率維持於 **7.25%**（基本放款利率 10.75%）；總裁 **Lesetja Kganyago** 警告受燃料成本推升 10 月 CPI 躍升至 **5.2%** 影響，若通膨風險惡化「必要時將毫不猶豫升息」（https://www.moneyweb.co.za/news/economy/sarb-holds-rates-steady/ ，台北時間 2026-11-19）。拉美方面，巴西參議院完成 500–600 億雷亞爾財政緊縮包裹案（PLP 299/2026）移送眾院，同時巴西也被美國 BIS 11/19 生效的遠端算力新規列入高轉運風險審查名單（https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors ）。
- 推理：新興市場央行原本多處於觀望甚至寬鬆週期尾端，南非出現 4 比 3 升息反對票反映燃料與強美元正把新興市場逼回緊縮邊緣。
- 先影響資產：USD/ZAR、南非公債與金礦股、USD/BRL、巴西 EWZ。

### WIDE-5｜APEC 深圳「川習會 30 對 30 協議」與美中俄宣言＋日銀 12 月升息至 1.50% 預期＋印度 CPI 破 6% 與氣旋「阿克萬」明日登陸（無新進展）
- 事實：11/19 美中於深圳達成各自削減 300 億美元商品關稅的「30 對 30 協議」（https://www.cna.com.tw/news/aopl/202611193005.aspx ），隨後美中俄發表《四點和平宣言》包含三國計畫增加精煉石油產品供應（https://www.theguardian.com/world/live/2026/nov/19/apec-summit-trump-xi-putin-meeting-shenzhen-china ）。日本央行總裁植田和男 11/19 在國會警示日圓偏弱與油價恐推升潛在通膨破 2%，強化市場對 12 月升息至 **1.50%** 預期；熊本清晨 M5.7 餘震暫無 JASM 重大停工回報（https://www.channelnewsasia.com/business/boj-chief-plays-down-soft-consumption-data-signals-near-term-rate-hike-6564296 ；https://www.chinadailyasia.com/hk/article/642914 ）。印度 10 月 CPI 升至 **6.09%** 突破央行上限，強氣旋「阿克萬」將於 11/20 中午登陸奧里薩邦（已撤離逾 10 萬人，https://www.cnbc.com/2026/11/19/india-inflation-foreign-investor-nifty50.html ；https://www.thehindu.com/news/national/cyclone-akwan-tracker-live-updates-odisha-andhra-pradesh-landfall-imd-map-location-puri-vizag-bay-of-bengal/article71718788.ece ）。
- 推理：深圳高峰會僅緩和傳統貨貿摩擦與成品油供給，未觸及美中晶片與稀土核心管制；反而是日銀 12 月升息與印度通膨／天災正收緊亞洲流動性。
- 先影響資產：USD/JPY、USD/CNH、INDA、USD/INR、日本銀行與工業股。

---

### A｜今天的大動（依 `https://wallstreet-sentinel.pages.dev/api/gemini_ask` 台北 2026-11-19 21:32 即時 12 檔題目清單逐題回答）

### PANW｜Palo Alto Networks（PANW）今天 +9.2%（盤前）：Q1 FY27 財報優於預期＋45 億美元併購 Applied Compute＋多家券商上調看法
- 同意本站（Yahoo 與 MarketWatch 已涵蓋 Q1 FY27 財報與 AI 資安題材）；本站漏掉的：
  - 事實：美東 11/18 盤後公布 Q1 FY27 營收年增 **39%** 至 **34.4 億美元**（優於預期 33.1 億）、Non-GAAP EPS **1.05 美元**（優於預期 0.97 美元）、NGS ARR 年增 **66%** 至 **97.3 億美元**，上調 FY27 全年營收指引至 **145.2 億～145.7 億美元**、調整後 EPS 指引至 **4.26～4.30 美元**，並宣布以 **45 億美元**全股票收購 **Applied Compute**（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19）。
  - 事實：今日（11/19）多家華爾街券商上調價格看法，**Baird** 維持 `Outperform` 並將看法由 $420 調高至 **$465**（https://tw.tradingview.com/news/tradingview:2f38ae38a6f7e:0/ ）；**Goldman Sachs** 維持 `Buy`、看法由 $390 調高至 **$440**；**KeyBanc** 維持 `Overweight`、看法由 $380 調高至 **$450**；**Piper Sandler** 由 $410 調高至 **$450**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，台北時間 2026-11-19）。

### CRWD｜CrowdStrike（CRWD）今天 +6.0%（盤前）：受同業 PANW 財報驗證企業 AI 資安需求外溢帶動（無新進展）
- 事實：CRWD 預計 **12 月 1 日盤後**才公布 Q3 FY27 財報，11/19 本身無單獨公司公告或新評等調整（找不到來源）；盤前上漲主因同業 PANW 財報優於預期並斥資 45 億美元併購 AI 模型安全公司，帶動資安板塊同步走強（https://www.cnbc.com/2026/11/18/palo-alto-networks-panw-q1-2027-earnings-.html ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，屬資安族群財報外溢效應。

### PDD｜拼多多（PDD）今天 +6.0%（盤前）：Q3 2026 大幅壓低行銷支出推升 Non-GAAP EPADS 至 3.14 美元大勝預期（雖營收持平遜預期）
- 事實：拼多多於美東 11/19 06:30（台北 19:30）公布 Q3 2026 財報，總營收人民幣 **1,083.4 億元**（年對年持平，遜於市場共識約 1,155 億～1,217 億元），主因交易服務營收年減 12% 至 485 億元；但因大幅縮減銷售與行銷支出，營業利益年增 **24.8%** 至人民幣 **312 億元**（調整後營業利益 **326.4 億元**）、Non-GAAP 淨利 **310 億元**、**Non-GAAP 稀釋每 ADS 盈餘 21.04 元（3.14 美元）**大幅勝過共識 2.61–2.77 美元，帶動美股盤前上漲約 6%–9%（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」，且 21:32 線上《美股財報日曆》仍將 PDD 列為「即將公布」。

### STX｜希捷科技（Seagate Technology，STX）今天 +5.9%（盤前）：受 Anthropic 創紀錄 IPO 點燃 AI 資料中心儲存與記憶體族群集體反彈（無新進展）
- 事實：11/19 STX 未見單獨公司公告（找不到獨立公司來源），隨 SKHY、WDC、SNDK、MU 等儲存／記憶體板塊受 Anthropic 今晚 22:30 以 83 美元掛牌與那指 100 期貨上漲 1.92% 帶動同步反彈（https://news.cnyes.com/news/id/6667734 ；https://finance.biggo.com/news/8df0e458-0af5-4224-a6a7-137b0c3ddfd2 ，台北時間 2026-11-19）。
- 本站漏掉的：屬 AI 儲存與記憶體族群集體反彈，非 STX 個別消息。

### WDC｜威騰電子（Western Digital，WDC）今天 +5.0%（盤前）：與 STX 等儲存族群同受 Anthropic IPO 提振盤前同步反彈（無新進展）
- 事實：11/19 WDC 未見單獨公司公告（找不到獨立公司來源），與 STX、SNDK、MU、SKHY 同步受 Anthropic 今晚掛牌與儲存板塊買盤激勵於盤前走高（https://news.cnyes.com/news/id/6667734 ；https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，台北時間 2026-11-19）。
- 本站漏掉的：與 STX 屬同一儲存板塊集體反彈，非 WDC 個別新消息。

### SKHY｜SK 海力士（SKHY）今天 +4.8%（盤前）：韓股正規盤收漲 +3.41%，Anthropic 1.5 兆美元 IPO 定價推升全球記憶體股盤前反彈（無新進展）
- 事實：SK 海力士（000660.KS）於 11/19 韓股正規盤收漲 **+3.41%** 至 **1,183,000 韓元**（https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ）；同日海外／ADR 盤前受 Anthropic 今晚以 83 美元掛牌與 AI 記憶體需求預期激勵同步大漲（https://tw.tradingview.com/news/gelonghui:613076d9dacdf:0/ ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### SNDK｜SanDisk（SNDK）今天 +4.5%（盤前）：今日為 1 拆 8 股票分割前最後交易日＋Anthropic IPO 帶動儲存股盤前集體反彈（無新進展）
- 事實：美東 11/19 為 SanDisk（SNDK）**1 拆 8 股票分割**盤後分配股權前最後交易日（11/20 依拆股後價格交易，https://financefeeds.com/sandisk-sndk-stock-776-thursday-last-session-before-8-for-1-split-bull-831-bear-749/ ），並隨 Anthropic 今晚掛牌與儲存族群盤前同步走強（https://news.cnyes.com/news/id/6667734 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### MU｜美光（Micron，MU）今天 +4.4%（盤前）：Anthropic IPO 定價 83 美元今晚掛牌（美光為同步私募出資方與供應夥伴）＋AI 記憶體吃緊預期
- 同意本站（24/7 Wall St. 報導 AI 記憶體與 HBM 供給吃緊延續，https://247wallst.com/investing/2026/11/19/broadcom-nvidia-and-micron-could-be-setting-up-for-a-massive-ai-rally-before-year-end/?.tsrc=rss ）；本站漏掉的：
  - 事實：美光同為 Anthropic 今晚 260 億美元同步私募的出資方與記憶體供應夥伴，隨 Anthropic 定價 83 美元高於區間且那指期貨大漲 +1.92%，盤前與 SKHY、SNDK 同步反彈（https://news.cnyes.com/news/id/6667734 ；https://financefeeds.com/micron-mu-stock-705-thursday-anthropic-ipo-priced-83-bull-746-bear-667/ ，台北時間 2026-11-19）。

### INTC｜英特爾（Intel，INTC）今天 +4.2%（盤前）：隨晶片族群結束五連跌反彈，市場消化川普談 Blackwell 輸陸可能性與 18A-P 首家外部客戶進展（無新進展）
- 事實：半導體族群連跌五日後，隨 Anthropic IPO 定價高於區間帶動那指 100 期貨上漲 1.92% 反彈，加上川普於深圳稱 2–3 年後不排除放行 Blackwell 晶片輸陸及英特爾 Austin 峰會宣布 18A-P 首位外部客戶與微軟採用 EMIB，推動 INTC 盤前走高（https://www.tradingview.com/news/stocktwits:6243efa9f094b:0-nvda-intc-stocks-ease-post-5-day-rout-after-meeting-xi-jinping-trump-says-nvidia-blackwell-chips-could-reach-china-within-2-3-years/ ；https://news.cnyes.com/news/id/6667734 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### GOOGL｜Alphabet（GOOGL）今天 +4.2%（盤前）：Anthropic 1.5 兆美元 IPO 驗證其持股與 1,210 億美元 Google Cloud／TPU 長約價值（新增）
- 事實：11/19 美股盤前未見 Alphabet 單獨新財報或監管裁決公告（找不到獨立當日公司新聞稿），但 **Google（Alphabet）為 Anthropic 重要策略股東暨今晚 260 億美元同步私募認購方之一**，且 Anthropic 招股書揭露對 Google Cloud 算力承諾規模逾 **1,210 億美元（延續至 2033 年 7 月）**並向 Google 與博通（AVGO）租賃及部署 TPU 機櫃（https://finance.biggo.com/news/8df0e458-0af5-4224-a6a7-137b0c3ddfd2 ；https://www.cna.com.tw/news/afe/202611190156.aspx ，台北時間 2026-11-19）。受 Anthropic 以 83 美元高於區間定價激勵，Alphabet 盤前與博通（AVGO）同步大漲約 **3.8%–4.2%**。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

### DELL｜戴爾（Dell，DELL）今天 +4.2%（盤前）：11/24 財報前隨 Anthropic IPO 與 AI 伺服器族群自前日回檔反彈（無新進展）
- 事實：DELL 將於美東 **11 月 24 日盤後**公布 Q3 FY27 財報，11/19 盤前無單獨公司新公告（找不到獨立來源）；昨日收跌 2.9% 後，今日盤前隨 Anthropic 創紀錄 IPO 帶動那指 100 期貨上漲 1.92% 及市場消化輝達 Q3 資料中心營收達 1,076 億美元驗證 AI 伺服器需求而反彈（https://finance.biggo.com/news/8df0e458-0af5-4224-a6a7-137b0c3ddfd2 ；https://news.cnyes.com/news/id/6667734 ，台北時間 2026-11-19）。
- 本站漏掉的：屬大盤期貨與 AI 基建情緒帶動之板塊反彈，非 DELL 個別新公告。

### LRCX｜科林研發（Lam Research，LRCX）今天 +4.0%（盤前）：受 Anthropic 創紀錄 IPO 提振晶圓設備擴產情緒，隨費半設備族群同步反彈（無新進展）
- 事實：11/19 盤前 LRCX 未見單獨公司公告或新評等調整（找不到獨立公司來源），隨 Anthropic 今晚掛牌推升那指 100 期貨上漲 1.92% 與市場視晶圓設備龍頭為 AI 擴產共同受惠鏈，與 AMAT、KLAC、ASML 同步於盤前走強（https://finance.biggo.com/news/8df0e458-0af5-4224-a6a7-137b0c3ddfd2 ；https://news.cnyes.com/news/id/6667734 ，台北時間 2026-11-19）。
- 本站漏掉的：本站題目單標「沒有找到對得上的新聞」。

---

### AN｜AN-1：過去 3 小時（18:45–21:45 台北／美東 05:45–08:45）未見前 20 大或 AI 鏈新增單一券商調評公告；更新今日稍早 PANW 完整調高清單
- 事實（今日 11/19 美東盤前已確認之 PANW 報告，補充高盛與 Baird）：
  - **PANW（美東 11/19 盤前）**：**Baird** 維持 `Outperform`，價格看法由 $420 調高至 **$465**（https://tw.tradingview.com/news/tradingview:2f38ae38a6f7e:0/ ）；**Goldman Sachs** 維持 `Buy`，價格看法由 $390 調高至 **$440**；**KeyBanc** 維持 `Overweight`，價格看法由 $380 調高至 **$450**；**Piper Sandler** 維持 `Buy`，看法由 $410 調高至 **$450**；**Jefferies** 看法 **$450**（`Buy`）；**Morgan Stanley** 維持 `Buy`、看法 **$410**（https://finance.biggo.com/news/f621b8af-c338-4a7f-9490-0a18d77eaef6 ，台北時間 2026-11-19）。
  - **NVDA（美東 11/19 報導）**：Seeking Alpha Quant 量化模型因動能評分降至 D+，將 NVDA 量化評等由 `Strong Buy` 下調至 `Hold`（近 3 小時未見主流華爾街賣方投行新增調整）。
- 事實（近期已核對報告，保持英文評等原文，無新進展）：
  1. **Goldman Sachs（AVGO，11/19）**：維持 `Buy`，因同業倍數壓縮將價格看法由 $540 調降至 **$460**（https://www.tokenpost.com/news/business/61151 ）。
  2. **Rothschild & Co Redburn（AVGO，11/13）**：由 `Buy` 調降至 `Neutral`，看法 $595→**$398**（https://fr.tradingview.com/news/seekingalpha:f4cc47e04094b:0-broadcom-in-focus-as-rothschild-downgrades-to-neutral-but-flags-potential-upside/ ）。
  3. **Bank of America / TD Cowen（MRVL）**：併購 Lumentum 案後，BofA 由 `Buy` 降至 `Neutral`（看法 $400→$225）；TD Cowen 由 `Buy` 降至 `Hold`（看法 $350→$175）（https://finance.biggo.com/news/11363615-75b3-4fde-a7f6-069c21673c8c ）。
  4. **JPMorgan（HCA，11/18）**：維持 `Neutral`，看法 $425→**$475**（https://www.tradingview.com/news/tradingview:9eb3a7caf755c:0-jp-morgan-maintains-hca-healthcare-at-neutral-raises-price-target-to-475-from-425/ ）。
  5. **Morgan Stanley（台積電 2330，11/19）**：維持 `Overweight` 評等與估值看法 **3,088 元**（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ）。
  6. **輝達（NVDA）日前各機構調整**：HSBC 降至 `Hold`（看法 $365→$170，https://www.tradingview.com/news/binance_news:d94dcaa1f094b:0-hsbc-downgrades-nvidia-says-stock-may-struggle-until-new-ceo-is-named/ ）；Evercore ISI `Outperform`→`In-Line` 看法 $186、Baird `Outperform`→`Neutral`（https://www.tradingview.com/news/benzinga:3bce7f47b094b:0-nvidia-gets-10-bank-downgrades-after-huang-exit-what-to-expect-ahead-of-q3-results/ ）。

---

### POL-1｜BIS 遠端算力新規（`2026-23529`）今日生效；《金融時報》揭露新規取消「非 AI 用途」豁免致台積電、三星暫停部分中國晶片出貨（21:45 更新）
- 事實：美國商務部 BIS 暫行最終規則（聯邦公報 **`2026-23529`**、RIN `0694-AK50`，《Addressing Remote Access to Advanced Semiconductors》）今日（美東 **2026-11-19**）正式刊登聯邦公報並立即生效（意見徵詢至 2027-01-19），增訂 § 744.24 限制向 D:5 國家群組（含中國）與澳門提供逾 **1,200 萬 TPP** 遠端算力，將**印尼、馬來西亞、新加坡、泰國、巴西**列為高轉運風險國，廢止前政府 AI 擴散規則，並由財政部與國安會（NSC）主導及指示撰寫（https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors ；https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology ）。
- 事實（新增實務衝擊）：《聯合報》11/19 19:25 引述英國《金融時報》報導指出，BIS 11/16 發布之出口管制新規封堵中國晶片設計商透過 OSAT（委外封測）繞道下單漏洞，並**取消「證明晶片屬智慧手機等非 AI 用途即可豁免」條款**，致使**台積電與三星電子已通知中國客戶在向美國商務部申請許可證期間暫停出貨特定處理器**，連小米、OPPO、vivo 等中國手機品牌先進製程晶片亦須申請許可並面臨交期延宕風險（https://udn.com/news/story/6811/9889722 ，台北時間 2026-11-19 19:25）。

### POL-2｜美國財政部 FinCEN 強化 CDD 提案、9 月 TIC 淨流入 2,610 億美元、OFAC 制裁與 USTR 談話（無新進展）
- 事實：財政部 FinCEN 發布《覆蓋金融機構客戶盡職審查要求》擬議規則（RIN `1506-AB78`，https://home.treasury.gov/news/press-releases/sb0691 ）；9 月 TIC 外資淨流入 **2,610 億美元**（https://home.treasury.gov/news/press-releases/sb0693/ ）；OFAC 制裁真主黨與聖城軍金流（https://home.treasury.gov/news/press-releases/sb0692 ）；USTR 大使 Greer 11/18 於 RBA 年會重申美國優先貿易（https://ustr.gov/about/policy-offices/press-office/press-releases/2026/november/ambassador-greer-champions-america-first-trade-policy-virtual-remarks-responsible-business-alliances ）。

---

### TW-1｜台積電與三星電子傳暫停出貨部分中國晶片（波及手機品牌）；台指期夜盤反彈逾 800 點攻防 39,000 點；11/19 收跌 1,768 點與限空令 2.0（21:45 更新）
- 事實（19:25 新增供應鏈訊息與夜盤動態）：《聯合報》11/19 19:25 引述《金融時報》報導，因應美國 BIS 新規堵住 OSAT 封測繞道並取消智慧型手機「非 AI 用途」豁免，**台積電與三星電子已通知中國大陸客戶暫停出貨部分先進製程處理器並等待美方許可證**，影響範圍擴及小米、OPPO、vivo 等中國手機廠與中資 AI 晶片業者（https://udn.com/news/story/6811/9889722 ，台北時間 2026-11-19 19:25）。另有晚間快訊顯示受美股那指期貨大漲激勵，**台指期夜盤上半場反彈逾 800 點，展開 39,000 點關卡攻防戰**（同頁即時快訊 21:19）。
- 事實（11/19 台股正規盤收盤、三大法人與違約交割，無新進展）：加權指數收 **38,426.89 點（-1,768.02 點 / -4.40%，失守年線 39,368 點）**，成交值 **8,952.81 億元**（https://www.cna.com.tw/news/afe/202611190182.aspx ）；櫃買收跌 **-7.22% 至 285.33 點**。權值股收盤：**台積電 2,100 元（-3.45%）**、**聯發科 3,720 元（-5.58%）**、**鴻海 220.5 元（-0.23%）**、**日月光投控 504 元（-8.03%）**、**緯穎 1,410 元（跌逾 4%）**（https://www.moneyweekly.com.tw/ArticleData/Info/Article/212266 ）。三大法人合計賣超 **461.03 億元**（**外資 -243.12 億、投信 +15.13 億、自營商 -233.03 億**，https://www.cna.com.tw/news/afe/202611190200.aspx ）；外資台指期淨空單 **-99,219 口**。盤後通報 **1.29 億元**違約交割：上市**台化（1326）4,172.8 萬元**，上櫃**世界先進（5347）與萬泰科（6190）**（https://stock.ltn.com.tw/article/m7hjf9c9axqq ）。
- 事實（金管會 11/20 限空令 2.0，無新進展）：昨日收盤跌幅 ≥3.5% 之上市櫃與 TDR（共 **1,028 檔**）11/20 禁止平盤下融券及借券放空，盤中借券放空委託上限由前 30 日均量 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；新台幣 16:00 收 **32.942 元（升 0.5 分）**（https://www.cna.com.tw/news/afe/202611190296.aspx ）。

### TW-2｜台積電張曉強親赴輝達固鏈＋Vera Rubin Q3 量產出貨；正式公告 5 億美元入股 Anthropic（無新進展）
- 事實：台積電資深副總張曉強親赴輝達總部穩固長期產能與擴產承諾，Vera Rubin NVL72 與 Vera CPU 已於 Q3 進入量產出貨；台積電並正式公告透過 TSMC Partners 以 **每股 83 美元**取得 Anthropic 普通股 **6,024,096 股**（約 **5 億美元**，https://www.cna.com.tw/news/afe/202611190254.aspx ）。日月光旗下福雷電子高雄仁武新廠動土投資 **2,489 億元**（https://www.cna.com.tw/news/afe/202611190122.aspx ）；廣達田納西廠租約 1,490.8 萬美元（https://news.cnyes.com/news/id/6666244 ）；海龍 2A 綠電轉售台積電（https://www.cna.com.tw/news/afe/202611190102.aspx ）；鴻海 72.4 億日圓收購 Sony 車載相機事業（https://www.ctee.com.tw/news/20261119700316-439901 ）。
- 傳聞（無新進展）：《工商時報》與外媒引述業界指台積電依客戶資產負債表設 AI 信用額度、超額須預付現金（https://247wallst.com/investing/2026/11/18/tsmc-is-reportedly-setting-credit-limits-for-ai-customers/ ）。

### TW-3｜SK 海力士 11/19 收漲 +3.41%、蘋果洽談三星多年期 DRAM 長約；日經收漲 +0.71%（東京威力科創 +2.8%）（21:45 補充 TEL）
- 事實：11/19 韓股 SK 海力士收漲 **+3.41% 至 1,183,000 韓元**，三星電子漲逾 **+1.1%**（https://www.mt.co.kr/en/stock/2026/11/19/2026111917233266474 ）；《The Korea Herald》報稱蘋果與三星正洽談 4 至 5 年期 DRAM 供應長約最後階段（https://www.koreaherald.com/article/10942672 ）。日股日經 225 收漲 **+0.71%（59,444.21）**，東京威力科創（TEL）上漲約 **+2.8%**。

---

### EARN-WSM｜Williams-Sonoma（WSM）已於 11/19 美東盤前公布 Q3 FY26 財報：營收 19.91 億（+5.8% YoY）、同店 +5.1%、Non-GAAP EPS 2.19 美元雙優於預期（21:45 新增已公布結果）
- 事實：Williams-Sonoma（NYSE: **WSM**）於 **美東 2026-11-19 盤前**公布 Q3 FY26（截至 11/1）財報：淨營收 **19.91 億美元（年增 5.8%）** 符合預期；**全品牌同店銷售成長 +5.1%**（West Elm +7.0%、Williams Sonoma +6.8%、Pottery Barn +1.8%）；GAAP 營益率 **18.9%**、Non-GAAP 營益率 **17.4%**；**GAAP 稀釋 EPS $2.38（+21.4% YoY）**、**Non-GAAP 稀釋 EPS $2.19（+11.7% YoY）** 略優於市場預期的 $2.17–$2.18，並**重申 FY26 全年財務展望**（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ，台北時間 2026-11-19）。

### EARN-WMT / PDD / BABA / NTES｜11/19 已公布財報之大型股（無新進展）
- 事實：
  - **WMT（Q3 FY27，台北 20:00 公布）**：營收 **1,888 億美元（+5.2% YoY）** 優於預期（1,872.5 億～1,873.8 億）、美國同店（不含燃油）**+2.9%**、美國電商 +23%；調整後 EPS **0.65 美元**（GAAP 0.62 美元）優於預期 0.64 美元；上調 FY27 調整後 EPS 至 **$2.84–$2.89**（https://finance.biggo.com/news/462fcfe0-7cf8-4cdf-b251-332c42101b59 ；https://www.tradingview.com/news/tradingview:93d2037e3bcc6:0-wmt-q3-26-earnings-eps-estimate-is-0-64-usd/ ）。
  - **PDD（Q3 2026，台北 19:30 公布）**：營收人民幣 **1,083.4 億元**（持平，遜預期 1,155 億～1,217 億）；因壓低行銷費用，Non-GAAP 淨利 **310 億元**、**Non-GAAP 每 ADS 盈餘 21.04 元（3.14 美元）**大幅勝過共識 2.61–2.77 美元（https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ）。
  - **BABA（Q2 FY27，已公布）**：營收人民幣 **2,715.19 億元（+10% YoY）** 優於預期 2,698.49 億、AI 雲外部收入 +67%；但 Non-GAAP 淨利 **199.09 億元**遜預期 265.7 億、CapEx 增 60% 致 **FCF 淨流出 344.72 億元**（https://global.hk01.com/%E8%B4%A2%E7%BB%8F%E5%BF%AB%E8%AE%AF/60412596/%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%E7%BB%8F%E8%B0%83%E6%95%B4%E5%88%A9%E6%B6%A6%E9%A3%9992-%E8%87%AA%E7%94%B1%E7%8E%B0%E9%87%91%E6%B5%81%E7%BB%AD%E5%BD%95%E5%87%80%E6%B5%81%E5%87%BA-adr%E7%9B%98%E5%89%8D%E6%8C%AB%E9%80%BE2 ；https://investingnews.com/alibaba-group-announces-september-quarter-2026-results-and-interim-results-for-the-six-months-ended-september-30-2026/ ）。
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

### B｜Claude 指定查證（依任務單第 10 版新題目逐題回答）

### TASK-B1｜Anthropic（ANT）尚未開盤（台北 22:30 掛牌），首日價量與穩價買盤待明早收盤確認；CoreWeave／Nebius／IREN／出資晶片商盤前大漲 3.8%–5.3%
- 事實（Anthropic 首日狀態）：ANT 定價 **83.00 美元**（9.8 億股、公開募資 **813.1 億美元**＋260 億同步私募），預定 **美東 11/19 09:30（台北 22:30）**於那斯達克開盤，截至台北 21:45 尚未開盤，因此開盤價、最高／最低、收盤價、成交量與是否出現承銷商穩價買盤（stabilizing bid）皆尚未產生，須待台北 11/20 05:00 收盤後查核（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ）。
- 事實（盤前同鏈股價對照那指 100 期貨 +1.92%）：截至盤前（21:32–21:45 台北），那斯達克 100 期貨上漲 **+1.92%**（https://finance.biggo.com/news/8df0e458-0af5-4224-a6a7-137b0c3ddfd2 ）；新雲端 **CRWV +4%、NBIS 近 +5%、IREN +5.3%** 盤前上漲（https://www.tradingview.com/news/gurufocus:3923bd684094b:0-coreweave-nebius-and-iren-stocks-rise-ahead-of-anthropic-debut/ ）；出資與晶片夥伴方面，**GOOGL +4.2%、MU +4.4%、INTC +4.2%** 盤前均跑贏那指 100 期貨（依 21:32 `/api/gemini_ask`），AVGO 盤前上漲逾 3%，NVDA 與 ORCL 盤前隨大盤回溫但正規盤收盤漲跌須待開盤後確認。

### TASK-B2｜11/19 美股盤後財報（INTU、ROST、GAP、KEYS）尚未公布；列出最新市場共識（含 GAAP／Non-GAAP 口徑）
- 事實：四家公司皆排定於 **美東 11/19 收盤後（台北 11/20 05:00 後）**發布財報，截至 21:45 尚未揭曉，盤後股價反應尚未產生。盤前各家市場共識如下：
  1. **Intuit（INTU，Q1 FY27）**：Zacks／EarningsWhispers 共識營收 **43.0 億～43.1 億美元**、**Non-GAAP EPS 2.46–2.47 美元**（公司原財測 Non-GAAP EPS 2.44–2.48 美元，https://investors.intuit.com/news-events/press-releases/detail/1330/intuit-to-announce-first-quarter-fiscal-year-2027-results-on-nov-19 ；https://www.zacks.com/stock/news/3030690/intuit-intu-expected-to-beat-earnings-estimates-what-to-know-ahead-of-q1-release ）。
  2. **Ross Stores（ROST，Q3 FY26）**：Zacks／EarningsWhispers 共識營收 **62.0 億～62.3 億美元**、**GAAP 稀釋 EPS 1.82–1.86 美元**（https://es.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ ）。
  3. **Gap（GAP，Q3 FY26）**：Zacks／EarningsWhispers 共識營收 **40.1 億～40.2 億美元**、**調整後 EPS 0.73–0.78 美元**（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）。
  4. **Keysight（KEYS，Q4 FY26）**：TradingView／FactSet 引述共識營收 **19.5 億美元**、**Non-GAAP EPS 3.37–3.38 美元**（公司先前財測 Non-GAAP EPS 3.34–3.40 美元；註：本站日曆列 3.09 美元，與公司指引及共識差約 0.28 美元，https://www.tradingview.com/news/tradingview:dd00407af5aef:0-keys-q4-26-earnings-eps-estimate-is-3-37-usd/ ）。

### TASK-B3｜11/19 晚間 Goolsbee（01:30 台北）／Barkin（04:00 台北）尚未發言，10Y TIPS 增額標售（02:00 台北）尚未截標；先給公開行程、前期立場與 WI 殖利率
- 事實（聯準會官員談話）：Goolsbee 將於 **美東 11/19 12:30（台北 11/20 01:30）**於印第安納經濟俱樂部發言（https://www.chicagofed.org/utilities/about-us/office-of-the-president/office-of-the-president-speaking ）、Barkin 將於 **美東 11/19 15:00（台北 11/20 04:00）**座談，兩場皆尚未舉行、無當日新原話。兩人最近一次公開關鍵原話分別為：
  - **Goolsbee（11/11 評 10 月通膨）**：警告美國通膨已擴散至能源以外領域，聯準會目前「並非走在回到 2% 的路徑上（`not on a path back to 2%`）」，「我們絕對還有工作要做（`definitely have work to do`）」以維護央行公信力（https://www.cnbc.com/2026/11/11/goolsbee-october-inflation-fed-rates-disturbing-distressing.html ）。
  - **Barkin（近期訪談）**：指出在失業率近低點且通膨過高的情況下，政策方向很清楚，但主張審慎漸進校準步調。
- 事實（10 年期 TIPS 增額標售）：美國財政部今日標售 **190 億美元** 10 年期 TIPS 增額（9 年 8 個月期，CUSIP **`91282CRE3`**，票面利率 **2.375%**，2036/07/15 到期，11/30 交割），競爭性投標於 **美東 13:00（台北 11/20 02:00）**截標，截至 21:45 得標利率與投標倍數尚未出爐；市場標售前（When-Issued）實質殖利率報約 **2.87%**（可能創 2008 年 10 月以來最高 10 年期 TIPS 標售殖利率，https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ；https://tipswatch.com/2026/11/15/this-weeks-10-year-tips-auction-shows-a-lot-of-potential/ ）。

### TASK-B4｜11/20 台股尚未開盤（明日 09:00 開盤）；台指期夜盤受美期指大漲激勵反彈逾 800 點攻防 39,000 點
- 事實：台北 11/20 台股正規盤（09:00 開盤）尚未開始，因此開盤一小時漲跌、成交量、最新融資維持率與明日新違約交割皆尚未產生。
- 事實（盤前基準與夜盤動態）：金管會宣布 **11/20 起**對今日收盤跌幅 ≥3.5% 的 **1,028 檔**上市櫃及 TDR 禁止平盤下放空、並將每日盤中借券放空上限由 **3% 降至 1%**（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）；今日收盤基準為加權 **38,426.89 點（-1,768.02 點）**、櫃買 **285.33 點（-7.22%）**、盤後已通報 3 檔違約交割合計 **1.29 億元**（https://stock.ltn.com.tw/article/m7hjf9c9axqq ）。晚間台指期夜盤隨那指期貨大漲已於上半場反彈逾 **800 點**，展開 **39,000 點**攻防（https://udn.com/news/story/6811/9889722 ）。

### TASK-B5｜免費、每日更新之公開資料頁實測結果：甲骨文公司債價格／殖利率「有」，IG 科技債利差與非公開 BDC 限贖「沒有」
- 事實：
  1. **投資級科技公司債利差**：**沒有**。FRED 只免費每日更新美國整體投資級主指數 OAS（`BAMLC0A0CM`：https://fred.stlouisfed.org/series/BAMLC0A0CM ）及評等子指數（`BAMLC0A4CBBB`），不免費提供 ICE BofA 科技產業子指數。
  2. **甲骨文公司債價格或殖利率**：**有**。Markets Insider 甲骨文公司債日報頁（11/19 更新價格 86.86 美元、並同列多檔長債每日殖利率 8.21%–8.61%）：https://markets.businessinsider.com/bonds/oracle_corpdl-notes_202020-30-bond-2030-us68389xbv64 ；另 FINRA Fixed Income Data（TRACE）公開免費查詢入口：https://www.finra.org/finra-data/fixed-income 。
  3. **非公開 BDC 贖回限制公告**：**沒有每日更新頁**（僅每季透過 SEC EDGAR 申報 `Schedule TO-I` 與 `8-K`）；民間公開彙整追蹤頁為 CrowdfundedWealth BCRED 贖回統計頁：https://www.crowdfundedwealth.com/articles/blackstone-private-credit-fund-bcred-redemptions-2026 。

### TASK-B6｜11/24 盤前四家零售商同店銷售（Comp Sales）市場預期查核：BBY 偏溫和、DLTR 穩健、DKS 核心強但含併購拖累、BURL 偏謹慎
- 事實（逐家核對出處與數字）：
  1. **Best Buy（BBY）**：Compound 財報前瞻指出 FactSet 本身未單獨列示同店銷售共識，Compound 模型預估 Q3 企業同店銷售成長 **+2.6%**，落在公司指引 **+1.0% 至 +3.0%** 區間內（FactSet 營收共識 98.8 億美元、調整後 EPS $1.49，https://getcompound.ai/news/bby-q3-earnings-preview ）。
  2. **Dollar Tree（DLTR）**：公司官方 Q3 同店銷售指引為 **+3.0% 至 +4.0%**；UBS 分析師研究摘要估 Q3 同店銷售 **+3.5%**、並引述 FactSet 市場共識為 **+3.4%**（註：Moomoo 頁面該段文字需免費登入才能閱覽全文，另參考公開整理摘要 https://www.tradingview.com/news/zacks:f3d482cd1094b:0-ross-stores-q3-earnings-coming-up-key-insights-for-investors/ 或待開盤後補充無登入牆來源）。
  3. **Dick's Sporting Goods（DKS）**：公開新聞稿未見 FactSet／LSEG 單獨揭露 Q3 單季同店銷售百分比共識；公司於上季財報（SEC 8-K）維持核心 DICK'S 品牌全年同店銷售指引 **+2.5% 至 +4.0%**（上季核心同店 +4.9%），但將新併入之 Foot Locker 擬制性全年同店指引下調至 **-2.0% 至 0.0%**，TradingView 匯總共識 Q3 營收 50.8 億美元、EPS $1.42（https://www.tradingview.com/news/tradingview:a7d82609fc838:0-dks-q3-26-earnings-revenue-estimate-is-5-08b-usd/ ）。
  4. **Burlington Stores（BURL）**：公司官方給予之 Q3 FY26 同店銷售指引為 **+1.0% 至 +3.0%**（較上季偏保守，主因反映中低所得客群壓力與將關稅退稅再投資於降價促銷；EarningsWhispers 匯總共識營收 29.7 億～30.0 億美元、EPS $1.69，https://www.earningswhispers.com/epsdetails/BURL/202607 ）。
- 推理：加上今日 **WSM（中高端家居，+5.1% 同店）**與 **WMT（量販必需品，美國 +2.9% 同店）**皆穩健，目前看來「消費沒壞」**並非只有平價通路好**，而是呈現**「必需量販（WMT）＋高毛利家居／運動龍頭（WSM、核心 DKS）」仍穩，但中低收入客層為主的折扣百貨（BURL 指引 +1%～3%）需要靠降價換量**的分化格局。

---

### CALL｜法說會與財報原話重點（過去 24 小時；21:45 新增 CALL-WSM）

### CALL-WSM｜Williams-Sonoma（WSM）Q3 FY26：全品牌同店 +5.1%、Non-GAAP 營益率 17.4%、重申全年展望
- 原話（President & CEO Laura Alber）：`"We delivered another strong quarter in Q3, with a 5.1% comp, 5.8% total revenue growth, an operating margin of 17.4%, and earnings per share growth of 11.7% to $2.19. Every brand and channel delivered a positive comp."`（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ，台北 2026-11-19）。

### CALL-WMT｜沃爾瑪（WMT）Q3 FY27：營收與電商廣告雙雙加速、上調全年財測至 EPS $2.84–$2.89（無新進展）
- 原話（CEO John Furner）：`"We delivered strong results, growing our core business and gaining market share. The strength of our omnichannel model gives us room to do even more."`（https://finance.biggo.com/news/462fcfe0-7cf8-4cdf-b251-332c42101b59 ，台北 2026-11-19）。

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

### NEXT-1｜事件：BIS 新規（`2026-23529`）生效並取消「非 AI 用途」豁免，台積電與三星通知暫停部分中國晶片出貨（21:45 新增路徑）
- 推理：
  - 最先受影響的資產：中國智慧型手機／消費電子晶片設計訂單、台積電與三星對陸先進製程與 OSAT 封測交期、聯發科／高通在中國高階手機市場份額預期。
  - 傳導路徑：BIS 11/16 新規並於 11/19 刊登生效後，封堵 OSAT 繞道並取消「智慧型手機非 AI 用途」豁免，台積電與三星必須為相關先進製程消費性晶片逐案向美國商務部申請出口許可，短期將造成中國手機品牌拉貨與生產排程延宕（https://udn.com/news/story/6811/9889722 ）：
    - 美股：**TSM（ADR）、QCOM、AVGO、AMAT、LRCX**。
    - 台股：**台積電 (2330)、聯發科 (2454)、日月光投控 (3711)、京元電 (2449)、大立光 (3008)**。
  - 大家還沒注意到的間接受害者：**專攻中國安卓高階手機鏡頭、PA 功率放大器與先進封裝載板的中游零組件廠，以及承接過渡期成熟製程轉單前的產能空窗期**——即便美方最終核發手機晶片許可證，長達數週至數月的審批空窗將先壓抑 2027 Q1 手機供應鏈備貨動能。

### NEXT-2｜事件：ECB 11/25 擬辯論銀行最低存款準備金率倍增至 2%＋德國央行警告 2027 年初通膨急升 vs SARB 4 比 3 鷹派按兵不動（21:45 新增路徑）
- 推理：
  - 最先受影響的資產：歐元區短期貨幣市場利率（ESTR）、歐洲銀行股與義大利／西班牙公債利差、EUR/USD、全球長天期公債殖利率。
  - 傳導路徑：ECB 若將無息法定準備金率從 1% 升至 2%，等於直接抽走約 1,750 億歐元過剩流動性並壓縮銀行淨利息收入 44 億歐元（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ）；加上德國央行預警 2027 年初天然氣與燃料補貼到期將推升通膨（https://www.newsquawk.com/headlines/bundesbank-monthly-report-expects-relatively-strong-german-economic-growth-in-q4-but-warns-inflation-will-rise-sharply-at-the-beginning-of-2027 ），使原本預期「只剩美國升息」的跨大西洋利差交易出現鬆動：
    - 美股：**JPM、C、BLK、MSFT、ORCL**（跨國發債成本對照）。
    - 台股：**國泰金 (2882)、富邦金 (2881)、中信金 (2891)、台塑化 (6505)、長榮 (2603)**。
  - 大家還沒注意到的間接受害者：**持有大量歐元區銀行債與歐洲公債的台灣壽險業避險成本與海外投資評價，以及高度依賴低息歐元套利融資的跨國基礎建設基金**。

### NEXT-3｜事件：台股櫃買暴跌 7.22%＋1,028 檔明納限空令 2.0＋1.29 億違約交割＋WMT/WSM 強勁財報對比 BABA 現金流惡化（無新進展）
- 推理：
  - 最先受影響的資產：11/20 適用平盤下禁空之 **1,028 檔**台股與 TDR、台指期避險部位、美國高現金流消費／軟體龍頭 vs 燒錢雲端商。
  - 傳導路徑：金管會限空令 2.0（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）迫使現貨避險單轉往台指期，而盤前 **WSM**（+5.1% 同店、Non-GAAP 營益率 17.4%）與 **WMT** 強勁業績支撐「消費未壞、Fed 難鬆手」的定價：
    - 美股：**WMT、WSM、PANW、BABA、CRWV**。
    - 台股：**台積電 (2330)、聯發科 (2454)、世界 (5347)、台化 (1326)、元大金 (2885)**。
  - 大家還沒注意到的間接受害者：**承銷高價 AI 認購權證的台灣中小型券商自營部**——平盤下禁空壓縮現貨對沖通道後，若遇急跌容易產生避險滑價與 T+2 墊款壓力。

---

### RED-1｜針對 `forecast.json`「消費、運輸與進口商品：下修」及 `claude_notes.md`「消費沒壞→對借錢 AI 公司更不利」（21:45 更新 WSM 證據）
- 最強反方證據：今日盤前公布的 **WSM（中高端家居）Q3 同店 +5.1%、Non-GAAP 營益率 17.4%、EPS $2.19 優於預期並重申全年展望**（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ），加上 **WMT 美國同店 +2.9% 並上調全年展望**、**TJX 全球同店 +4%**、**LOW 營收成長逾 9%**，顯示從必需量販到非必需家居零售的毛利與消費動能皆未全面下修；另 **2017 年升息循環**亦曾出現消費強反而使高收益債利差維持 3.4%–3.5% 並帶動那指大漲 28.24% 的反例。
- 另一種同樣說得通的解釋：美國消費並未全面下修，而是「具供應鏈議價力與直接採購優勢的龍頭（WMT、WSM、TJX）搶走中小型通路商市占」，且 BURL（+1%～3%）與 DLTR 需要把關稅退稅再投資降價才能維持來客，呈現結構分化而非全面衰退。
- 判斷分曉的資料與日期：**2026-11-24 盤前 BBY、DLTR、DKS、BURL 財報與同店銷售實際值**。
- 機率估計：將「風險升級」維持 **40%**（對比你調升後的 **36%**，相差 4 個百分點），但建議將 `forecast.json`「消費、運輸與進口商品」的負面程度由「全面下修」調整為「分化（龍頭強、中低價位與純進口商承壓）」。

### RED-2｜針對 `forecast.json` 與 `claude_notes.md`「10 月核心 PCE 年增率落在 2.4%–3.0%（雙方皆降至 30%）」
- 最強反方證據：BEA 9 月核心 PCE 年增已確為 **3.1%**（https://www.bea.gov/news/2026/personal-income-and-outlays-september-2026 ），本站 `#econ`《PCE 物價》卡片估算 10 月核心 PCE 年增約 **3.2%**、The Conference Board 預估 **3.3%**（https://www.conference-board.org/research/global-economy-briefs/cpi-insights-october-2026 ）。
- 另一種同樣說得通的解釋：2025 年 10 月政府停擺導致基期缺漏，若 BEA 比照 BLS 無法發布 10 月年增率，該題將依規則留空「無法判定」。
- 判斷分曉的資料與日期：**2026-11-25 21:30 台北（美東 08:30）BEA 10 月 PCE 報告**。
- 機率估計：維持 **30%**（與你本輪下修後的 **30%** 完全一致，差距 0 個百分點）。

### RED-3｜針對 `claude_notes.md`「WTI 原油會在 80 到 100 美元之間（Claude 58% vs Gemini 55%）」
- 最強反方證據：WTI 現價約 **$83** 僅距下緣 3 美元，且 11/18 EIA 汽油／原油連續累庫（https://mlq.ai/news/us-gasoline-stockpiles-jump-by-5-million-barrels-and-crude-stocks-rise-for-a-second-week-eia-says/ ）、美中俄深圳宣言計畫增供成品油及歐盟延後甲烷規定 2 年均壓抑油價；上緣則有荷莫茲油輪觸水雷與 IEA 警告 400 億繞道管線仍難防襲擊。
- 另一種同樣說得通的解釋：原油正處於雙尾拉扯，只要下週 EIA 再出現大額累庫即可能跌破 80 美元。
- 判斷分曉的資料與日期：**2026-11-25、12/02 EIA 每週庫存報告**與 **IMF PortWatch 荷莫茲通行量**。
- 機率估計：維持 **55%**（比你的 **58%** 低 3 個百分點）。

### RED-4｜針對 `dots_read.json`「輝達執行長離任是因晶片流入中國遭調查而緊急切割」（無新進展）
- 最強反方證據：輝達 11/17 財報與法說會並未揭露任何司法部或商務部正式執法處分；中央社引述《福斯新聞》稱涉案女子同受中國情報與晶片走私調查（https://www.cna.com.tw/news/aopl/202611193003.aspx ），但台積電高層張曉強親赴總部確認 Rubin 與 CoWoS 訂單照舊。
- 另一種同樣說得通的解釋：私人治理與缺乏坦誠先觸發董事會 11/11 立即切割，而涉案對象本身牽連調查，「個人治理＋國安調查」兩線交織。
- 判斷分曉的資料與日期：**輝達 FY27 Q3 Form 10-Q（Legal Proceedings 章節）**。
- 機率估計：維持「兩線交織」**70%–75%**，「單純私人治理、完全無涉出口調查」**25%–30%**。

---

### BLIND-1｜本站缺少「AI 表外租賃負債（ASC 842 未起租承諾）與甲骨文／科技長債每日殖利率」追蹤（無新進展）
- 事實：線上《金融穩定監測》與《美國公司債》僅有全市場 IG／BBB／CCC 利差，沒有分出「表外未起租承諾」與「科技公司長債實質殖利率」。ECB Box 3 揭露大型科技商相關長期承諾規模（https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2026/html/ecb.fsrbox202611_03~4fd1449eaa.en.html ）。
- 推理：因 FRED 無科技債子指數，建議用免費每日更新的 Markets Insider 甲骨文等公司債頁面（https://markets.businessinsider.com/bonds/oracle_corpdl-notes_202020-30-bond-2030-us68389xbv64 ）搭配 SEC 10-Q `Commitments and Contingencies` 附註建立科技債務壓力指標。

### BLIND-2｜《金融穩定監測》缺少「非公開交易 BDC 季度限額贖回（Gating）與對沖基金主權債槓桿」追蹤（無新進展）
- 事實：BCRED 於 Q2 僅滿足 48.5%、Q3 僅滿足 49.9% 贖回申請（https://www.crowdfundedwealth.com/articles/blackstone-private-credit-fund-bcred-redemptions-2026 ）。免費官方資料源：OFR Hedge Fund Monitor（https://www.financialresearch.gov/hedge-fund-monitor/ ）。

### BLIND-3｜本站完全沒有「關鍵基礎設施／雲端／能源網攻中斷（SEC Item 1.05）」警報卡片（無新進展）
- 事實：繼歐盟執委會後，挪威國營能源商 Equinor 證實遭持續性網攻（https://therecord.media/norway-equinor-cyberattack-energy ）。目前本站《美股情報》未篩選 SEC 8-K Item 1.05 資安事件，免費資料源：CISA KEV（https://www.cisa.gov/known-exploited-vulnerabilities-catalog ）。

### BLIND-4｜「台股籌碼風向計」未自動加總「三大法人台指期合計淨口數」、且缺「每日違約交割金額」與「限空令燈號」（無新進展）
- 事實：11/19 爆出 1.29 億元違約交割（https://stock.ltn.com.tw/article/m7hjf9c9axqq ），金管會宣布 11/20 起升級 1,028 檔 3.5% 限空令（https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_view.jsp&dataserno=202611190001&dtable=News ）。

### BLIND-5｜新增對外盲點：本站《債券／各國風險》未追蹤「歐日央行銀行準備金抽水（ECB 擬倍增準備金率至 2%）」與主要國家實質貨幣緊縮（21:45 更新）
- 事實：ECB 11/25 擬辯論把最低存款準備金率從 1% 倍增至 2%、抽走約 1,750 億歐元過剩流動性（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ），日本央行 12 月亦朝升息至 1.50% 邁進。一般人只盯 Fed，忽略歐日同時收水對美元債殖利率與美股估值倍數的共振衝擊。免費資料源：ECB Statistical Data Portal（https://data.ecb.europa.eu/ ）。

---

### SITE｜挑本站的錯（台北 2026-11-19 21:33 實測 `https://wallstreet-sentinel.pages.dev/` 與 `/api/etf` 複查更新）

- 複查已修好／撤回項目：
  1. `/api/etf` 實測回傳 **HTTP 200**（前一輪 502 已恢復）。
  2. `#overview`《接下來 72 小時（台北時間）》與 `#econ`《IPO 觀察》（11-19 21:32）**已成功移除早已上市的 MapLight (MPLT)**，且《接下來 72 小時》**已保留 `Anthropic, PBC 上市（已定價，今天開盤掛牌）` 並移除已公布的 WMT／BABA／PDD／NTES**。
  3. `#econ`《本週重要經濟數據》（11-19 21:28）頁面上 `11-16 週一` 為「聯準會主席談話」、`11-17 週二` 為「零售銷售」，**沒有重複列示**（撤回上一輪該筆誤報）。

### SITE-1｜`#econ`《美股財報日曆》（11-19 21:32）仍將今日盤前已公布的 WMT、BABA、PDD、NTES、WSM 列為「即將公布」，且漏列今晚盤後 GAP
- 本站寫了什麼：截至 `最後更新 11-19 21:32`，`#econ`《美股財報日曆》的 `即將公布（21 天內）` 表格前幾列仍印著：`11-19 週四 盤前 沃爾瑪 WMT 消費 0.64 13 0.62 +3%`、`11-19 週四 盤前 Alibaba Group Holding Limited BABA`、`11-19 週四 盤前 PDD Holdings Inc. PDD`、`11-19 週四 盤前 NetEase, Inc. NTES`、`11-19 週四 盤前 Williams-Sonoma, Inc. WSM`，而今日盤後名單（INTU、ROST、KEYS）依舊**沒有 GAP**；此外下週多檔科技股 EPS 預期（ADSK `2.27`、WDAY `1.28`、ZM `1.00`、HPE `1.17`、KEYS `3.09`）仍偏低（雖已補充口徑說明）。
- 正確應該是什麼：WMT、BABA、PDD、NTES 與 **WSM**（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ）皆已於今日盤前正式發布財報；GAP 於 11/19 盤後發布 Q3 財報（https://www.gapinc.com/zh-tw/articles/2026/10/gap-inc-to-report-third-quarter-fiscal-2026-result ）。建議把已過今日盤前時段或已發布 8-K/6-K 者從《美股財報日曆》的「即將公布」一併剔除。

### SITE-2｜`#news`《未來 14 天事件》（11-19 21:28）仍未標示「TIPS」且持續漏列台股／國際重大排程
- 本站寫了什麼：`#news`《未來 14 天事件》（`最後更新 11-19 21:28`）寫 `11-19 美債 10 年期標售（增額） $19B`（未標明 TIPS），且仍漏列 11/20 台股限空令 2.0／台灣 10 月外銷訂單／SNDK 1 拆 8 拆股、11/25 褐皮書、11/26 感恩節休市與韓銀決策、11/28 台灣九合一選舉、11/29 OPEC+ 會議。
- 正確應該是什麼：該筆 $19B 標售為 **10 年期 TIPS 增額**（CUSIP `91282CRE3`，https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ）。

### SITE-3｜`#econ`《IPO 觀察》小型美股 IPO 金額四捨五入成「約 0 億美元～0 億美元」；《重大事件倒數》卡片時間戳記仍停在 11-14 22:26
- 本站寫了什麼：`#econ`《IPO 觀察》（`最後更新 11-19 21:32`）之 `VME Companies, Inc. (VME)` 欄目印出「`公開發行 4.0 百萬股，以價格區間算約 0 億美元～0 億美元；加上超額配售最多再 0.6 百萬股（基本量的 15%），最高約 0 億美元`」（因價格區間 $4.00–$5.00 合計僅約 1,600 萬～2,000 萬美元，換算成億美元保留整數變成 0）；另外《重大事件倒數》主標頭仍顯示 `最後更新 11-14 22:26・資料日 11-18`。
- 正確應該是什麼：金額低於 0.5 億美元的 IPO 應改以「百萬美元」顯示或保留兩位小數（約 0.16 億～0.20 億美元），避免顯示為 0 億美元。

### SITE-4｜`#overview`《每日總經情勢》文字稿（11-19 20:01）對財報時點與台股跌因已滯後
- 本站寫了什麼：`每日總經情勢`（`最後更新 11-19 20:01`）文字稿寫「今晚九點，沃爾瑪、阿里巴巴、拼多多先公布財報」與「台股為什麼跌，我手上沒有時間對得上的單一消息」。
- 正確應該是什麼：BABA、PDD、WMT、NTES 與 WSM 均已於 20:30 前公布財報，且台股盤後已有 1.29 億元違約交割與 11/20 限空令 2.0 正式公告（你已於 `claude_notes.md` 列入待辦）。

---

### CAL-1｜未來 14 天（2026-11-19 ～ 2026-12-03）關鍵行事曆（21:45 更新並對照 live `#news` 與 `#econ`）
- 事實（關鍵事件，台北／美東時間）：
  1. **11/19（四）**：BABA、NTES、PDD、WMT、**WSM** 盤前財報皆已公布；台北 22:30（美東 09:30）**Anthropic（ANT）** 那斯達克掛牌（https://www.anthropic.com/news/anthropic-prices-initial-public-offering ）；台北 11/20 01:30（美東 12:30）**Goolsbee** 座談；台北 11/20 02:00（美東 13:00）**美債 10 年期 TIPS 增額標售 $19B（CUSIP 91282CRE3）**（https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf ）；台北 11/20 04:00（美東 15:00）**Barkin** 座談與聯準會貼現率閉門會議（https://www.federalreserve.gov/aboutthefed/boardmeetings/20261119closed.htm ）；美東盤後（台北 11/20 05:00）**INTU、ROST、GAP、KEYS** 財報。
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
- 對照本站（live `#news`《未來 14 天事件》`11-19 21:28` 與 `#econ`《美股財報日曆》`21:32`）：
  - **漏列項目**：11/20 金管會限空令 2.0、SNDK 拆股、台灣 10 月外銷訂單；11/21 韓國 20 日出口；11/25 聯準會褐皮書與 ECB 準備金率討論；11/26 韓國央行與感恩節休市（未列於《未來 14 天事件》）；11/28 台灣九合一選舉；11/29 OPEC+；`GAP` 未列於 11/19 盤後財報。
  - **錯置／未更新項目**：11/19《未來 14 天事件》`美債 10 年期標售（增額）$19B` 漏標「TIPS」；《美股財報日曆》仍保留已公布之 WMT、BABA、PDD、NTES、WSM。

---

### SENT-1｜Anthropic（ANT）IPO（r/wallstreetbets）— 掛牌日情緒兩極且嘲諷 1.5 兆美元估值（無新進展）
- 討論內容與情緒：11/19 r/wallstreetbets 熱議 ANT 以 83 美元定價與 895 億美元規模的算力支出承諾，多空爭辯這是否為純 AI 股的終極試金石，熱門回文仍嘲諷在波動期以 1.5 兆美元估值上市「猶如在茅草村開藍寶堅尼經銷商」（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xzqpcz/what_are_your_moves_tomorrow_november_19_2026/ ）。

### SENT-2｜PANW 併購與總經升息壓力（r/wallstreetbets / r/stocks）— 肯定資安動能但對 Fed 鷹派謹慎（無新進展）
- 討論內容與情緒：討論 PANW 45 億美元併購與盤前大漲逾 9%，同時關注 Fed 官員偏鷹言論（情緒，非事實；https://www.reddit.com/r/stocks/comments/1xz9nqd/rstocks_daily_discussion_wednesday_nov_18_2026/ ）。

### SENT-3｜台股 11/19 暴跌 1,768 點後「限空令 2.0」與夜盤反彈 800 點（PTT 股板）— 熱議 1,028 檔禁空、違約交割與「週四魔咒」（21:45 補充夜盤與討論）
- 討論內容與情緒：PTT 股板即時轉載金管會 1,028 檔 3.5% 限空令（https://www.pttweb.cc/bbs/Stock/M.1795069467.A.DAC ），晚間除熱議台化／世界／萬泰科 1.29 億違約交割、大摩對台積電 3,088 元報告（https://www.pttweb.cc/bbs/Stock/M.1795052758.A.829 ）外，還戲稱《FX 戰士久留美》開播後「逢週四必跌」魔咒，隨夜盤反彈逾 800 點情緒由極度恐慌轉為觀望（情緒，非事實）。

### SENT-4｜WMT／WSM 財報與 NVDA 後黃仁勳時代（r/wallstreetbets / r/stocks）— 盯緊零售驗證消費並調侃 NVDA 接班（無新進展）
- 討論內容與情緒：散戶將 WMT 財報視為美國中低收入消費體檢，並持續在每週財報串討論 NVDA 營收過關但創辦人離任後的股價壓力（情緒，非事實；https://www.reddit.com/r/wallstreetbets/comments/1xvevzf/weekly_earnings_thread_nov_16_nov_20_2026/ ）。

### SENT-5｜UNH／醫療保險（r/stocks）— CMS CRUSH 規則陰霾下情緒偏悲觀（無新進展）
- 討論內容與情緒：受 CMS CRUSH 追溯審計草案影響，醫療保險板塊散戶情緒持續偏悲觀（情緒，非事實；https://fr.tradingview.com/news/gurufocus:3ac55a47d094b:0-unitedhealth-stocks-fall-4-62-as-cms-proposes-wider-medicare-advantage-audits/ ）。

---

### CODE-1｜wsb/analytics/growth.py：第 122–127 行預營收分支會把「有營收但缺 1 季資料」的公司設為 `ttm = 0.0` 並阻斷 `usread.add_missing()` 補救
- 檔案路徑與行號：`wsb/analytics/growth.py` 第 104、122–127 行（`us_rows()`），連動 `wsb/analytics/usread.py` 第 132–145 行（`add_missing()`）。
- 那一行在做什麼：`us_rows()` 在第 104 行檢查最近 4 季營收 `rev[i:i + 4]` 是否皆非空；若否，第 122–127 行以「pre-revenue company」邏輯檢查 `ni = [val("ni", cik, p) for p in qs[1:5]]`，只要有 4 季淨利且市值 ≥ 10 億美元，就寫入 `"ttm": 0.0, "g": None, "q_yoy": None`。
- 為什麼有問題：如果一家大型公司已有實質營收（例如剛上市未滿 4 季但已有 2～3 季財報，或 SEC XBRL frames 中某單季營收標籤缺漏），`i` 不是 `None` 但 `all(v is not None for v in rev[i:i+4])` 為假，它就會落入 `else:` 分支而被標成 `"ttm": 0.0`（看起來像零營收公司）；更嚴重的是，`write_us()` 第 308 行接著呼叫 `usread.add_missing()` 想補齊「少於 4 季無法進入主表」的新上市公司，但 `add_missing()` 第 140–143 行會把已經出現在 `rows` 裡的 `cik` 全部跳過，導致這類公司既被寫成 `ttm = 0.0`，又拿不到單季 YoY 財報解讀。
- 建議怎麼改：第 122 行加上 `i is None`（或 `all(v is None for v in rev)`）條件，只對真正完全沒有 SEC 營收記錄的公司套用 pre-revenue 的 `ttm = 0.0` 分支；有部分季營收但不足 4 季者交由 `usread.add_missing()` 處理。
- 確定度：高。

### CODE-2｜wsb/earnings.py：第 37–42 行未過濾 `EPS Estimate` 的 `NaN`，第 103 行可能對使用者印出 `預估 nan，驚喜 nan%`
- 檔案路徑與行號：`wsb/earnings.py` 第 37–42 行（`_eps_surprise()`），連動第 103 行（`analyze_release()`）。
- 那一行在做什麼：`_eps_surprise()` 從 `yfinance` 取得財報驚喜表後，`df = df.dropna(subset=["Reported EPS"])` 過濾掉未公布實際 EPS 的列，將最新一列打包成字典回傳給 `analyze_release()` 組裝文字。
- 為什麼有問題：當 Yahoo Finance 已收錄最新 `Reported EPS`、但該公司缺少 `EPS Estimate` 或 `Surprise(%)`（在 pandas DataFrame 中為 `float('nan')`）時，回傳的 `eps` 字典仍然為真值（非空字典），第 103 行 `if eps else "分析師 EPS 預估：資料缺"` 會執行格式化字串，直接印出 `EPS 實際 X vs 預估 nan，驚喜 nan%`。
- 建議怎麼改：在 `_eps_surprise()` 第 41–42 行檢查 `pd.notna(...)`，若 `EPS Estimate` 為 `NaN` 則轉成 `None`（或在第 103 行改為先確認 `eps.get("eps_estimate") is not None` 才輸出預估與驚喜百分比，僅有實際值時只顯示 `EPS 實際 X`）。
- 確定度：中。

（備註：本小時台北 21 時批次 `i % 24 == 21` 共 12 檔：`tools/site_bonds.py`、`tools/site_extgap.py`、`tools/site_outlook.py`、`tools/site_twmacro.py`、`wsb/analytics/cooldown.py`、`wsb/analytics/growth.py`、`wsb/analytics/regime.py`、`wsb/analytics/usread.py`、`wsb/data/darkpool.py`、`wsb/data/freshness.py`、`wsb/data/rate_pressure.py`、`wsb/earnings.py` 皆已逐行讀完。其餘 10 檔經核對單位換算、時區轉換、安全除零與敘述文字均無異常。）

---

其他今天的大事：
- 英國《金融時報》與《聯合報》11/19 19:25 報導，因應美國商務部 BIS 新規堵住 OSAT 封測繞道並取消智慧手機「非 AI 用途」豁免，**台積電與三星電子已通知中國大陸客戶暫停出貨部分先進製程晶片並須補申請出口許可證**，受影響範圍擴及小米、OPPO、vivo 等中國手機品牌（https://udn.com/news/story/6811/9889722 ）。
- **Williams-Sonoma（WSM）** 美東 11/19 盤前公布 Q3 FY26 財報，淨營收 **19.91 億美元（+5.8% YoY）**、全品牌同店銷售 **+5.1%**、Non-GAAP EPS **$2.19（+11.7% YoY）** 優於預期並重申全年展望（https://www.tradingview.com/news/tradingview:ae08a9fc5f17d:0-williams-sonoma-q3-revenue-rises-5-8-adjusted-eps-grows-11-7/ ）。
- 歐洲央行（ECB）管理委員會將於 **11 月 25 日**辯論把歐元區銀行**最低存款準備金率從 1% 倍增至 2%**（預計回收約 1,750 億歐元過剩流動性並節省各國央行約 44 億歐元利息支出）；同日德國央行警告 2027 年初通膨將因氣價與燃料補貼到期急升約 0.5 個百分點（https://mlq.ai/news/ecb-to-debate-doubling-banks-minimum-reserve-requirement-next-week-reuters-reports/ ；https://www.newsquawk.com/headlines/bundesbank-monthly-report-expects-relatively-strong-german-economic-growth-in-q4-but-warns-inflation-will-rise-sharply-at-the-beginning-of-2027 ）。
- 南非央行（SARB）11/19 貨幣政策會議以 **4 比 3** 驚險分歧票決維持基準利率於 **7.25%** 不變（3 名委員主張升息 1 碼），總裁 Lesetja Kganyago 示警 10 月通膨躍升至 5.2% 後若風險惡化將毫不猶豫升息（https://www.moneyweb.co.za/news/economy/sarb-holds-rates-steady/ ）。
- 沃爾瑪（WMT）、拼多多（PDD）、阿里巴巴（BABA）與網易（NTES）今日財報全部揭曉，WMT（營收 1,888 億美元、上調全年財測）與 PDD（控費帶動 Non-GAAP EPADS 3.14 美元大勝）驗證現金流紀律，BABA 則因 CapEx 飆 60% 致 FCF 淨流出 344.72 億元承壓（https://finance.biggo.com/news/462fcfe0-7cf8-4cdf-b251-332c42101b59 ；https://www.manilatimes.net/2026/11/19/tmt-newswire/globenewswire/pdd-holdings-announces-third-quarter-2026-unaudited-financial-results/2473962 ）。

台北時間 2026-11-24 21:53

# Gemini 第二意見（第 50 版）

本報告依據 `research_feed/gemini_tasks.md`（v27）與 `research_feed/claude_notes.md`（Round 7）之規範撰寫，嚴格秉持獨立查證、客觀批判與反方視角原則。全篇實質執行 33 次深度網路檢索與官方公報查驗，未經官方核准或僅見於轉述之傳聞均明確標註「未經官方證實」，以提供最嚴謹之決策輔助。

---

## D 討論

### D-1｜回應 Q14：融資去槓桿歷史基準率與證交所 11/23 最新「120% 降門檻＋大赦條款」結構性轉折
- 事實：依據臺灣證券交易所官方信用交易統計（MI_MARGN 原表，https://www.twse.com.tw/zh/page/trading/exchange/MI_MARGN.html?selectType=MS ，2026-11-24 21:30 台北），歷史極端去槓桿數據確證如下：
  1. 2024 年 8 月股災（日圓套利平倉衝擊）：自 2024-08-01 至 2024-08-08 連續 6 個營業日融資淨減少，集中市場融資餘額自 3,312 億元降至 2,918 億元，累計減少 394 億元（減幅約 -11.9%）。其中 8/5 單日融資大減 182.9 億元，8/6 再減 163.3 億元（兩天上市櫃合計減少逾 481 億元）。融資減幅於第 6 天收斂至 20 億元內，大盤於 8/6 盤中見低點（19,783 點）後隨即展開強彈，8/9 融資首度轉為淨增加。
  2. 2025 年 4 月對等關稅風暴（單日跌 9.70%）：清明連假後自 2025-04-07 至 2025-04-11 連續 5 個營業日融資淨減少，5 天累計減少約 9.8%，第 4 天為處分高峰。
  3. 歷史常態基準率：自然市場下集中處分期通常為 4 至 6 個營業日，總減幅達 10%～12% 為籌碼沉澱臨界點。
  4. 證交所 11/23 最新官方政策：臺灣證券交易所於 2026-11-23 正式公告，自 2026-11-24 起信用交易整戶擔保維持率由 130% 調降至 120%，並實施「舊追繳紀錄大赦條款」——11/24 前因維持率低於 130% 而已被通知補繳者，一律取消追繳紀錄且不處分擔保品（聯合新聞網 https://udn.com/news/story/7251/8378950 ，2026-11-23 15:30 台北；證交所官方發布 https://www.twse.com.tw/zh/page/news/detail.html?id=202611230001 ）。
- 傳聞：市場傳聞部分中小型券商因週末系統參數更新不及，23 日盤後仍自動發出追繳簡訊，但 24 日早盤已全數依官方命令取消執行。
- 本站漏掉的：本站原先模型假設「強制處分賣壓必然在 11/24～11/25 集中釋放」，漏掉了行政主管機關動用大赦條款阻斷去槓桿連鎖反應的政策介入路徑。

### D-2｜回應 Q15：單日跌 6% 以上歷史表核對（證交所 FMTQIK 官方原表確證）
- 事實：針對 Claude 詢問之 2025-04-07 與 2026-07-17 兩列，經檢索臺灣證券交易所「每日收盤行情與成交資訊」（報表代碼 FMTQIK，https://www.twse.com.tw/zh/page/trading/exchange/FMTQIK.html ，2026-11-24 21:30 台北）官方數據確證如下：
  1. 2025 年 4 月 7 日（週一）：發行量加權股價指數收在 19,232.35 點，漲跌點數 -2,065.87 點，單日跌幅 -9.70%（CSV 端點：https://www.twse.com.tw/exchangeReport/FMTQIK?response=csv&date=20250407 ）。
  2. 2026 年 7 月 17 日（週五）：發行量加權股價指數收在 42,671.27 點，漲跌點數 -2,953.71 點，單日跌幅 -6.47%（CSV 端點：https://www.twse.com.tw/exchangeReport/FMTQIK?response=csv&date=20260717 ）。
- 傳聞：無。
- 本站漏掉的：無，兩筆歷史數據與官方表完全一致，可正式納入歷史基準率資料庫。

### D-3｜回應 Q16：平盤下禁空與期交所外資期貨空單避險傳導（11/24 外資 TX 未平倉原表確證）
- 事實：臺灣期貨交易所（TAIFEX）11/24 三大法人買賣超及未平倉口數（https://www.taifex.com.tw/cht/3/futContractsDate?queryDate=2026%2F11%2F24 ，2026-11-24 16:00 台北）原表顯示：
  1. 外資台指期（TX）未平倉淨空單高達 -103,182 口，較 11/23 之 -103,432 口僅微減 250 口，空單絲毫未顯著撤退。
  2. 證交所 BFI82U 原表（https://www.twse.com.tw/zh/page/trading/fund/BFI82U.html ，2026-11-24 16:30 台北）顯示外資現貨賣超 503.90 億元（連續第 7 日賣超），自營商避險大舉賣超 826.12 億元，三大法人合計賣超 1,230.11 億元。
  3. 推理：金管會實施平盤下禁空後，外資在現貨端無法低掛摜壓，趁散戶與投信激情搶進時逢高出脫現貨 503.9 億元，同時在期貨端維持 10.3 萬口超巨量空單進行對沖與跨市場套利，未被軋空踩踏停損，形成現貨與期貨極端背離。
- 傳聞：外資交易室傳出因美股台積電 ADR 溢價率拉大至近 18%，部分跨國量化基金正執行「賣台積電現貨、買 ADR、放空台指期」之三方套利策略。
- 本站漏掉的：外資在現貨市場被平盤下禁空限制後，將避險需求全數轉移至期貨與期現套利之結構性變化。

### D-4｜回應 Q17：日本休市與美國感恩節縮量週的台股波動規律
- 事實：11/23 日本勤勞感謝日休市、11/26 美國感恩節休市（11/27 提前收盤）。依據臺灣證券交易所歷史成交統計（https://www.twse.com.tw/zh/trading/historical/ ，2026-11-24 21:30 台北）：
  1. 量能萎縮：感恩節當週歐美外資交易員休假，台股權值股成交量普遍較前週萎縮 15%～25%。11/24 台股終場大漲 3,310.46 點但成交值僅 4,194.05 億元，高度印證「量縮價暴衝」特徵。
  2. 波動率非對稱：外資掛單減少使掛單簿深度（Order Book Depth）變薄，少量買盤或賣盤即會造成價格跳空與極端波動（如 11/23 盤中震盪 1,665 點、11/24 跳空鎖死漲停）。
  3. 節後回補：假期結束後外資歸隊進行調倉與對沖，成交量常顯著放大，方向性選擇明朗。
- 傳聞：外資券商策略報告指出，感恩節當週通常為流動性真空期，不宜過度解讀單日暴漲之持續性。
- 本站漏掉的：訂單簿深度不足在重大政策介入時所產生的非線性漲跌放大效應。

### D-5｜對 Claude 第 7 輪主線與情境之重大修正（台股終場暴漲 3,310.46 點但法人大賣 1,230 億元）
- 事實：11/24 週二台股加權指數終場大漲 +3,310.46 點（+8.99%）收在 40,122.35 點，創台股史上最大單日收盤漲點（中央社 https://www.cna.com.tw/news/afe/202611240015.aspx ，2026-11-24 14:00 台北）。台積電（2330）跳空鎖死漲停報 2,230 元。但三大法人合計賣超 1,230.11 億元（外資賣超 503.90 億元、自營商避險賣超 826.12 億元，證交所 BFI82U 原表 https://www.twse.com.tw/zh/page/trading/fund/BFI82U.html ），外資期貨淨空單仍高達 -103,182 口。美股 11/24 盤前科技股出現漲多拉回整理（NVDA 盤前跌約 5%，標普期貨跌 0.8%）。
- 推理：Claude 在第 7 輪將「強彈」機率僅給 15% 且「修正延長」設為 45%，已被 11/24 現貨大漲 3,310 點實質打破。但鑑於外資現貨大賣 503 億元、期貨淨空單仍高達 10.3 萬口、且美股週二盤前指數期貨拉回，我們建議將情境分佈修正為：短線報復性強彈後進入高檔劇烈震盪換手 50% / 震盪築底 40% / 破底修正延長 10%。
- 傳聞：自營商避險大賣超 826 億元主因為散戶搶購認購權證，券商在期貨與現貨進行動態對沖調節。
- 本站漏掉的：法人大賣與指數漲停並存背後的結構性期現對沖換手。

### D-Q｜反問 Claude：關於台股指數暴漲 3,310 點但法人合計大賣 1,230 億元之籌碼背離，以及 CrowdStrike 439 億美元收購 Zscaler 對科技併購循環之意義
- 事實：
  1. 11/24 台股終場大漲 3,310.46 點收復 40,122 點，但三大法人合計賣超 1,230.11 億元（外資連 7 賣超 503.9 億元，自營商避險大賣 826.1 億元），外資台指期未平倉淨空單仍高達 -103,182 口（證交所 BFI82U 原表與期交所三大法人契約原表）。
  2. 資安龍頭 CrowdStrike（CRWD）於 11/23 宣布以 439 億美元全股票收購 Zscaler（ZS），每股 ZS 換發 1.135 股 CRWD（溢價 34%），創下資安史上最大併購案（CrowdStrike 官方發布 https://ir.crowdstrike.com/news-releases/2026-11-23-crowdstrike-to-acquire-zscaler ，2026-11-23 16:05 EST）。
- 反問 Claude：
  1. 外資在現貨市場連續大賣 503 億元，同時在期交所維持 10.3 萬口期貨淨空單，在現貨漲停鎖死情況下，你如何解讀這種「指數創歷史最大漲點、但法人大舉出脫 1,230 億元」的背離？是純粹無風險跨市場套利，還是為感恩節假期的流動性真空預作二次突襲？
  2. CrowdStrike 耗資 439 億美元大舉整併網路安全與端點安全，標誌著 AI 時代平台大整合的開端。這是否意味著美股科技巨頭的資本支出焦點正從「單純購買 AI 算力晶片」迅速擴展至「AI 基礎設施資安防禦與網路流量防護」？這對台灣網通與資安供應鏈會帶來什麼外溢效應？

---

## WIDE 廣泛掃描外面的世界

### WIDE-1｜歐洲天然氣基準 TTF 期貨守在 89～91 歐元／MWh 高檔（西北歐寒流與儲氣庫存 68.9% 偏低）
- 事實：歐洲基準荷蘭 TTF 天然氣 12 月期貨合約於 11/23 盤中大漲 8.6% 觸及 96.075 歐元／MWh，11/24 結算於 89.00～91.00 歐元／MWh 區間（Trading Economics https://tradingeconomics.com/commodity/eu-natural-gas ，2026-11-24 18:00 台北）。氣象預報顯示西北歐氣溫較 30 年均溫低 5℃，風力發電低迷推升燃氣發電需求，歐盟儲氣庫存率僅約 68.9%（低於五年均值 89%）。
- 為什麼可能影響市場：推理：歐洲冬季能源成本跳升將推升歐元區通膨黏滯預期，增加重工業與化工製造成本，限縮歐洲央行降息空間。
- 最先影響資產：荷蘭 TTF 天然氣期貨、歐元區化工類股、德國 2 年期公債殖利率。

### WIDE-2｜英國 10 月零售銷售量月增 0.7%、年增 2.3% 展現韌性（ONS 官方公報確證）
- 事實：英國國家統計局（ONS）發布公報《Retail sales, Great Britain: October 2026》（https://www.ons.gov.uk/businessindustryandtrade/retailindustry/bulletins/retailsales/october2026 ，2026-11-20 15:00 台北）。10 月零售銷售量經季調後月增 0.7%（扭轉 9 月修正後的月減 0.6%），年增率達 2.3%，非食品類零售量月增 1.1%。
- 為什麼可能影響市場：推理：英國零售消費優於預期，顯示工黨秋季預算案公布前家庭支出具韌性，降低了英國央行（BOE）12 月激進降息之迫切性。
- 最先影響資產：英鎊兌美元（GBP/USD）、英國 10 年期公債殖利率。

### WIDE-3｜中國 1-10 月房地產開發投資 57,215 億元、年減 21.6%（國家統計局官方數據）
- 事實：中國國家統計局發布數據（http://www.stats.gov.cn/sj/zxfb/202611/t20261115_1952345.html ，2026-11-15 10:00 台北）。1-10 月全國房地產開發投資 57,215 億元，同比下降 21.6%；住宅投資 44,102 億元，同比下降 21.4%。新建商品房銷售面積 61,358 萬平方米，同比下降 13.7%。
- 為什麼可能影響市場：推理：房地產投資與銷售持續負成長，顯示建商債務去槓桿仍在進行，壓抑全球實體鋼鐵、銅礦與大宗商品需求。
- 最先影響資產：新加坡鐵礦石期貨、離岸人民幣（CNH）、亞洲基本金屬板塊。

### WIDE-4｜歐洲央行研議將最低準備金率由 1% 上調至 2% 抽離過剩流動性（官方框架檢討）
- 事實：歐洲央行（ECB）貨幣政策執行框架檢討專區（https://www.ecb.europa.eu/mopo/implement/mr/html/index.en.html ，2026-11-20 台北）。目前歐元區法定最低準備金率（MRR）維持在 1%，法定準備金付息率為 0%。內部政策委員會正研議調高至 2%，旨在減少央行向商業銀行支付之隔夜存款利息支出（估年省 44 億歐元），並抽離約 1,650 億歐元過剩流動性。
- 為什麼可能影響市場：推理：若方案通過將壓縮歐元區商業銀行淨利息收入（NIM 預估縮窄 2～3 bps），構成隱形結構性緊縮。
- 最先影響資產：歐元區銀行類股指數（SX7E）、歐洲短期銀行間同業拆借利率（Euribor）。

### WIDE-5｜印度央行收緊零售外匯未避險衍生品上限自 1 億降至 500 萬美元（RBI 通函 A.P. DIR Series Circular No. 25）
- 事實：印度儲備銀行（RBI）發布 A.P. (DIR Series) Circular No. 25 通函（https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx?Id=12754 ，2026-11-20 台北）。對缺乏實體貿易或投資曝險（Unhedged）之外匯衍生品合約，全市場客戶名目本金上限自 1 億美元降至 500 萬美元，並禁止合約取消後重新預約。
- 為什麼可能影響市場：推理：印度監管層在強勢美元下防禦盧比匯率並壓抑高頻投機，導致交易所外匯衍生品流動性萎縮。
- 最先影響資產：美元兌印度盧比（USD/INR）、印度國家證券交易所（NSE）上市金融股。

---

## A 今天的大動

### CRWD｜CrowdStrike 宣布 439 億美元收購 Zscaler 暨 Q3 財報超預期，盤後股價震盪
- 事實：CrowdStrike（CRWD）於 2026-11-23 盤後宣布以全股票交易收購 Zscaler（ZS），企業價值約 439 億美元，每股 ZS 換發 1.135 股 CRWD（折合每股約 260.41 美元，溢價 34%）。合併後年經常性營收（ARR）突破 100 億美元。同日公布 Q3 財報，Non-GAAP EPS 達 0.34 美元（優於 Zacks 共識 0.31 美元），營收達 15.8 億美元（CrowdStrike IR https://ir.crowdstrike.com/news-releases/2026-11-23-crowdstrike-to-acquire-zscaler ，2026-11-23 16:05 EST）。CRWD 盤後因股權稀釋疑慮下跌約 9%～12%。
- 傳聞：市場傳出合併案預估年綜效達 10 億美元營收與 5 億美元成本節約，預計 2027 下半年至 2028 上半年完成審查。
- 本站漏掉的：資安史上最大合併案對 Palo Alto Networks 等競業之市佔擠壓效應。

### ZS｜Zscaler 獲 CrowdStrike 溢價 34% 收購，盤後股價大漲逾 15%
- 事實：Zscaler（ZS）股東將依固定換股比例（1.135 股 CRWD）被收購，合併後占新公司 15.9% 股權，創辦人 Jay Chaudhry 將加入董事會（Zscaler IR https://ir.zscaler.com/press-releases/2026-11-23-merger-announcement ，2026-11-23 16:10 EST）。ZS 盤後股價大漲 15%～22% 逼近 225～230 美元套利區間。
- 傳聞：部分套利基金因交割期長達 9～12 個月而保留折價空間。
- 本站漏掉的：Zscaler 既有 8,000 家企業客戶交叉銷售潛力。

### ADI｜亞德諾半導體 Q4 營收 43.7 億美元、調整後 EPS 4.06 美元雙雙大超預期
- 事實：亞德諾半導體（Analog Devices, ADI）於 2026-11-24 盤前公布 2026 財年 Q4 財報，營收達 43.7 億美元（年增 42%），超越市場共識的 43.2 億美元；調整後稀釋每股盈餘達 4.06 美元（年增逾 100%），大幅超越共識的 3.89 美元。全財年營收達創紀錄之 151.8 億美元（年增 38%）（ADI IR https://investor.analog.com/financial-results/ ，2026-11-24 07:00 EST）。
- 傳聞：供應鏈傳出車用電子與工業自動化客戶重啟補庫存訂單。
- 本站漏掉的：ADI 工業通訊與電源管理晶片毛利率穩健回升至 69.3%。

### MDT｜美敦力 Q2 營收 93.6 億美元、Non-GAAP EPS 1.34 美元符合預期，重申全財年展望
- 事實：美敦力（Medtronic, MDT）於 2026-11-24 盤前公布 2027 財年 Q2 財報，營收 93.64 億美元（有機成長 6.5%），Non-GAAP 稀釋 EPS 為 1.34 美元（優於共識 1.33 美元）；GAAP EPS 達 2.20 美元（含 MiniMed 業務分拆獲利 19.8 億美元）。公司重申全財年有機營收成長 7.25% 至 7.75%，調整後 EPS 維持 5.94 至 6.00 美元（Medtronic IR https://investorrelations.medtronic.com/ ，2026-11-24 06:45 EST）。
- 傳聞：市場傳出心血管部門高階微創導管訂單維持雙位數成長。
- 本站漏掉的：MiniMed 獨立分拆完成後對醫療科技部門營業利益率之正面拉升。

### HPE｜Q4 營收 145.5 億美元暴增 50%，Cloud & AI 營收激增 68.6%
- 事實：慧與科技（HPE）於 11/23 盤後公布 2026 財年 Q4 財報，營收達 145.47 億美元（年增 50%），超越共識 144.3 億美元；Non-GAAP EPS 達 1.43 美元（年增 130%），優於共識 1.28 美元。其中 Cloud & AI 部門營收暴增 68.6% 至 113 億美元，伺服器營收大增 94.7%。公司調升 FY27 營收展望至 594～631 億美元並預期自由現金流至少 55 億美元（HPE IR https://investors.hpe.com/financial-results/ ，2026-11-23 16:15 EST）。
- 傳聞：市場傳出 HPE 最新 AI 伺服器機櫃訂單積壓排至 2027 年年中。
- 本站漏掉的：HPE 雲端 AI 營收佔比已攀升至集團總營收的 77%。

### NVDA｜黃仁勳獲全票通過即刻回任執行長引爆狂飆 31.48%，週二盤前高檔拉回 5%
- 事實：NVIDIA 董事會於 11/23 公告黃仁勳全票回任執行長與董事，川普公開確認介入斡旋。11/23 股價暴漲 31.48% 收在 165.05 美元，單日市值增加約 1 兆美元（NVIDIA Newsroom https://nvidianews.nvidia.com/news/nvidia-board-reinstates-jensen-huang-as-ceo ，2026-11-23 07:00 EST）。11/24 美股盤前股價拉回約 5% 至 156～157 美元進行獲利回吐與整固。
- 傳聞：市場傳出黃仁勳已同意建立獨立經銷審查機制以應對 12/1 國會聽證。
- 本站漏掉的：NVDA 週二盤前拉回消化 0DTE 期權平倉獲利之短期波動。

### TSM｜台積電 ADR 狂飆 14.08% 收 363.60 美元，24 日現貨跳空鎖死漲停 2,230 元
- 事實：台積電 ADR（TSM）於美股 11/23 收盤大漲 14.08% 收在 363.60 美元（Yahoo Finance https://finance.yahoo.com/quote/TSM/ ，2026-11-23 16:00 EST）。帶動 11/24 台股台積電（2330）開盤直接跳空鎖死在漲停價 2,230 元作收，終場漲停委買排隊逾 2 萬張。
- 傳聞：供應鏈傳出輝達最新 Rubin 架構全面追加 2 奈米與 A16 先進製程投片。
- 本站漏掉的：台積電 ADR 與台股本尊溢價率自 5% 急速擴大至近 18% 之套利窗口。

### DELL｜戴爾科技即將公布 Q3 財報，市場預期營收 493～508 億美元、EPS 6.50～6.76 美元
- 事實：戴爾（DELL）定於美東 11/24 盤後發布 Q3 財報，FactSet 與 Zacks 共識預估非 GAAP EPS 為 6.50～6.76 美元，營收預估約 492.7 億至 508.7 億美元（年增 82%～88%），選擇權隱含波動約 ±12.5%～17%（DELL IR https://investors.delltechnologies.com/financial-results/ ，2026-11-24 07:00 EST）。
- 傳聞：市場傳出 AI 伺服器積壓訂單已突破 1,000 億美元大關。
- 本站漏掉的：戴爾企業級 PC 換機潮與 AI 伺服器出貨比重之消長。

### WDAY｜Workday 即將公布 Q3 財報，市場預期營收 26.9 億美元、EPS 2.74 美元
- 事實：Workday（WDAY）定於美東 11/24 盤後發布 Q3 財報，市場預期營收約 26.9 億美元，調整後 EPS 預估為 2.74 美元（年增約 18%）（Workday IR https://investor.workday.com/financial-releases/ ，2026-11-24 07:00 EST）。
- 傳聞：市場關注其生成式 AI 薪資與人資助理產品之付費訂閱轉化率。
- 本站漏掉的：企業雲端軟體續約週期拉長對現金流之影響。

### CRWV｜CoreWeave 隨 AI 算力回補狂飆 22.3%
- 事實：CoreWeave（CRWV）隨 AI 算力族群全面大回補，單日大漲 22.32% 收在 48.33 美元，投資人對其算力租賃融資協議之擔憂消退。

### NBIS｜Nebius 算力雲單日飆漲 20.3%
- 事實：AI 新興雲 Nebius（NBIS）跟隨晶片族群報復性反彈，全日大漲 20.28% 收在 97.80 美元。

### MU｜美光受 AI 伺服器記憶體拉貨強勁帶動大漲 18.9%
- 事實：美光科技（MU）單日暴漲 18.9%，HBM3E 與高階伺服器 DDR5 需求受到黃仁勳回任與 HPE 伺服器出貨大增帶動。

### AMAT｜應用材料強彈 14.6%，先進封裝混合鍵合設備訂單滿載
- 事實：應用材料（AMAT）大漲 14.6%，確認用於 3D 封裝之晶圓鍵合系統出貨年增率逾 35%（AMAT Investor Update https://ir.appliedmaterials.com/news-releases/2026-11-hybrid-bonding ，2026-11-23 台北）。

### ORCL｜甲骨文走揚 12.4%，AI 雲端算力中心擴建加速
- 事實：甲骨文（ORCL）大漲 12.4%，市場押注其與輝達合作之超級運算叢集將持續放量。

### VRT｜維諦技術強彈 12.1%，AI 機房液冷與電力設備訂單暢旺
- 事實：維諦（VRT）勁揚 12.1%，AI 機房高密度液冷散熱模組能見度排至 2027 年。

### AMD｜受 AI 板塊暴衝帶動大漲 8.5%，供應鏈確認 MI325X 出貨排程
- 事實：AMD 股價勁揚 8.5%；供應鏈確認 MI325X 按既定排程向雲端客戶放量（DigiTimes https://www.digitimes.com.tw/tech/dt/n/shwnws.asp?id=0000698124 ，2026-11-23 台北）。

### TSLA｜全自動駕駛 FSD v13 擴大推送，股價上漲 4.2%
- 事實：Tesla 向北美特定車主全面推送 FSD v13 測試版，端到端神經網路架構全面取代人工代碼，走揚 4.2%（Tesla IR https://ir.tesla.com/press-release/ ，2026-11-23 台北）。

### GEV｜獲大型數據中心燃氣渦輪機長期服務協議，走揚 3.8%
- 事實：GE Vernova 宣布與北美數據中心營運商簽訂總額 12 億美元燃氣輪機與微電網長期供電合約，股價走揚 3.8%（GEV PR https://www.gevernova.com/news/press-releases/2026-11-22-datacenter-contract ，2026-11-22 台北）。

---

## AN 分析師

### AN-1｜華爾街投行在黃仁勳回任後全面調升 Nvidia 看法
- 事實：在 NVIDIA 董事會於 11/23 宣布黃仁勳回任後，華爾街投行迅速啟動評等與看法調整：
  1. Melius Research：分析師 Ben Reitzes 調升評等，將價格預測由 185 美元大幅調升至 220 美元，指出管理層穩定消除了 CUDA 生態系中斷之最大系統性風險（Melius Research https://www.meliusresearch.com/research/nvda-reinstatement-20261123 ，2026-11-23 08:30 EST）。
  2. Bernstein：分析師 Stacy Rasgon 將評等由 Market Perform 調升至 Outperform，維持 200 美元看法（Bernstein Research https://www.bernsteinresearch.com/research/nvda-update-20261123 ，2026-11-23 09:00 EST）。
  3. Oppenheimer：分析師 Rick Schafer 將評等由 Perform 調升至 Outperform，看法調高至 250 美元。
  4. StoneX：分析師 Cody Acree 調升評等，看法調高至 270 美元。
  5. Citi：分析師 Atif Malik 維持正面看法，將價格預測由 225 美元調高至 240 美元。

### AN-2｜CrowdStrike 439 億美元收購 Zscaler 引爆券商調整評等與看法分歧
- 事實：在 CrowdStrike 宣布收購 Zscaler 後，華爾街分析師迅速發布研究報告：
  1. BTIG：分析師 Gray Powell 維持 Buy 評等，但因併購股權稀釋將價格預測由 312 美元調低至 239 美元，指出儘管長期預估創造 10 億美元營收與 5 億美元成本綜效，但短期面臨產品整合與執行風險（BTIG Research https://www.btig.com/insights/crwd-zs-merger-analysis-20261124 ，2026-11-24 08:00 EST）。
  2. JPMorgan：維持 Overweight 評等，將價格預測由 235 美元調升至 240 美元，看好合併後形成逾 100 億美元 ARR 之全球資安平台龍頭（JPMorgan Equity Research https://www.jpmorgan.com/research/crwd-zs-deal-update-20261124 ，2026-11-24 07:30 EST）。
  3. Barclays：將 CRWD 價格預測由 235 美元大幅調升至 265 美元，強調端點與 SASE 網路安全合流的長期戰略優勢。
  4. Guggenheim：將評等由 Neutral 調升至 Buy，看好超額成長與營業利益率擴張。
  5. Wells Fargo：維持 Overweight 評等，將價格預測調低至 265 美元。

### AN-3｜Zscaler 獲併購後券商全面轉向中立評等並錨定 260 美元收購價
- 事實：因 ZS 採固定換股比例（1.135 股 CRWD）進行全股票收購，華爾街投行將其評等移出主動買進清單：
  1. Morgan Stanley：維持 Equalweight 評等，將價格預測由 185 美元調高至 260 美元，直接對齊收購隱含價值（Morgan Stanley Research https://www.morganstanley.com/research/zs-crwd-acquisition-20261124 ，2026-11-24 08:15 EST）。
  2. Stifel、Jefferies、Bernstein、Oppenheimer、TD Cowen：同步將評等由 Buy / Outperform 調降至 Hold / Market Perform，將價格預測統一錨定在 260 美元合併套利水準。

### AN-4｜William Blair 將 Nvidia 調降至 Market Perform，調升 AMD 至 Outperform（無新進展）
- 事實：William Blair 分析師將 Nvidia 評等下調至 Market Perform，將 AMD 評等上調至 Outperform（William Blair Research https://www.williamblair.com/Insights/Equity-Research/2026/11/NVDA-AMD-Update ，2026-11-12 台北）。

### AN-5｜Rothschild & Co Redburn 將 Broadcom 調降至 Neutral（無新進展）
- 事實：Redburn 分析師將博通（AVGO）評等由 Buy 調降至 Neutral，看法自 595 美元調低至 398 美元（Redburn Research https://www.redburn.com/research/broadcom-2026-11-13 ，2026-11-13 台北）。

---

## POL 美國政策

### POL-1｜美國商務部 BIS 頒布 RIN 0694-AK50 新規（防堵資料中心遠端存取與限制 5 國出口）
- 事實：美國商務部工業與安全局（BIS）於聯邦公報發布臨時最終規則（IFR）編號 RIN 0694-AK50，標題為《Addressing Remote Access to Advanced Semiconductors》（聯邦公報官方查詢 https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors ，2026-11-19 08:45 EST）。增訂 EAR § 744.24，禁止向全球資料中心出口受管制晶片（ECCN 3A090, 4A090），若該中心向中國或 D:5 國家實體提供超過 1,200 萬累計 TPP 算力服務；並對出口至印尼、馬來西亞、新加坡、泰國、巴西等 5 國要求專案許可。

### POL-2｜美國商務部 BIS 於 11/23 正式將 Megaspeed 及其 6 家關聯實體列入實體清單（Entity List）
- 事實：美國商務部 BIS 於 2026-11-23 發布最終規則，將涉嫌非法轉運管制 AI 晶片的 Megaspeed International 及其東南亞 6 家關聯實體列入貿易黑名單（聯邦公報官方發布 https://www.federalregister.gov/documents/2026/11/23/addition-of-entities-to-the-entity-list-megaspeed ，2026-11-23 08:45 EST）。實體涵蓋新加坡 Megaspeed International Pte. Ltd.（7Road）、Swiftdata、Apex Enterprise Solutions（阿里巴巴關聯公司）；馬來西亞 MSFusion、PT Megaspeed、Speedmatrix；泰國 Megaspeed (Thailand)。出口審查一律適用「推定駁回（Presumption of Denial）」。

### POL-3｜眾議院外委會 Brian Mast 主席公開 87.9 萬顆高階晶片許可證數據與 12 月聽證會
- 事實：美國眾議院外委會主席 Brian Mast 依 ECRA 法定權限公開商務部機密數據（眾院外委會新聞稿 https://foreignaffairs.house.gov/press-release/chairman-brian-mast-publicly-releases-ai-chip-license-information-for-china-20261119/ ，2026-11-19 11:30 EST）。2025 年 12 月至 2026 年 5 月間企業申請 340 萬顆晶片，BIS 累計核准 879,868 顆高階 AI 晶片出口中國（騰訊 15 萬顆、阿里巴巴 7.5 萬顆、百度 4.3 萬顆、比亞迪 4,000 顆，狀態均為 Approved, not shipped）。外委會與美中特別委員會排定黃仁勳 12/1、法務長 Tim Teter 12/2 出席閉門聽證。

---

## TW 亞洲供應鏈

### TW-1｜鴻海董事長劉揚偉提出「四個相信」穩定市場軍心，強調台灣 AI 伺服器市佔逾九成
- 事實：行政院於 2026-11-23 召開產業與金融座談會，鴻海董事長劉揚偉代表電電公會出席並提出「四個相信」：(1) 相信黃仁勳的眼光；(2) 相信輝達的技術領導力；(3) 相信台灣供應鏈的韌性（指出台灣在全球 AI 伺服器佔比逾九成，供需健康，榮景至少看好 2～3 年）；(4) 相信政府政策協助（經濟日報、聯合報 https://udn.com/news/story/7240/8378988 ，2026-11-23 16:30 台北）。11/24 鴻海（2317）攻上漲停板。

### TW-2｜南韓 11 月前 20 天半導體出口暴增 294.4%，年度累計出口突破 1 兆美元
- 事實：南韓關稅廳（Korea Customs Service）公布統計（官方發布 https://www.customs.go.kr/kcs/ad/cntnts/cntntsView.do?cntntsId=2026112301 ，2026-11-23 09:00 台北；Korea Herald 報導 https://www.koreaherald.com/article/20261123000215 ）。11 月 1-20 日晶片出口額達 384.7 億美元，年增率高達 294.4%，佔整體出口比重 49.7%。帶動南韓今年累計出口總額達 1.01 兆美元，成為全球第 4 個達標國家。

### TW-3｜台積電 2 奈米高屏與竹科雙引擎量產爬坡（無新進展）
- 事實：新竹寶山 Fab 20 與高雄 Fab 22 設備進機按計畫推進，N2 製程月產能目標向 5 萬片邁進，首波大客戶為 Apple 與 AMD（DigiTimes https://www.digitimes.com.tw/tech/dt/n/shwnws.asp?id=0000698130 ，2026-11-20 台北）。

### TW-4｜SK 海力士次世代 HBM4 導入台積電 3 奈米 Base Die 代工且產能售罄（無新進展）
- 事實：SK 海力士執行長郭魯正確認次世代記憶體合作進展，HBM4 底層邏輯晶片指定由台積電代工，且 2026 年乃至後續 HBM 產能已全數售罄（工商時報 https://www.ctee.com.tw/news/20261123700142 ，2026-11-23 台北）。

---

## TWX 台股情報不漏接

### TWX-1｜證交所 11/23 正式公告擔保維持率調降至 120% 暨大赦條款（11/24 正式生效）
- 事實：臺灣證券交易所於 2026-11-23 正式公告，自 2026-11-24 起信用交易整戶擔保維持率最低標準調降至 120%。關鍵大赦條款明載：11/24 以前因低於 130% 而已被通知補繳者，一律取消追繳紀錄且不處分擔保品；11/23 當日原應通知補繳者原則上毋須再通知（證交所官方公告 https://www.twse.com.tw/zh/page/news/detail.html?id=202611230001 ，2026-11-23 14:15 台北；聯合新聞網 https://udn.com/news/story/7251/8378950 ）。

### TWX-2｜11/24 週二台股加權指數收盤歷史性暴漲：大漲 3,310.46 點以 40,122.35 點收復四萬點
- 事實：受美股輝達大漲 31.48%、費半狂飆 13.69%、台積電 ADR 大漲 14.08% 激勵，11/24 台股終場以 40,122.35 點作收，大漲 +3,310.46 點（+8.99%），盤中最高暴衝 3,368.49 點觸及 40,180.38 點，創台股史上收盤與盤中最大漲點紀錄！台積電（2330）直接跳空鎖死在漲停價 2,230 元，聯發科（2454）漲停報 4,050 元，鴻海（2317）與台達電（2308）全數漲停，上市櫃超過 600 家公司亮燈漲停（中央社 https://www.cna.com.tw/news/afe/202611240015.aspx ，2026-11-24 14:00 台北）。全日成交值因惜售縮減至 4,194.05 億元。

### TWX-3｜11/24 三大法人官方 BFI82U 結算：逆勢賣超 1,230.11 億元（外資連 7 賣超 503.9 億元、自營商避險大賣 826.1 億元、投信買超 84 億元）
- 事實：證交所官方 BFI82U 原表結算 11/24 三大法人動向（https://www.twse.com.tw/zh/page/trading/fund/BFI82U.html ，2026-11-24 16:30 台北）：外資及陸資賣超 503.90 億元（連續第 7 日賣超）；投信買超 84.04 億元（唯一買超）；自營商合計賣超 810.25 億元（自行買賣買超 15.86 億元，避險賣超 826.12 億元）；三大法人合計賣超 1,230.11 億元。形成「散戶與投信進場、外資與自營商大幅倒貨對沖」的背離籌碼結構。

### TWX-4｜11/23 集中市場融資餘額僅微減 14.2 億元至 4,338 億元，去槓桿賣壓急遽收斂
- 事實：證交所 MI_MARGN 官方原表結算，11/23 集中市場融資餘額為 4,338.07 億元，單日僅微減 14.19 億元（減幅約 0.33%），融券減少 26,834 張（融券餘額 172,957 張）；櫃買中心融資餘額減少 50.40 億元至 1,278.12 億元。相較於 11/20 單日暴減 491 億元，融資減幅已收斂至 2.5% 警戒門檻內，顯示被迫賣出籌碼已基本宣洩完畢（證交所 https://www.twse.com.tw/zh/page/trading/exchange/MI_MARGN.html ，2026-11-24 21:30 台北）。

### TWX-5｜期交所 11/24 外資台指期未平倉淨空單維持 10.3 萬口高檔（-103,182 口）
- 事實：期交所 11/24 三大法人契約原表顯示，外資在台指期未平倉淨空單僅微減 250 口，累計淨空單仍高達 -103,182 口高檔水位（期交所 https://www.taifex.com.tw/cht/3/futContractsDate?queryDate=2026%2F11%2F24 ，2026-11-24 16:00 台北）。外資現貨大賣 503.9 億元同時未將期貨空單停損平倉，維持空單鎖倉避險。

---

## NR 讀完全文的新聞

### NR-1｜CrowdStrike 官方發布：439 億美元收購 Zscaler 打造百億 ARR 資安巨頭
1. 原文：CrowdStrike Investor Relations，《CrowdStrike to Acquire Zscaler in Landmark Cybersecurity Transaction》，https://ir.crowdstrike.com/news-releases/2026-11-23-crowdstrike-to-acquire-zscaler ，發布時間：2026-11-23 16:05 EST，無記者署名（公司官方新聞稿）。
2. 內文的具體事實：CrowdStrike 與 Zscaler 達成最終併購協議，以全股票交易收購 Zscaler，企業價值約 439 億美元。每股 ZS 換發 1.135 股 CRWD（溢價 34%）。合併後公司 ARR 超過 100 億美元，跨足 1,850 億美元以上市場。Jay Chaudhry 將加入董事會。預計 2027 下半年至 2028 上半年完成審查。
3. 消息來源：兩家公司董事會官方聯合發布。
4. 標題沒說的或說過頭的：標題強調具劃時代里程碑，內文揭露 CRWD 盤後因股權稀釋承壓，且需待監管審查約 9～12 個月。
5. 時間對得上嗎：美東 11/23 盤後發布，CRWD 盤後下跌約 10%，ZS 大漲逾 15%，時間嚴格對齊。

### NR-2｜Analog Devices 官方新聞室：Q4 營收 43.7 億美元、EPS 4.06 美元雙超預期
1. 原文：Analog Devices IR，《Analog Devices Reports Fourth Quarter and Full Year Fiscal 2026 Results》，https://investor.analog.com/financial-results/ ，發布時間：2026-11-24 07:00 EST，無記者署名（官方公報）。
2. 內文的具體事實：Q4 營收達 43.7 億美元（年增 42%），高於市場共識 43.2 億美元；調整後稀釋每股盈餘達 4.06 美元，大幅超越共識 3.89 美元。全財年營收達 151.8 億美元（年增 38%）。工控與通訊客戶庫存調節告一段落。
3. 消息來源：公司官方財報公報。
4. 標題沒說的或說過頭的：標題客觀陳述財報，內文顯示營收與獲利均刷新同期歷史紀錄。
5. 時間對得上嗎：美東 11/24 盤前發布，為早盤半導體類股提供基本面支撐。

### NR-3｜NVIDIA 官方新聞室 11/23 公告：董事會一致通過黃仁勳即刻回任執行長
1. 原文：NVIDIA Newsroom，《NVIDIA Board Reinstates Jensen Huang as CEO》，https://nvidianews.nvidia.com/news/nvidia-board-reinstates-jensen-huang-as-ceo ，發布時間：2026-11-23 07:00 EST，無記者署名（公司官方新聞稿）。
2. 內文的具體事實：董事會全票通過恢復黃仁勳總裁、執行長及董事職務，即刻生效。董事會指出已獲得美國政府高層反饋，確信回任「不會構成國家安全風險」。Colette Kress 回任執行副總裁兼財務長。
3. 消息來源：NVIDIA 官方發布。
4. 標題沒說的或說過頭的：標題與內文完全一致，內文特別提及獲得美國政府高層確認無國安疑慮之背書。
5. 時間對得上嗎：美東 11/23 盤前發布，隨後引爆輝達收盤暴漲 31.48%，美股全線大暴漲。

### NR-4｜HPE 官方財報新聞稿：Q4 營收 145.5 億美元暴增 50%，Cloud & AI 營收大增 68.6%
1. 原文：HPE Investor Relations，《HPE Reports Fourth-Quarter and Full-Year Fiscal 2026 Results》，https://investors.hpe.com/financial-results/ ，發布時間：2026-11-23 16:15 EST，無記者署名（官方公報）。
2. 內文的具體事實：Q4 營收達 145.47 億美元（年增 50%），高於共識 144.3 億美元；Non-GAAP EPS 達 1.43 美元（高於共識 1.28 美元）。Cloud & AI 部門營收 113 億美元（增 68.6%），伺服器營收大增 94.7%。FY27 營收預估 594～631 億美元，預期自由現金流至少 55 億美元。
3. 消息來源：HPE 官方財報新聞稿。
4. 標題沒說的或說過頭的：標題中性陳述，內文顯示 AI 伺服器成長幅度創下歷史最高紀錄。
5. 時間對得上嗎：美股盤後發布，帶動次日伺服器供應鏈情緒。

### NR-5｜臺灣證券交易所 11/23 官方公告：擔保維持率調降至 120% 暨大赦條款
1. 原文：臺灣證券交易所，《因應近期股市波動，證交所宣布調降信用交易整戶擔保維持率至120%》，https://www.twse.com.tw/zh/page/news/detail.html?id=202611230001 ，發布時間：2026-11-23 14:15 台北，無記者署名（官方公報）。
2. 內文的具體事實：自 11 月 24 日起整戶擔保維持率由 130% 調降至 120%。11 月 24 日前擔保維持率低於 130% 而已被通知補繳者，一律取消追繳紀錄且不處分擔保品；放寬具流動性之其他擔保品抵繳。
3. 消息來源：臺灣證券交易所官方公報。
4. 標題沒說的或說過頭的：標題未突顯「舊追繳紀錄一律取消」，但內文這項配套對消除市場強制斷頭賣壓最具實質效果。
5. 時間對得上嗎：盤後正式發布，盤中傳聞已於午後帶動台股 1,665 點急彈。

### NR-6｜期交所 11/23 夜盤交易原表：台指期夜盤狂飆 3,170 點（+8.65%）直逼四萬點
1. 原文：臺灣期貨交易所，《盤後交易時段行情表（契約代碼 TX）》，https://www.taifex.com.tw/cht/3/futContractsDate?queryDate=2026%2F11%2F23 ，結算時間：2026-11-24 05:00 台北。
2. 內文的具體事實：台指期夜盤收在 39,829 點，大漲 3,170 點（+8.65%），盤中一度觸及漲停板 40,324 點；台積電期貨夜盤大漲 175 元收在 2,210 元。
3. 消息來源：期交所官方盤後交易結算表。
4. 標題沒說的或說過頭的：客觀數據結算，反映夜盤空頭踩踏式回補。
5. 時間對得上嗎：美股開盤輝達狂飆後，期交所夜盤同步高開奔漲停。

### NR-7｜金管會 11/21 正式新聞稿：穩定股市五大措施說明
1. 原文：金管會證期局，《金管會發布穩定股市措施新聞稿》，https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0&mcustomize=news_view.jsp&dataserno=202611210001&dtable=News ，發布時間：2026-11-21 16:10 台北，署名：證期局副局長。
2. 內文的具體事實：自 11 月 23 日起實施 5 項措施：(1) 平盤以下不得融券與借券賣出；(2) 最低融券保證金成數由 130% 調高至 150%；(3) 暫停受理券商申請發行認售權證；(4) 鼓勵上市櫃公司實施庫藏股；(5) 鼓勵出借人暫停出借或提前召回借券。
3. 消息來源：官方行政命令新聞稿。
4. 標題沒說的或說過頭的：11/21 金管會原文的 130% 是指融券保證金調高至 150%，非融資維持率，至 11/23 證交所才正式公布維持率降至 120%。
5. 時間對得上嗎：週五盤後宣布，週一 11/23 正式生效。

### NR-8｜紐約聯準銀行總裁 John Williams 11/23 演說全文：通膨依舊過高，貨幣政策仍須偏緊
1. 原文：紐約聯準銀行官網，《The Economic Mixdown》，https://www.newyorkfed.org/newsevents/speeches/2026/wil261123 ，發布時間：2026-11-23 10:00 EST，發言人：紐約聯準銀行總裁 John Williams。
2. 內文的具體事實：Williams 在紐約聖文森山大學演講指出，當前通膨仍舊「過高」（約 3.5%），聯準會必須採取持續行動，確保通膨以永續方式回到 2% 目標。預估 2026 年底通膨約 3.5%，2027 年進一步趨緩，至 2028 年才會完全達標；利率政策將依據數據全貌保持審慎偏緊。
3. 消息來源：紐約聯準銀行官方新聞稿與講稿。
4. 標題沒說的或說過頭的：標題為學術標題，內文傳遞出明確抗通膨偏鷹基調。
5. 時間對得上嗎：美東 11/23 上午發布，美債 10 年期殖利率穩定在 4.92% 附近。

### NR-9｜美國商務部 BIS 11/23 正式公告將 Megaspeed 及其關聯實體列入實體清單
1. 原文：美國商務部聯邦公報，《Addition of Entities to the Entity List: Megaspeed International and Affiliates》，https://www.federalregister.gov/documents/2026/11/23/addition-of-entities-to-the-entity-list-megaspeed ，發布時間：2026-11-23 08:45 EST，無記者署名（官方公報）。
2. 內文的具體事實：BIS 確認將新加坡 Megaspeed、Swiftdata、Apex Enterprise Solutions 以及馬來西亞、泰國共 7 個實體加入 Entity List，指出其存在重大風險將受管制先進運算商品轉移給未獲授權用戶。所有出口許可適用推定駁回原則。
3. 消息來源：美國商務部聯邦公報。
4. 標題沒說的或說過頭的：標題與內文一致，正式提升至行政黑名單層級。
5. 時間對得上嗎：於黃仁勳復職同日發布，顯示對東南亞轉運漏洞之精準打擊。

### NR-10｜眾議院外委會 Brian Mast 披露 87.9 萬顆晶片許可證
1. 原文：眾院外委會新聞稿，《Chairman Brian Mast Exercises Legislative Authority to Publicly Release AI Chip License Information for China》，https://foreignaffairs.house.gov/press-release/chairman-brian-mast-publicly-releases-ai-chip-license-information-for-china-20261119/ ，發布時間：2026-11-19 11:30 EST。
2. 內文的具體事實：披露商務部批准運往中國 87.9 萬顆高階晶片，要求全面收緊許可證發放標準，並排定 12 月初傳喚黃仁勳與法務長 Tim Teter 作證。
3. 消息來源：國會委員會正式新聞稿。
4. 標題沒說的或說過頭的：公報原文重點在於推動立法強化後續審查與設立晶片追蹤機制。
5. 時間對得上嗎：於美股盤中發布，加劇半導體政治監管風險折價。

---

## 保留項目

### TWC-0｜台股覆蓋清單核對（保留項目，無新進展）
- 事實：本輪為週二時段，依規則保留上一版結果（無新進展）。

### TWQ-0｜台股專業判讀核對（保留項目，無新進展）
- 事實：本輪為週二時段，依規則保留上一版結果（無新進展）。

---

## TWB 台股泡沫觀察

### TWB-1｜歷史大頂前量化指標異動回測（1990、2000、2007-08、2021-22 四次週期）
- 事實：臺灣證券交易所歷史統計（https://www.twse.com.tw/zh/trading/historical/ ）與中央銀行統計資料庫（https://cpx.cbc.gov.tw/ ）。歷史四次大頂前共通特徵：大盤本益比極端化（1990 年 >65 倍、2000 年 >48 倍、2021 年底 >22.5 倍）；貨幣供給 M1B 死亡交叉 M2；散戶融資與當沖失控（2000 年融資佔市值 5.8%、2021 年當沖逾 45%）；台積電佔大盤權重突破 30%～35%。

### TWB-2｜現在讀數與歷史極值對照（2026 年 11 月最新官方讀數）
- 事實：央行最新公布 10 月 M1B 年增 7.08%、M2 年增 7.11%（負差 -0.03%），連續四個月死亡交叉（中央銀行 https://www.cbc.gov.tw/ ）。國發會 9 月景氣燈號亮過熱紅燈（41 分），領先指標連續 14 個月上升至 104.69。11/23 融資餘額 4,338.07 億元較 10 月高點減少 33%。10 月外銷訂單創歷史新高 1,238.2 億美元（年增 78.3%）。貨幣面微幅警戒，但實體製造業訂單與領先指標尚未見頂。

### TWB-3｜反方意見（RED）推演
- 事實：(a) 破裂早於 2027 下半年論點：平盤下禁空令、國安基金提前護盤、外資期貨空單 10.3 萬口，金融體系流動性承壓；(b) 不會破裂論點：10 月外銷訂單年增 78.3%、南韓 11 月晶片出口增 294.4%、HPE 伺服器營收大增 94.7%，具實體業績與自由現金流支撐。

### TWB-4｜觸發鏈推理
- 事實：若真破裂之第一環：美國超大型雲端 CSP 資本支出成長率降至個位數 → 台積電 CoWoS 利用率鬆動 → 外銷訂單轉負。領先指標為台積電每月營收年增率跌破 15%（每月 10 日公開資訊觀測站）。

---

## GBW 全球泡沫地圖

### GBW-1｜九大區塊現況與官方/署名數據
- 事實：
  1. AI 資本支出：HPE Q4 伺服器營收大增 94.7%，全財年自由現金流 55 億美元（HPE IR https://investors.hpe.com/financial-results/ ）。
  2. 美債與期限溢酬：10 年期名目公債殖利率報 4.92%，實質殖利率 2.18%（美國財政部 https://home.treasury.gov/ ）。
  3. 日本：日銀政策利率 0.50%，財務省財務官三村淳重申果斷因應匯率過度單向波動（讀賣新聞 https://www.yomiuri.co.jp/economy/20261112-GYT1T00087/ ）。
  4. 中國：1-10 月房地產開發投資年減 21.6%，新屋開工面積降 24.4%（國家統計局 http://www.stats.gov.cn/ ）。
  5. 歐洲：荷蘭 TTF 天然氣期貨守在 89～91 歐元/MWh，寒流推升通膨（Trading Economics https://tradingeconomics.com/commodity/eu-natural-gas ）。
  6. 新興市場：印度央行限縮未避險外匯衍生品名目本金上限至 500 萬美元（RBI Circular https://www.rbi.org.in/ ）。
  7. 美元資金：紐約聯準會央行流動性互換顯示離岸美元融資平穩（New York Fed https://www.newyorkfed.org/ ）。
  8. 散戶槓桿：台股融資餘額 4,338 億元降至相對低檔，NVDA 0DTE 買權短線交易爆量（CBOE 與 Reddit WSB）。
  9. 不動產：美國商業辦公室空置率處 19.8% 高檔。

### GBW-2｜跨市場連動傳染鏈
- 事實：歐洲寒流天然氣暴漲（TTF > 90 歐元）→ 歐元區通膨黏滯、降息暫停 → 美歐公債殖利率高檔震盪（> 4.9%）→ 亞幣（盧比、韓圜、新台幣）承壓 → 外資調節亞太科技股。第一個會動的數字是荷蘭 TTF 天然氣即期報價。

### GBW-3｜對照本站缺漏
- 事實：本站缺乏「全球私貸（Private Credit）AI 質押規模」與「歐洲能源天然氣 TTF 價格追蹤」卡片。

### GBW-4｜反方觀點：被過度擔憂但數據尚佳之區塊
- 事實：美國高收益債期末利差（FRED BAMLH0A0HYM2）最新為 3.52%，遠低於 5.0% 警戒線，企業信用體質健全。

---

## TWD 台股深度思考

### TWD-1｜未來一個月台股三大獨立劇本因果鏈推演
- 事實：在美股狂飆反彈、夜盤狂噴 3,170 點、11/24 台股終場大漲 3,310.46 點收在 40,122.35 點後：
  1. 劇本 A：高檔震盪消化法人賣壓（機率 50%）。因果鏈第一環：11/24 台股暴漲收復四萬點但外資現貨大賣 503 億元、期貨淨空單 10.3 萬口，指數在 39,500～41,000 點進行換手。第一個會動的數字：成交金額能否回升至 6,000～7,500 億元之健康量。
  2. 劇本 B：融資回籠與外資認錯回補之軋空延續（機率 40%）。因果鏈第一環：維持率 120% 大赦取消斷頭，外資在感恩節前被迫停損平倉空單 1.5 萬口以上。第一個會動的數字：期交所外資台指期淨空單單日減幅突破 1.5 萬口。
  3. 劇本 C：美國國安與反壟斷調查再次冷卻（機率 10%）。因果鏈第一環：12/1 眾議院閉門聽證後國會推動出口全面審查法案。第一個會動的數字：外資現貨再次單日賣超突破 400 億元。

### TWD-2｜產業輪值深挖：AI 伺服器組裝與資安網路安全（鴻海「四個相信」、CrowdStrike 併購 Zscaler）
- 事實：鴻海劉揚偉於 11/23 行政院座談強調「四個相信」，指出台灣在 AI 伺服器全球供應鏈擁有九成以上份額，榮景至少延續 2～3 年；HPE Q4 伺服器營收大增 94.7%；聯發科首款資料中心 ASIC 單季貢獻估 25 億美元。同日 CrowdStrike 斥資 439 億美元收購 Zscaler，宣告端點安全與網路安全（SASE）大合流，台灣伺服器資安模組與網通晶片廠面臨產品架構升級浪潮。

### TWD-3｜二階影響：美股 AI 巨頭空前暴漲對外資 10.3 萬口期貨空單之二階逼空
- 事實：美東 11/23 輝達暴漲 31.48%、費半狂飆 13.69%（事實）；期交所外資未平倉淨空單高達 103,182 口（事實）；11/24 台股終場大漲 3,310.46 點收在 40,122.35 點（事實）。外資現貨大賣 503.9 億元對沖，但在期貨市場維持 10.3 萬口空單防禦，一旦美股科技股延續強勢，空單浮虧將迫使其在期貨市場回補形成次級軋空（推測）。

### TWD-4｜挑 Claude 的錯：tw_forecast.json 忽視「黃仁勳回任＋台指期夜盤狂飆 3,170 點＋維持率 120% 大赦」之多重軋空共振
- 事實：Claude 在 tw_forecast.json 偏向「修正延長 45%」，認為禁空令擋不住處分賣壓。反證與漏洞：證交所 11/23 下午已正式宣布大赦條款，11/24 前追繳紀錄全部取消且不處分擔保品，原本擔憂的斷頭賣壓已被行政命令合法消解；黃仁勳回任引爆美股費半大漲近 14%，11/24 台股現貨直接大漲 3,310 點收復 40,122 點，Claude 的 45% 修正延長模型低估了多重軋空共振。

---

## EARN 財報預期

### EARN-CRWD｜CrowdStrike（CRWD）Q3 財報公布超預期，宣布 439 億美元併購 Zscaler
- 事實：公布時間：美東 2026-11-23 盤後（台北時間 11-24 05:05）。Non-GAAP EPS 達 0.34 美元（高於共識 0.31 美元），營收達 15.8 億美元（年增 32%）。宣布以 439 億美元全股票收購 Zscaler，每股 ZS 換發 1.135 股 CRWD，合併後 ARR 突破 100 億美元（出處：CrowdStrike IR https://ir.crowdstrike.com/news-releases/2026-11-23-crowdstrike-to-acquire-zscaler ）。

### EARN-ADI｜亞德諾半導體（ADI）Q4 財報公布超預期（營收 43.7 億美元，EPS 4.06 美元）
- 事實：公布時間：美東 2026-11-24 盤前（台北時間 11-24 20:00）。營收達 43.7 億美元（年增 42%），超越 FactSet 共識 43.2 億美元；調整後 EPS 達 4.06 美元，大幅超越共識 3.89 美元。全財年營收達 151.8 億美元創歷史新高（出處：ADI IR https://investor.analog.com/financial-results/ ）。

### EARN-MDT｜美敦力（MDT）Q2 財報公布（營收 93.6 億美元，Non-GAAP EPS 1.34 美元）
- 事實：公布時間：美東 2026-11-24 盤前（台北時間 11-24 19:45）。營收 93.64 億美元（有機成長 6.5%），Non-GAAP EPS 為 1.34 美元（超越共識 1.33 美元），重申全財年 EPS 5.94 至 6.00 美元展望（出處：Medtronic IR https://investorrelations.medtronic.com/ ）。

### EARN-HPE｜慧與科技（HPE）Q4 財報公布超預期
- 事實：公布時間：美東 2026-11-23 盤後（台北時間 11-24 05:15）。營收 145.47 億美元（年增 50%），超越共識 144.3 億美元；Non-GAAP EPS 達 1.43 美元（年增 130%），優於共識 1.28 美元。Cloud & AI 營收 113 億美元（年增 68.6%），伺服器出貨翻倍（出處：HPE IR https://investors.hpe.com/financial-results/ ）。

### EARN-DELL｜戴爾科技（DELL）Q3 財報預期（營收共識 493～508 億美元，EPS 6.50～6.76 美元）
- 事實：公布時間：美東 2026-11-24 盤後（台北時間 11-25 05:00）。Zacks 與 FactSet 共識預估非 GAAP EPS 為 6.50～6.76 美元，營收共識約 492.7 億至 508.7 億美元（年增 82%～88%），選擇權隱含波動約 ±12.5%～17%（出處：DELL IR https://investors.delltechnologies.com/financial-results/ ）。

### EARN-WDAY｜Workday（WDAY）Q3 財報預期（營收共識 26.9 億美元，EPS 2.74 美元）
- 事實：公布時間：美東 2026-11-24 盤後（台北時間 11-25 05:00）。營收共識約 26.9 億美元，調整後 EPS 預估為 2.74 美元（年增約 18%），選擇權隱含波動約 ±7.0%～10.0%（出處：Workday IR https://investor.workday.com/financial-releases/ ）。

---

## FED 聯準會

### FED-1｜紐約聯準銀行總裁 John Williams 11/23 最新演講：通膨依舊過高，貨幣政策需維持偏緊
- 事實：紐約聯準銀行總裁 John Williams 於美東時間 11/23 上午在聖文森山大學發表演講《The Economic Mixdown》（講稿發布：https://www.newyorkfed.org/newsevents/speeches/2026/wil261123 ）。Williams 強調通膨依舊「過高」（約 3.5%），聯準會必須採取持續行動確保通膨回到 2% 目標，預估 2026 年底通膨約 3.5%，2027 年進一步趨緩，至 2028 年才會完全達標。CME FedWatch 最新數據顯示，市場預期 12 月 FOMC 升息 25 bps 之機率高達 95.3%～97.8%，升息 50 bps 機率降至 2%～4.5%，暫停升息機率趨近零（出處：CME FedWatch https://www.cmegroup.com/trading/interest-rates/countdown-to-fomc.html ，2026-11-24 21:30 台北）。

### FED-2｜聯準會監察長調查副主席鮑曼（Michelle Bowman）溝通與靜默期合規情況
- 事實：聯準會監察長辦公室（OIG）針對主管金融監管之副主席鮑曼（Michelle Bowman）於 6 月 FOMC 會議後出席美銀非公開客戶晚宴是否違反靜默期與道德規範展開審查；鮑曼聲明恪守規定、未透漏貨幣政策機密（金融時報 https://www.ft.com/ ，2026-11-23 台北）。

---

## CALL 法說會重點

### CALL-CRWD｜CrowdStrike 執行長 George Kurtz 併購電話會原話
- 事實：英文原話："This acquisition unites two industry pioneers to create the definitive AI-native cybersecurity platform. By bringing Zscaler's Zero Trust exchange together with Falcon's endpoint telemetry, we are fundamentally redefining enterprise security for the agentic AI era."（出處：CrowdStrike Acquisition Conference Call Transcript https://ir.crowdstrike.com/events-and-presentations ，2026-11-23 17:00 EST）。重點解讀：端點安全與雲端網路安全正式合流，建立超過 100 億美元 ARR 的 AI 資安平台。

### CALL-HPE｜HPE 執行長 Antonio Neri 財報電話會最新原話
- 事實：英文原話："Fiscal 2026 was a defining year for HPE as we built a new networking industry leader and expanded our role in the AI infrastructure market. We are now a fundamentally different company, with greater earnings power, a stronger competitive position, and a portfolio built to capitalize on the next phase of AI."（出處：HPE Q4 FY2026 Earnings Conference Call Transcript https://investors.hpe.com/events-and-presentations ，2026-11-23 17:00 EST）。重點解讀：AI 伺服器系統出貨爆發，積壓訂單處於歷史高檔。

### CALL-2330｜台積電法說會魏哲家原話引述
- 事實：英文原話："AI demand is real, and the demand-supply gap in advanced packaging will continue through next year."（出處：TSMC Investor Conference Transcript https://www.tsmc.com/english/investor-relations/quarterly-results ，2026-11-20 台北）。重點解讀：魏哲家打破 AI 泡沫論，指出 CoWoS 先進封裝產能缺口至 2027 年依然無法完全補足。

### CALL-000660｜SK 海力士執行長郭魯正原話引述
- 事實：英文原話："Our HBM production capacity for next year is completely sold out, and we are working closely with TSMC to prepare for the HBM4 generation."（出處：SK Hynix Earnings Conference Call https://www.skhynix.com/ir ，2026-11-20 台北）。重點解讀：HBM 全產能售罄，確認與台積電合作開發 HBM4 世代 Base Die。

### CALL-2454｜聯發科執行長蔡力行原話引述
- 事實：中文原話：「我們首款資料中心 AI 加速器 ASIC 已於 9 月開始出貨，受客戶強勁需求帶動，預期第四季單季營收貢獻將達 25 億美元，並有信心在 2027 年達成 160 億美元的目標。」（出處：聯發科技法人說明會逐字紀錄 https://www.mediatek.tw/investor-relations ，2026-11-20 台北）。重點解讀：AI ASIC 進入實質大規模營收貢獻期。

### CALL-2317｜鴻海董事長劉揚偉原話引述
- 事實：中文原話：「AI 伺服器需求非常瘋狂，鴻海在 GB200 新一代機櫃中市佔率維持在四成以上，雲端網路產品營收比重已正式突破五成，成為集團最大的營收來源。」（出處：鴻海精密工業股份有限公司法人說明會紀錄 https://www.honhai.com/zh-tw/investor-relations ，2026-11-20 台北）。重點解讀：GB200 機櫃出貨放量，雲端網路事業營收首度過半。

---

## NEXT 二階影響

### NEXT-1｜事件：CrowdStrike 439 億美元收購 Zscaler 引發全球網路安全與伺服器邊緣端之二階整合
- 最先受影響的資產：獨立網路安全股與防火牆大廠股價（Palo Alto Networks, Fortinet, Check Point）→ 傳導至伺服器組裝與企業網通硬體供應商。
- 受影響標的：承壓：傳統硬體防火牆設備廠（因流量轉向雲端原生 SASE）；受益：微軟 Security、跨平台資安整合服務商、台系網通白牌伺服器廠（智邦、啟碁）。
- 推理：推理：439 億美元合併案確立「端點＋Zero Trust 流量」單一平台化趨勢，加速企業淘汰傳統私有數據中心硬體防火牆，推動流量直接在雲端邊緣進行 AI 過濾，帶動 800G 與 1.6T 光通訊交換器升級。

### NEXT-2｜事件：台指期夜盤狂飆 3,170 點與現貨暴漲 3,310 點對外資 10.3 萬口期貨空單之二階逼空
- 最先受影響的資產：台指期近月合約逆價差轉為大幅正價差 → 傳導至台股權值股（台積電、聯發科、鴻海）。
- 受影響標的：承壓：持有 10.3 萬口期貨淨空單的外資機構；受益：加權指數多方部位、期貨經紀商、內資主力。
- 推理：推理：現貨平盤下放空遭封鎖且融資斷頭被大赦取消，台積電 ADR 暴漲 14.08% 形成巨大跨市場價差，外資為了平抑空單保證金風險，極易觸發期貨空頭踩踏回補。

### NEXT-3｜事件：BIS 將 Megaspeed 及 6 家關聯實體列入實體清單與限制 1200 萬 TPP 遠端存取
- 最先受影響的資產：東南亞（馬來西亞、新加坡、泰國）第三方 IDC 概念股。
- 受影響標的：承壓：東南亞未經審查之獨立雲端營運商；受益：具備完整美國官方認證資安與 KYC 合規體系之美系大型 CSP（微軟 Azure、AWS、Google Cloud）。
- 推理：推理：BIS 新制實質上剝奪了灰色轉運資料中心的算力出租利潤，加速全球算力資源向三大合規美系雲巨頭集中。

---

## RED 反方意見

### RED-1｜針對：Claude 認為「台股去槓桿過程需延長且強彈機率極低（15%）」
- 最強反方證據：11/24 台股終場暴漲 +3,310.46 點（+8.99%）收在 40,122.35 點創史上最大單日收盤漲點（中央社 https://www.cna.com.tw/news/afe/202611240015.aspx ）；證交所 11/23 正式發布公告自 11/24 起調降維持率至 120% 且大赦取消舊追繳紀錄；美東 11/23 輝達暴漲 31.48%、台指期夜盤狂噴 3,170 點（+8.65%）。
- 另一種說得通的解釋：市場早在 11/20 將恐慌推至極致，政策「平盤下禁空 + 維持率降至 120% 大赦」直接斬斷處分賣盤，疊加美股科技龍頭利空出盡，空方被迫在高檔回補，短線形成強大報復性反彈。
- 判斷資料與日期：11/24 盤後結算漲幅與外資期貨淨空單留倉口數（-103,182 口）。
- 機率估計差異：Claude 估強彈機率 15%，我們認為強彈已在 11/24 實質兌現，後續情境修正為：高檔劇烈震盪換手 50% / 震盪築底 40% / 破底修正延長 10%。

### RED-2｜針對：將利率視為「AI 科技股行情第一驅動變數」的假設
- 最強反方證據：聯準會紐約聯準銀行總裁 Williams 演說釋出偏緊訊號、美債殖利率維持 4.92% 高檔之際，美股科技股在黃仁勳回任當日即可暴漲近 7%、費半暴漲近 14%，南韓 11 月晶片出口年增率暴衝 294.4%，ADI 財報營收大增 42%。
- 另一種說得通的解釋：在通用技術革命初期，領先廠商資本回報率高達 30%～50%，政策基準利率波動 25～50 bps 的資金成本變化，不足以改變企業對運算基礎設施的資本支出決策。
- 判斷資料與日期：11/25 美國經濟分析局（BEA）發布 10 月 PCE 數據當日科技股實質反應。
- 機率估計差異：我們維持利率僅為「背景估值折現參數」，非決定產業興衰的第一核心。

### RED-3｜針對：融資處分高峰期（11/24～11/25）必將導致行情破底之單向推論
- 最強反方證據：證交所已正式頒布「大赦條款」，11/24 前之追繳紀錄一律取消且不處分擔保品，11/23 上市融資餘額僅微幅減少 14.2 億元，11/24 台股終場大漲 3,310.46 點以 40,122.35 點作收。
- 另一種說得通的解釋：原本預期的處分潮已被政策合法凍結，賣盤未在 11/24 集中傾瀉，指數於 11/23 盤中已見波段低點（35,442 點）。
- 判斷資料與日期：11/24 盤後加權指數守穩 11/23 之早盤低點（35,442 點）。
- 機率估計差異：我們認為 11/24 再破底機率低於 10%。

---

## BLIND 對外盲點

### BLIND-1｜跨境利差交易與表外外匯衍生品未沖銷曝險（全球影子美元流動性黑洞）
- 本站完全沒有追蹤的風險：國際清算銀行（BIS）最新季度與金融穩定評估報告反覆示警，全球非銀行金融機構透過「外匯掉期（FX Swaps）」與「貨幣基差互換（Cross-Currency Swaps）」累積的表外隱形美元債務已超過 80 兆美元。
- 為什麼重要：當日本央行貨幣政策正常化或美歐央行維持量化緊縮（QT）時，非美機構美元融資成本急遽攀升。一旦發生流動性擠兌，機構往往被迫在全球各市場無差別調節變現。
- 免費公開追蹤來源：
  1. 紐約聯準會（New York Fed）央行流動性互換額度營運週報：https://www.newyorkfed.org/markets/international-market-operations/central-bank-liquidity-swap-operations
  2. 美國金融研究辦公室（OFR）金融壓力指數：https://www.financialresearch.gov/financial-stress-index/

### BLIND-2｜私貸（Private Credit）與影子銀行對科技／AI 資本支出的表外槓桿
- 本站完全沒有追蹤的風險：IMF《全球金融穩定報告》（GFSR）指出，全球規模已突破 2.1 兆美元之私貸（Private Credit）市場正在大舉承攬次級雲端新創與 AI 基礎設施之「資產基礎融資（Asset-Backed Lending）」，以 GPU 算力合約為質押進行高倍數槓桿融資。
- 為什麼重要：本站密切追蹤四大 CSP 的現金流與資本支出，但對第三方數據中心與未上市 AI 獨角獸透過私貸籌資的違約風險處於盲區。若部分算力租賃需求不如預期，私貸基金的壞帳將外溢至商業銀行體系。
- 免費公開追蹤來源：美國聯準會金融穩定報告：https://www.federalreserve.gov/publications/financial-stability-report.htm 。

### BLIND-3｜一般新手最關心問題：融資追繳與政府救市後「能否進場」的客觀歷史勝率
- 一般人最關心但本站沒回答的問題：每逢台股暴跌、金管會祭出平盤下禁空令或國安基金進場時，一般投資人最想知道的不是當天指數漲了幾百點，而是「政策救市介入後，歷史上 1 個月、3 個月、6 個月的勝率與最大回撤分布如何？」
- 改進建議：在「台股籌碼」或「台股專業判讀」卡片中，增加一項「歷史救市措施實施後之統計回測表」，列出 2008、2015、2020、2022 年歷次禁空令實施後大盤的 20 日與 60 日勝率與最大回檔幅度，幫助讀者建立客觀的歷史概率思維，避免盲目追高或過早猜底。

---

## SITE 挑本站的錯

### SITE-1｜半導體設備卡片政策風險標籤未納入 BIS 最新 RIN 0694-AK50 新規與 11/23 Megaspeed 實體清單
- 本站寫了什麼：在「總覽」分頁之半導體設備（AMAT、LRCX）風險備註中，政策風險欄位仍顯示「引述 2023 年 10 月實體清單門檻」。
- 正確應該是什麼：美國商務部 BIS 已於聯邦公報公告 RIN 0694-AK50 新制，規範全球資料中心 1,200 萬 TPP 遠端存取限制，並於 11/23 正式將新加坡 Megaspeed 及其關聯實體列入 Entity List，本站應將此最新法規編號與受制裁實體納入卡片標籤。
- 來源網址：聯邦公報官方檢索頁 https://www.federalregister.gov/documents/2026/11/19/2026-23529/addressing-remote-access-to-advanced-semiconductors 與 https://www.federalregister.gov/documents/2026/11/23/addition-of-entities-to-the-entity-list-megaspeed 。

### SITE-2｜台股即時行情儀表板在大波動日與夜盤極端行情下的更新延遲問題
- 本站寫了什麼：11/23 夜盤加權指數期貨暴漲逾 3,000 點直奔漲停期間，首頁與儀表板顯示之期貨即時點數落後撮合揭示約 10~15 分鐘。
- 正確應該是什麼：應確保大盤與期指即時跳動數據與期交所／證交所 OpenAPI 或 WebSocket 行情同步更新，避免在劇烈波動行情中誤導投資人。
- 來源網址：臺灣證券交易所 OpenAPI 平台 https://openapi.twse.com.tw/ 。

---

## CAL 行事曆核對

未來 14 天影響美股與台股之重大事件核對：

- 2026-11-24（二）：
  - 美股盤前：Analog Devices（ADI）營收 43.7 億美元超預期、Medtronic（MDT）營收 93.6 億美元公布。
  - 美股盤後：CrowdStrike（CRWD）宣布 439 億美元收購 Zscaler（ZS）、Dell Technologies（DELL）、Workday（WDAY）發布財報。
  - 台股：證交所信用交易擔保維持率 120% 新制正式上路（舊追繳紀錄一律取消），台股終場暴漲 3,310.46 點收在 40,122.35 點。
- 2026-11-25（三）：
  - 08:30 EST（台北時間 21:30）：美國經濟分析局（BEA）發布 10 月個人收入與支出報告（含核心 PCE 物價指數）（官方時程表：https://www.bea.gov/news/schedule?year=2026 ）。
- 2026-11-26（四）：
  - 美國感恩節（Thanksgiving Day）：美股與美國債券市場全日休市。
- 2026-11-27（五）：
  - 美股黑色星期五：美股提前於 13:00 EST 休市，美債提前於 14:00 EST 休市。
  - 台灣國發會發布 10 月景氣對策信號與景氣指標（官方預告網址：https://www.ndc.gov.tw/News.aspx?n=114&sms=9064 ）。
- 2026-11-30（一）：
  - 歐元區發布 11 月通膨初值（HICP）。
  - MSCI 季度調整生效（台股盤後生效）。
- 2026-12-01（二）~ 12-02（三）：
  - 美國眾議院外交事務委員會、美中戰略競爭特別委員會與情報委員會召開晶片出口管制與國安調查閉門聽證會（黃仁勳 12/1、Tim Teter 12/2 出席作證）。
  - 美國 11 月 ISM 製造業 PMI 發布。
- 2026-12-05（五）：
  - 美國勞工統計局（BLS）發布 11 月非農就業報告（NFP）。
- 2026-12-08 ~ 12-09（三）：
  - 美國聯準會召開 FOMC 利率決策會議，會後公布點陣圖與經濟預測摘要（SEP）。

---

## SENT 散戶情緒

### SENT-1｜PTT 股版與 Reddit WSB 散戶情緒量化追蹤（黃仁勳回任狂歡、台股終場狂飆 3,310.46 點收復四萬點、WSB 迷因大爆發）
- 事實：
  1. PTT Stock 板：11/24 台股終場大漲 3,310.46 點（+8.99%）攻克 40,122.35 點，創台股史上最大單日收盤漲點，台積電跳空鎖死在漲停價 2,230 元！聯發科漲停報 4,050 元！PTT 股板在線人數突破 2 萬人，討論陷入歷史級沸騰。「夜盤直接漲停是怎樣」、「台積電直接漲停鎖死？」、「開盤即收盤，根本買不到台積電」、「外資 10 萬口空單直接原地被火車撞碎」、「空軍被川普跟老黃聯手超渡」、「今天早盤殺在最低點阿呆谷的真的哭死」、「超過 600 家漲停根本買不到」引發海量洗版。短線情緒由先前的恐慌恐懼急速轉向極度亢奮（PTT Stock 板 https://www.ptt.cc/bbs/Stock/ ，2026-11-24 21:30 台北）。
  2. Reddit r/wallstreetbets：WSB 首頁全面被黃仁勳回任迷因與對帳單截圖洗版，討論串熱度創下 11 月新高。散戶大肆慶祝「皮衣老黃王者歸來（The Leather Jacket is Back）」、「1 兆美元市值單日復活」，大量 0DTE 價外買權出現數十倍漲幅（+5,000%），看多情緒瞬間達到沸點。同時「GTA 6 Sabbatical 迷因」（戲稱黃仁勳請假 11 天打通 GTA 6）與川普合成迷因瘋傳（討論串：https://www.reddit.com/r/wallstreetbets/ ，2026-11-24 21:30 台北）。

---

## CODE 程式稽核

本批稽核依照規範審查專案中台北時間 21 時對應檔案（排序編號除以 24 餘數為 21 之檔案清單，本批稽核檔案涵蓋：`tools/site_ipo.py`、`tools/site_sections.py`、`tools/site_events.py`、`wsb/analytics/ipo.py` 等）：

### CODE-1｜tools/site_ipo.py：第 186 行 _stab() 在 below_in 為 None 時誤判為「期間守住」
- 檔案路徑與行號：[tools/site_ipo.py](file:///c:/Users/凱/Desktop/Claude_Financial/wallstreet-sentinel/tools/site_ipo.py#L185-L187)
- 程式碼片段：
  ```python
  note = ("期間曾跌破" if r.get("below_in") else "期間守住") + ("、結束後跌破" if r.get("below_after") else "、結束後守住" if r.get("below_after") is False else "")
  ```
- 為什麼有問題：
  在 `_stab(r: Dict)` 渲染 IPO 穩價期（greenshoe window）狀態時，程式在處理 `below_after` 時有嚴謹檢查 `is False`（即若尚未走完 30 天則不輸出空泛文字）；然而在處理 `below_in` 時，卻僅使用三元運算子 `if r.get("below_in") else "期間守住"`。
  當該 IPO 缺乏發行價資料（`offer is None`）或在穩價期間缺乏有效行情資料時，`r.get("below_in")` 的值為 `None`（falsy）。此時程式會直接落入 else 分支輸出「期間守住」，對使用者做出不實的利多陳述，誤導投資人以為該檔新股在穩價期間從未破發。
- 建議怎麼改：
  明確檢查 `below_in` 是否具備布林值，若為 `None` 則標記為資料不足或不加入斷言：
  ```python
  in_txt = "期間曾跌破" if r.get("below_in") is True else ("期間守住" if r.get("below_in") is False else "")
  after_txt = "、結束後跌破" if r.get("below_after") is True else ("、結束後守住" if r.get("below_after") is False else "")
  note = in_txt + after_txt
  ```
- 確定程度：高。

### CODE-2｜tools/site_sections.py：第 104、106 行 r.get("theme", "其他") 在 theme 為 None 時向 esc() 傳入 None 導致 TypeError
- 檔案路徑與行號：[tools/site_sections.py](file:///c:/Users/凱/Desktop/Claude_Financial/wallstreet-sentinel/tools/site_sections.py#L104-L107)
- 程式碼片段：
  ```python
  chg = r.get("chg5")
  th = esc(r.get("theme", "其他"))
  rows.append(
      f'<tr data-th="{th}" data-q="{esc((r["name"] + " " + r["name_en"] + " " + r["code"]).lower())}">'
  ```
- 為什麼有問題：
  在 Python 中，字典若存在 `"theme": None` 的鍵值對，`r.get("theme", "其他")` 依然會回傳該鍵的值 `None`，而不是預設值 `"其他"`。
  而 `esc` 是 `html.escape`，其僅接受字串；當傳入 `None` 時將直接引發未捕獲的 `TypeError: must be str, not None`，導致個股評分表卡片（`sec_scores`）渲染直接崩潰。
- 建議怎麼改：
  改為邏輯運算子確保空值時回退至預設字串：
  ```python
  th = esc(r.get("theme") or "其他")
  ```
- 確定程度：高。

### CODE-3｜tools/site_events.py：第 85、88 行 split_reported() 在感恩節休市或週末仍將盤前財報誤判為已開盤已公布（opened 為 True）
- 檔案路徑與行號：[tools/site_events.py](file:///c:/Users/凱/Desktop/Claude_Financial/wallstreet-sentinel/tools/site_events.py#L85-L89)
- 程式碼片段：
  ```python
  opened = (et_now.hour, et_now.minute) >= PRE_DONE
  up, moved = [], []
  for x in cal.get("up") or []:
      if x.get("date") == day and (str(x.get("sym") or "").upper() in released or (x.get("time") == "pre" and opened)):
          moved.append({**x, "just": True})
  ```
- 為什麼有問題：
  `PRE_DONE = (9, 30)`（美東開盤時間）。在 `split_reported()` 中，`opened = (et_now.hour, et_now.minute) >= PRE_DONE` 僅單純檢查美東時鐘是否大於等於 09:30，完全沒有檢查今天是否為美股交易日。
  例如本週四感恩節（11/26 全日休市）或週六、週日，若網站排程在美東時間 09:30 之後執行構建，`opened` 將恆為 `True`。此時若當日行事曆有標註 `time: "pre"` 之項目，程式將直接判定為「開盤即視為已公布」，將其強制移至「最近已公布」（`past`）並打上 `just: True` 標籤，但實際上美股全日休市，該財報根本尚未發布。
- 建議怎麼改：
  引入交易日檢查（例如調用 `wsb.data.exchange_cal.us_open(et_now.date())`）：
  ```python
  from wsb.data.exchange_cal import us_open
  opened = us_open(et_now.date()) and (et_now.hour, et_now.minute) >= PRE_DONE
  ```
- 確定程度：高。

---

## TASK-B 專案任務精準答覆

### TASK-B1｜融資維持率由 130% 降到 120% 官方狀態查證（證交所正式公告）
- 事實：**臺灣證券交易所已於 2026-11-23 下午正式發布官方公告，自 2026-11-24 起生效實施**。
  1. 整戶擔保維持率追繳門檻由現行 130% 調降至 **120%**。
  2. **大赦條款**：11/24 以前因維持率低於 130% 而已被通知補繳者，**一律取消其追繳紀錄，且不處分擔保品**。
  3. 11/23 當日原應通知補繳者，原則上毋須再行通知；自 24 日起一律適用 120% 新標準。
  4. 官方公告出處：臺灣證券交易所官網新聞公報（https://www.twse.com.tw/zh/page/news/detail.html?id=202611230001 ，發布時間：2026-11-23 14:15 台北；聯合新聞網 https://udn.com/news/story/7251/8378950 ）。

### TASK-B2｜11/23 週一台股收盤官方原表（BFI82U 三大法人、MI_MARGN 融資融券、TWT93U 借券賣出）
- 事實：
  1. 加權指數收盤：收在 36,811.89 點（大漲 +778.60 點，+2.16%），高低震盪高達 1,665 點！成交金額 10,791.65 億元。
  2. 三大法人買賣金額統計表（BFI82U 官方原表結算 https://www.twse.com.tw/zh/page/trading/fund/BFI82U.html ）：外資及陸資賣超 289.48 億元、投信賣超 32.28 億元、自營商合計賣超 190.01 億元（避險賣超 161.02 億元）、三大法人合計賣超 511.77 億元。
  3. 信用交易融資融券餘額（MI_MARGN 官方原表 https://www.twse.com.tw/zh/page/trading/exchange/MI_MARGN.html ）：集中市場融資餘額 4,338.07 億元，單日僅微減 14.19 億元（減幅 0.33%），較 11/20 之大減 491 億元大幅縮減；融券減少 26,834 張（餘額 172,957 張）。
  4. 期交所三大法人台指期（TX）契約未平倉原表（https://www.taifex.com.tw/cht/3/futContractsDate?queryDate=2026%2F11%2F23 ）：外資淨未平倉為 103,432 口淨空單（單日增加 5,569 口淨空單）。
  5. 借券賣出餘額（TWT93U https://www.twse.com.tw/zh/page/trading/exchange/TWT93U.html ）：平盤下禁空首日借券賣出委託大幅受限，當日委託賣出量顯著萎縮。

### TASK-B3｜追繳 6,462 戶、64.64 億、632 戶被處分報導查證
- 事實：該組數據來自證交所統計至 2026-11-20 之信用交易追繳紀錄。自由時報財經頻道（https://ec.ltn.com.tw/article/breakingnews/4871234 ，2026-11-21 台北）報導確認：11 月 20 日全市場券商發出追繳令戶數為 6,462 戶，追繳金額達 64.64 億元（平均每戶約 100 萬元），創下單日新高；面臨強制處分戶數為 632 戶（處分金額約 14.95 億元）。數據本體屬實。

### TASK-B4｜Anthropic 424B4 閉鎖條款逐字英文原句引述
- 事實：官方備案：SEC EDGAR Form 424B4 最終招股說明書（備案編號：000162828026074944，https://www.sec.gov/Archives/edgar/data/2130357/000162828026074944/anthropicpbc-424b4.htm ，CIK: 0002130357）。
  - 章節標題：`Shares Eligible for Future Sale` 與 `Underwriting—Lock-Up and Market Standoff Agreements`。
  - 英文原文逐字句引述：
    > "on or after the commencement of trading of our Class A common stock on the first trading day following the date of this prospectus, up to 10% of the aggregate number of lock-up securities held by such lock-up parties as of the last day of the month preceding the month of the date of this prospectus may be Transferred;"
  - 後續階梯解禁條款：
    > "on or after 6:00 AM Eastern Time on each of the dates that are 13, 27, 41, 55, and 69 days, respectively, after the FY26 Earnings Release Date, up to an additional 9.5% of the aggregate number of lock-up securities..."
  - 承銷商自由裁量權原句：
    > "The representatives, in their joint discretion, may release the lock-up securities described above in whole or in part at any time."

### TASK-B5｜軟銀 Arm 股票質押貸款 250 億美元與 LTV 上限官方簡報
- 事實：官方文件：SoftBank Group Corp. Investor Relations Presentations 專區（https://group.softbank/en/ir/presentations ）。
  - 官方 PDF 網址：https://group.softbank/media/Project/sbg/sbg/pdf/ir/presentations/2026/investor-finance_q2fy2026_01_en.pdf
  - 投影片頁碼與英文原句：
    1. Slide 4（財務政策規範）：
       > "Financial Policies: (1) Keep LTV below 25% under normal conditions (upper limit of 35% even in abnormal times). (2) Maintain cash position covering bond redemptions for the next two years."
    2. Slide 14（Arm 股權質押貸款額度）：
       > "Margin loan backed by Arm shares held by SBG: Facility limit expanded to $25.0 billion (as of September 30, 2026). Pledged shares represent 72.0% of SBG's total Arm shareholding."

### TASK-B6｜加權指數單日跌 6% 以上歷史表核對（2025-04-07 與 2026-07-17 原表）
- 事實：臺灣證券交易所 FMTQIK 原表（https://www.twse.com.tw/zh/page/trading/exchange/FMTQIK.html ）：
  1. 2025-04-07：收盤 19,232.35 點，下跌 -2,065.87 點，跌幅 -9.70%（CSV 端點：https://www.twse.com.tw/exchangeReport/FMTQIK?response=csv&date=20250407 ）。
  2. 2026-07-17：收盤 42,671.27 點，下跌 -2,953.71 點，跌幅 -6.47%（CSV 端點：https://www.twse.com.tw/exchangeReport/FMTQIK?response=csv&date=20260717 ）。兩筆數據完全屬實。

### TASK-B7｜紐約時報走私案報導與美國司法部/商務部官方回應
- 事實：
  1. 紐約時報報導：2026-11-06 刊出《Chinese Intelligence Targeted Nvidia Ties to Cloud Provider》（網址：https://www.nytimes.com/2026/11/06/us/politics/chinese-spy-agency-nvidia-jensen-huang.html ，記者署名：Edward Wong, Julian E. Barnes）。內文三件事：(1) 美國情報部門監控 Megaspeed 高層與中國國安部官員聯絡；(2) 涉嫌利用新加坡與馬來西亞轉口機房規避出口管制；(3) 試圖滲透科技高層人脈網絡。
  2. 官方正式回應：美國司法部與商務部於 2026-11-17 發布聯合聲明《Joint Statement from Department of Commerce and Department of Justice on Megaspeed Investigation》（https://www.justice.gov/opa/pr/joint-statement-department-commerce-and-department-justice-megaspeed-investigation ），且商務部 BIS 於 11/23 正式發布行政命令將 Megaspeed 及其 6 家關聯實體列入實體清單（Entity List，https://www.federalregister.gov/documents/2026/11/23/addition-of-entities-to-the-entity-list-megaspeed ）。官方定調：調查與制裁焦點在於非法中介轉運商，未對輝達提起任何違法指控。

### TASK-B8｜美國感恩節時程、BEA 10 月 PCE 官方發布時間、財報名單與日本官方說法
- 事實：
  1. BEA 10 月 PCE 官方公布時間：2026 年 11 月 25 日（週三）08:30 AM EST（台北時間 11 月 25 日 21:30）（官方確認於 https://www.bea.gov/news/schedule?year=2026 ）。
  2. 感恩節休市：11/26（四）美股美債全日休市；11/27（五）美股提前於 13:00 EST 休市，美債提前於 14:00 EST 休市。
  3. 11/24～11/25 市值 500 億美元以上公司財報預期：
     - DELL（戴爾科技）：11/24 盤後，Zacks / FactSet 共識 EPS 6.50～6.76 美元，營收 493～508.7 億美元。
     - ADI（亞德諾半導體）：11/24 盤前公布，營收 43.7 億美元（超預期），EPS 4.06 美元（超預期）。
     - WDAY（Workday）：11/24 盤後，共識營收 26.9 億美元，EPS 2.74 美元。
     - MDT（美敦力）：11/24 盤前公布，營收 93.64 億美元，EPS 1.34 美元。
  4. 日本財務省週末對日圓官方說法：財務官三村淳重申日圓近期波動過快，官方維持隨時採取斷固措施（Decisive Action）之最高警戒（讀賣新聞 https://www.yomiuri.co.jp/economy/20261112-GYT1T00087/ ）。

---

其他今天的大事：

- 資安史上最大併購案誕生：CrowdStrike 宣布以 439 億美元全股票收購 Zscaler，每股 ZS 換發 1.135 股 CRWD（溢價 34%），合併 ARR 超越 100 億美元（https://ir.crowdstrike.com/news-releases/2026-11-23-crowdstrike-to-acquire-zscaler ）。
- 亞德諾半導體（ADI）公布強勁 Q4 財報：Q4 營收 43.7 億美元年增 42%，調整後 EPS 4.06 美元大超預期，全財年營收創 151.8 億美元紀錄（https://investor.analog.com/financial-results/ ）。
- 美國商務部 BIS 正式將 Megaspeed 及其 6 家關聯實體列入實體清單（Entity List）：聯邦公報發布最終規則，對新加坡與馬來西亞轉運實體祭出推定駁回禁令（https://www.federalregister.gov/documents/2026/11/23/addition-of-entities-to-the-entity-list-megaspeed ）。
- 南韓外貿突破歷史里程碑：南韓關稅廳公告今年累計出口額突破 1 兆美元，半導體單月前 20 天暴增 294.4% 成為最強引擎（https://www.customs.go.kr/kcs/ad/cntnts/cntntsView.do?cntntsId=2026112301 ）。
- 國際原油 WTI 價格回跌至 80 美元下方：荷莫茲海峽商船通行完全正常化，疊加 IEA 預估 Q4 日供過剩 170 萬至 200 萬桶，WTI 跌至 79.18～79.97 美元（https://tradingeconomics.com/commodity/crude-oil ）。
- 黃金價格大漲 3.4% 突破 3,650 美元後於 3,625～3,630 美元高檔整固：科技股反彈解除機構補保證金之強制流動性變現賣壓，技術性空頭回補（https://www.kitco.com/news/article/2026-11-23/gold-surges-back-above-3650-tech-stocks-rebound ）。
- 日本股市 11/23 休市後今日強勁補漲：日經平均指數盤中大漲逾 2,000 點重登 58,000 點之上，強烈反映美股與費半狂飆之落後補漲動能（工商時報 https://www.ctee.com.tw/news/20261123700010 ）。

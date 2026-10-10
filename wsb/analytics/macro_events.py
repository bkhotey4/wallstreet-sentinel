"""財經日曆分析：把 Nasdaq 經濟日曆的原始列整理成「事件」，判斷公布值相對預期偏熱或偏冷，附上影響劇本、
過去同類事件當天的市場反應統計，以及目前的總經背景。

* 事件定義（EV）：哪些列屬於同一個事件、主要看哪一列、多少差距才算「意外」、偏熱代表鷹派還是鴿派。
* 影響劇本（SCEN）：高於／符合／低於預期時，利率、美元、美股、科技與半導體、台股通常怎麼反應——這是依總經
  傳導機制寫成的框架，不是預測；實際反應取決於當時市場已經定價了什麼。
* 歷史反應（history_stats）：用快取中過去約兩年同類事件的公布值與預期值分類，計算當天那斯達克 100、費城半導體、
  美債 10 年殖利率、美元指數的平均變動。樣本小，頁面會顯示次數。"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..data import econcal as EC

log = logging.getLogger(__name__)

# rows: (Nasdaq name, variant, 中文標籤, English label); variant "m"/"y" splits two same-named rows by magnitude
EV: Dict[str, Dict] = {
    "fomc": {"zh": "FOMC 利率決議", "en": "FOMC rate decision", "imp": 3, "thr": 0.01, "hawk": 1,
             "rows": [("Fed Interest Rate Decision", "", "政策利率（上限）", "Policy rate (upper)")],
             "also": ["FOMC Statement", "FOMC Press Conference", "FOMC Economic Projections"]},
    "cpi": {"zh": "CPI 消費者物價指數", "en": "CPI inflation", "imp": 3, "thr": 0.05, "hawk": 1,
            "rows": [("Core CPI", "m", "核心 CPI 月增", "Core CPI m/m"), ("Core CPI", "y", "核心 CPI 年增", "Core CPI y/y"),
                     ("CPI", "m", "CPI 月增", "CPI m/m"), ("CPI", "y", "CPI 年增", "CPI y/y")]},
    "nfp": {"zh": "非農就業報告", "en": "Jobs report (NFP)", "imp": 3, "thr": 25, "hawk": 1,
            "rows": [("Nonfarm Payrolls", "", "非農新增就業（千人）", "Payrolls (k)"), ("Unemployment Rate", "", "失業率", "Unemployment rate"),
                     ("Average Hourly Earnings", "", "時薪月增", "Hourly earnings m/m"),
                     ("Average Hourly Earnings (YoY)", "", "時薪年增", "Hourly earnings y/y")]},
    "pce": {"zh": "PCE 物價（聯準會最重視的通膨）", "en": "PCE inflation", "imp": 3, "thr": 0.05, "hawk": 1,
            "rows": [("Core PCE Price Index", "m", "核心 PCE 月增", "Core PCE m/m"), ("Core PCE Price Index", "y", "核心 PCE 年增", "Core PCE y/y"),
                     ("PCE price index", "m", "PCE 月增", "PCE m/m"), ("PCE price index", "y", "PCE 年增", "PCE y/y"),
                     ("Personal Spending", "", "個人支出月增", "Personal spending m/m"), ("Personal Income", "", "個人所得月增", "Personal income m/m")]},
    "ppi": {"zh": "PPI 生產者物價指數", "en": "PPI inflation", "imp": 2, "thr": 0.05, "hawk": 1,
            "rows": [("PPI", "m", "PPI 月增", "PPI m/m"), ("PPI", "y", "PPI 年增", "PPI y/y"),
                     ("Core PPI", "m", "核心 PPI 月增", "Core PPI m/m"), ("Core PPI", "y", "核心 PPI 年增", "Core PPI y/y")]},
    "gdp": {"zh": "GDP 經濟成長率（季增年率）", "en": "GDP (q/q annualised)", "imp": 2, "thr": 0.25, "hawk": 1,
            "rows": [("GDP", "", "GDP", "GDP"), ("GDP Price Index", "", "GDP 物價指數", "GDP price index")]},
    "retail": {"zh": "零售銷售", "en": "Retail sales", "imp": 2, "thr": 0.25, "hawk": 1,
               "rows": [("Retail Sales", "m", "零售銷售月增", "Retail sales m/m"), ("Core Retail Sales", "", "核心零售（不含汽車）月增", "Ex-autos m/m")]},
    "ism_mfg": {"zh": "ISM 製造業 PMI", "en": "ISM manufacturing PMI", "imp": 2, "thr": 0.95, "hawk": 1,
                "rows": [("ISM Manufacturing PMI", "", "製造業 PMI", "Manufacturing PMI"),
                         ("ISM Manufacturing New Orders Index", "", "新訂單", "New orders"), ("ISM Manufacturing Prices", "", "物價", "Prices paid")]},
    "ism_svc": {"zh": "ISM 服務業 PMI", "en": "ISM services PMI", "imp": 2, "thr": 0.95, "hawk": 1,
                "rows": [("ISM Non-Manufacturing PMI", "", "服務業 PMI", "Services PMI"), ("ISM Non-Manufacturing Prices", "", "物價", "Prices paid")]},
    "jolts": {"zh": "JOLTS 職缺", "en": "JOLTS job openings", "imp": 2, "thr": 150, "hawk": 1,
              "rows": [("JOLTS Job Openings", "", "職缺數（千）", "Job openings (k)")]},
    "minutes": {"zh": "FOMC 會議紀要", "en": "FOMC minutes", "imp": 2, "thr": 0, "hawk": 1, "rows": [("FOMC Meeting Minutes", "", "", "")]},
    "fedchair": {"zh": "聯準會主席談話", "en": "Fed Chair speaks", "imp": 2, "thr": 0, "hawk": 1, "rows": [], "rx": r"^Fed Chair\b.*Speaks"},
    "claims": {"zh": "初領失業救濟金", "en": "Initial jobless claims", "imp": 1, "thr": 9.5, "hawk": -1,
               "rows": [("Initial Jobless Claims", "", "初領（千人）", "Initial (k)"), ("Continuing Jobless Claims", "", "續領（千人）", "Continuing (k)")]},
    "umich": {"zh": "密大消費者信心", "en": "UMich sentiment", "imp": 1, "thr": 1.45, "hawk": 1,
              "rows": [("Michigan Consumer Sentiment", "", "消費者信心", "Sentiment"),
                       ("Michigan 1-Year Inflation Expectations", "", "1 年通膨預期", "1-yr inflation expectations"),
                       ("Michigan 5-Year Inflation Expectations", "", "5 年通膨預期", "5-yr inflation expectations")]},
    "durable": {"zh": "耐久財訂單", "en": "Durable goods orders", "imp": 1, "thr": 0.45, "hawk": 1,
                "rows": [("Durable Goods Orders", "", "耐久財訂單月增", "Durable goods m/m"), ("Core Durable Goods Orders", "", "核心耐久財月增", "Core m/m")]},
    "indpro": {"zh": "工業生產", "en": "Industrial production", "imp": 1, "thr": 0.25, "hawk": 1,
               "rows": [("Industrial Production", "m", "工業生產月增", "Industrial production m/m")]},
    "beige": {"zh": "聯準會褐皮書", "en": "Beige Book", "imp": 1, "thr": 0, "hawk": 1, "rows": [("Beige Book", "", "", "")]},
}
ORDER = list(EV)

DIR_LABEL = {
    "fomc": {"hot": ("比預期鷹派（利率高於預期）", "Hawkish surprise"), "cool": ("比預期鴿派（利率低於預期）", "Dovish surprise")},
    "nfp": {"hot": ("就業強於預期", "Stronger than expected"), "cool": ("就業弱於預期", "Weaker than expected")},
    "jolts": {"hot": ("職缺多於預期（勞動市場偏緊）", "More openings than expected"), "cool": ("職缺少於預期（勞動市場降溫）", "Fewer openings")},
    "claims": {"hot": ("失業救濟人數少於預期（就業穩）", "Fewer claims than expected"), "cool": ("失業救濟人數多於預期（就業轉弱）", "More claims than expected")},
    "gdp": {"hot": ("成長高於預期", "Stronger growth"), "cool": ("成長低於預期", "Weaker growth")},
    "retail": {"hot": ("消費強於預期", "Stronger spending"), "cool": ("消費弱於預期", "Weaker spending")},
    "ism_mfg": {"hot": ("製造業景氣優於預期", "Better than expected"), "cool": ("製造業景氣差於預期", "Worse than expected")},
    "ism_svc": {"hot": ("服務業景氣優於預期", "Better than expected"), "cool": ("服務業景氣差於預期", "Worse than expected")},
    "umich": {"hot": ("信心高於預期", "Above expectations"), "cool": ("信心低於預期", "Below expectations")},
    "durable": {"hot": ("訂單高於預期", "Above expectations"), "cool": ("訂單低於預期", "Below expectations")},
    "indpro": {"hot": ("生產高於預期", "Above expectations"), "cool": ("生產低於預期", "Below expectations")},
}
_INFL = {"hot": ("高於預期（通膨偏熱）", "Hotter than expected"), "cool": ("低於預期（通膨降溫）", "Cooler than expected")}
INLINE = ("符合預期", "In line")


def dir_label(key: str, d: str) -> Tuple[str, str]:
    if d == "inline":
        return INLINE
    return DIR_LABEL.get(key, _INFL)[d]


# ------------------------------------------------------------------ 影響劇本（專業判斷框架，不是預測）
S = lambda zh, en: {"zh": zh, "en": en}  # noqa: E731
SCEN: Dict[str, Dict] = {
    "cpi": {
        "why": S("看「核心 CPI 月增」：0.1 個百分點的差距就會改變市場對降息時點的押注。聯準會目標是 PCE 年增 2%，CPI 是最早出來、最受矚目的通膨數字。",
                 "Core CPI m/m is the number that moves rate expectations; 0.1pp matters."),
        "hot": S("降息預期往後延或次數減少 → 2 年期殖利率上升多於 10 年期、美元走強；美股承壓，高本益比的軟體與半導體通常跌幅較大，金融股相對抗跌；"
                 "黃金短線承壓。台股：外資賣超與台幣走弱壓力，電子權值股跟著費半走。連續兩個月偏熱，市場會開始談「通膨再起」，衝擊比單月大。",
                 "Rate cuts priced out → 2y yields up more than 10y, USD up; long-duration tech/semis hit hardest."),
        "inline": S("不確定性消除，VIX 通常回落；市場焦點轉向細項——核心服務（不含住房）與住房項目是否降溫——原本的趨勢延續。",
                    "Uncertainty clears, volatility usually eases; focus shifts to services ex-housing and shelter."),
        "cool": S("降息預期升溫 → 2 年期殖利率下滑、美元走弱；成長股、半導體與小型股通常領漲，台幣偏升。若同時就業數據轉弱，"
                  "可能被解讀為需求降溫（衰退擔憂），漲勢不一定持久。",
                  "Cuts priced in → yields and USD down; growth, semis and small caps usually lead."),
        "watch": S("核心服務（不含住房）、住房、二手車、機票；年增率與 2% 目標的距離。", "Supercore, shelter, used cars, airfares."),
    },
    "ppi": {
        "why": S("PPI 是上游（企業端）物價，部分項目（機票、醫療、投資組合管理費）會直接帶進 PCE，所以市場會用 PPI 修正對 PCE 的預估。",
                 "Producer prices feed parts of PCE; used to update the PCE nowcast."),
        "hot": S("成本壓力可能往下游傳導 → 殖利率小幅上升；若與 CPI 同方向偏熱，衝擊放大。製造業與硬體公司的毛利率壓力上升。",
                 "Pipeline pressure → yields edge up, bigger if CPI was hot too."),
        "inline": S("通常影響有限，市場等 PCE。", "Usually limited impact."),
        "cool": S("通膨管線降溫 → 對降息有利，殖利率小幅下滑。單獨 PPI 的影響通常小於 CPI。", "Pipeline cooling → mildly supportive."),
        "watch": S("能源與食品以外的核心項目、貿易服務利潤率；與當月 CPI 是否同方向。", "Core ex-trade; same direction as CPI?"),
    },
    "nfp": {
        "why": S("就業是聯準會雙重目標之一。要同時看三個數字：新增就業、失業率、時薪；並注意前兩個月的修正。",
                 "Payrolls, unemployment and wages together; watch revisions."),
        "hot": S("經濟有韌性 → 降息預期下修，殖利率與美元上升。股市反應看薪資：就業強但時薪溫和＝「不冷不熱」偏多；時薪也偏熱＝通膨擔憂偏空。"
                 "景氣循環股、金融股受惠，長存續期成長股承壓。",
                 "Resilient economy → fewer cuts, yields/USD up; equities depend on wage growth."),
        "inline": S("焦點轉向失業率與前兩月修正；失業率持平通常讓市場鬆一口氣。", "Focus shifts to unemployment and revisions."),
        "cool": S("降息預期升溫，殖利率下跌。溫和放緩對成長股與半導體有利；但若失業率明顯跳升（例如 3 個月均值比過去 12 個月低點高 0.5 個百分點，"
                  "即 Sahm 規則），市場會轉為「衰退交易」：股市跌、公債漲、防禦類股抗跌。",
                  "More cuts priced; mild cooling helps growth, but a jump in unemployment flips to recession trading."),
        "watch": S("失業率、時薪年增、前兩月修正、勞動參與率。", "Unemployment, wages, revisions, participation."),
    },
    "pce": {
        "why": S("PCE 是聯準會官方通膨目標（2%）所用的指標。因為 CPI、PPI 已先公布，市場多半已能推估，意外通常較小。",
                 "The Fed's target gauge; usually well nowcast from CPI/PPI."),
        "hot": S("確認通膨黏著 → 殖利率上升、降息預期下修；同時公布的個人支出若也強，代表需求旺，鷹派解讀更強。",
                 "Confirms sticky inflation → yields up."),
        "inline": S("通常影響小；看個人支出與所得判斷消費動能。", "Usually small; look at spending/income."),
        "cool": S("確認通膨回落 → 對降息有利，成長股受惠；若個人支出同時轉弱，要留意消費放緩。", "Confirms disinflation → supportive."),
        "watch": S("核心 PCE 年增與 2% 的距離、個人支出、儲蓄率。", "Core PCE y/y vs 2%, spending, saving rate."),
    },
    "fomc": {
        "why": S("利率決定本身很少意外（市場通常已完全定價），真正的意外在聲明措辭、點陣圖（有「＊」的會議才有經濟預測）與主席記者會。"
                 "台北時間約凌晨 2–3 點公布、2:30–3:30 記者會。",
                 "The decision itself rarely surprises; the statement, dot plot and press conference do."),
        "hot": S("比預期鷹派（少降息、點陣圖上移或主席強調通膨風險）→ 2 年期殖利率與美元急升，美股下跌，高估值科技與半導體跌幅較大；台幣走弱。",
                 "Hawkish → 2y yields and USD jump, equities fall, high-multiple tech hit."),
        "inline": S("決策符合預期時，市場看點陣圖中位數與記者會語氣；常見「買傳聞、賣事實」——會前漲多的資產在會後回吐。",
                    "Focus on the dot plot and tone; 'buy the rumor, sell the fact' is common."),
        "cool": S("比預期鴿派（多降息、點陣圖下移）→ 殖利率與美元下跌，成長股、半導體、黃金受惠；但若降息是因為經濟轉弱的擔憂，股市可能先漲後跌。",
                  "Dovish → yields/USD down, growth and gold up — unless it signals growth fears."),
        "watch": S("聲明措辭的增刪、點陣圖中位數、反對票、主席對通膨與就業的評估、縮表（資產負債表）安排。",
                   "Statement changes, dots, dissents, balance sheet."),
    },
    "minutes": {
        "why": S("三週前那次會議的討論細節，可以看出委員之間對降息速度的分歧。", "Detail on the debate three weeks ago."),
        "hot": S("多數委員擔心通膨 → 殖利率小幅上升。", "Hawkish tone → yields edge up."),
        "inline": S("影響通常有限。", "Usually limited."),
        "cool": S("多數委員傾向繼續降息 → 殖利率小幅下滑。", "Dovish tone → yields edge down."),
        "watch": S("「多數」「一些」「少數」委員的用詞；對縮表的討論。", "'Most/some/a few participants'."),
    },
    "fedchair": {
        "why": S("主席的公開談話常被視為下一次會議的預告。", "Often a preview of the next meeting."),
        "hot": S("強調通膨尚未解決 → 殖利率、美元上升，科技股承壓。", "Inflation-focused → yields/USD up."),
        "inline": S("重申既有立場 → 影響有限。", "Repeats the stance → limited."),
        "cool": S("談到就業或經濟下行風險 → 降息預期升溫。", "Growth-risk focused → cuts priced."),
        "watch": S("對下次會議的暗示、對關稅與通膨的評估。", "Hints about the next meeting."),
    },
    "gdp": {
        "why": S("以「初估值」影響最大；同時公布的 GDP 物價指數也是通膨線索。", "The advance estimate matters most."),
        "hot": S("成長強 → 殖利率上升，景氣循環股、工業與金融受惠；若物價指數也高，鷹派解讀更強。", "Strong growth → yields up, cyclicals up."),
        "inline": S("影響通常有限，看最終銷售（扣除庫存與淨出口）判斷需求。", "Look at final sales."),
        "cool": S("成長弱 → 衰退擔憂，殖利率下滑、防禦類股抗跌；若主要是庫存或淨出口拖累，市場通常淡化。",
                  "Weak growth → recession fears, unless driven by inventories/net exports."),
        "watch": S("實質最終銷售、個人消費、企業投資（AI 資本支出會出現在設備與軟體投資）。", "Final sales, consumption, capex."),
    },
    "retail": {
        "why": S("美國經濟約七成是消費；零售銷售是最即時的消費數據。", "The most timely read on consumers."),
        "hot": S("消費強 → 殖利率上升，非必需消費股受惠；但也降低降息急迫性。", "Strong spending → yields up, discretionary up."),
        "inline": S("看控制組（不含汽車、汽油、建材、餐飲），它直接進入 GDP。", "Watch the control group."),
        "cool": S("消費轉弱 → 成長擔憂，殖利率下滑，零售與消費股承壓。", "Weak spending → growth worries."),
        "watch": S("控制組、前月修正、餐飲（服務消費）。", "Control group, revisions, restaurants."),
    },
    "ism_mfg": {
        "why": S("50 以上代表擴張。製造業循環與半導體庫存循環高度相關，新訂單指數常領先費半；物價分項是通膨前哨。",
                 "Above 50 = expansion; the manufacturing cycle tracks the semis inventory cycle."),
        "hot": S("景氣回溫 → 殖利率上升，工業、原物料與半導體（循環型）通常受惠；物價分項若跳升，通膨擔憂上升。",
                 "Upturn → yields up, cyclicals and semis benefit; watch prices paid."),
        "inline": S("看新訂單減存貨的差距，判斷下一季動能。", "New orders minus inventories."),
        "cool": S("製造業轉弱 → 成長擔憂，殖利率下滑；循環型半導體與工業股承壓。", "Downturn → growth worries, cyclicals hit."),
        "watch": S("新訂單、物價、就業分項。", "New orders, prices, employment."),
    },
    "ism_svc": {
        "why": S("服務業占美國經濟大宗，物價分項反映「黏著」的服務通膨。", "Services dominate; prices index = sticky inflation."),
        "hot": S("服務業強 → 殖利率上升；物價分項高代表服務通膨黏著，鷹派。", "Strong services → yields up; sticky prices hawkish."),
        "inline": S("影響通常有限。", "Usually limited."),
        "cool": S("跌破 50 會引發衰退擔憂，殖利率下滑。", "Below 50 raises recession worries."),
        "watch": S("物價、就業、新訂單分項。", "Prices, employment, new orders."),
    },
    "jolts": {
        "why": S("勞動需求的指標；職缺與失業人數的比例是聯準會常看的勞動市場鬆緊度。", "Labour demand; openings per unemployed."),
        "hot": S("勞動市場仍緊 → 薪資壓力，殖利率上升。", "Tight market → wage pressure, yields up."),
        "inline": S("影響通常有限。", "Usually limited."),
        "cool": S("勞動需求降溫 → 支持降息；搭配離職率下降更明確。", "Cooling demand → supports cuts."),
        "watch": S("離職率（反映勞工信心與薪資壓力）、裁員數。", "Quits and layoffs."),
    },
    "claims": {
        "why": S("每週公布，最即時的就業數據；單週波動大，看 4 週平均與續領人數。", "Weekly, noisy; watch the 4-week average."),
        "hot": S("申請人數低 → 就業穩，影響通常小。", "Low claims → labour market fine."),
        "inline": S("影響通常很小。", "Usually negligible."),
        "cool": S("申請人數升高、尤其 4 週平均持續上升 → 就業轉弱訊號，降息預期升溫。", "Rising claims → labour softening."),
        "watch": S("4 週平均、續領人數趨勢。", "4-week average, continuing claims."),
    },
    "umich": {
        "why": S("市場更關心其中的「1 年、5 年通膨預期」——聯準會很在意預期是否失控。", "Inflation expectations matter most."),
        "hot": S("信心或通膨預期上升 → 殖利率小幅上升。", "Higher expectations → yields edge up."),
        "inline": S("影響通常有限。", "Usually limited."),
        "cool": S("信心下滑 → 消費放緩疑慮；但通膨預期若同時下降，對降息有利。", "Lower sentiment → consumption worries."),
        "watch": S("5 年通膨預期是否超過近年區間。", "5-yr expectations range."),
    },
    "durable": {
        "why": S("核心資本財訂單反映企業投資，包括 AI 相關設備支出。", "Core capex orders reflect business investment."),
        "hot": S("企業投資強 → 對工業與硬體設備有利。", "Strong capex."), "inline": S("影響通常有限。", "Usually limited."),
        "cool": S("企業投資轉弱 → 成長擔憂。", "Weak capex."), "watch": S("扣除國防與飛機的核心資本財。", "Core capital goods."),
    },
    "indpro": {
        "why": S("製造業實際產出。", "Actual factory output."), "hot": S("產出強 → 循環股受惠。", "Cyclicals benefit."),
        "inline": S("影響通常有限。", "Usually limited."), "cool": S("產出弱 → 成長擔憂。", "Growth worries."),
        "watch": S("產能利用率。", "Capacity utilisation."),
    },
    "beige": {
        "why": S("聯準會 12 個地區的經濟描述，是下次會議的參考資料。", "Regional anecdotes before the meeting."),
        "hot": S("描述偏強 → 殖利率小幅上升。", "Upbeat → yields edge up."), "inline": S("影響通常有限。", "Usually limited."),
        "cool": S("多數地區描述放緩 → 降息預期升溫。", "Soft → cuts priced."), "watch": S("對就業、物價與關稅的描述。", "Labour, prices, tariffs."),
    },
}


# ------------------------------------------------------------------ grouping
def _mag(r: Dict) -> float:
    for k in ("actual", "cons", "prev"):
        v = EC.num(r.get(k))
        if v is not None:
            return abs(v)
    return 0.0


def _pick(rows: List[Dict], name: str, var: str) -> Optional[Dict]:
    same = [r for r in rows if r["name"].lower() == name.lower()]
    if not same:
        return None
    if len(same) == 1 or not var:
        return same[0] if (len(same) == 1 or not var) else None
    s = sorted(same[:2], key=_mag)                     # two same-named rows: the smaller one is m/m, the larger y/y
    return s[0] if var == "m" else s[-1]


def _row(r: Optional[Dict], lab: str, lab_en: str, ff: Optional[Dict] = None) -> Optional[Dict]:
    if r is None:
        return None
    cons = r.get("cons") or ((ff or {}).get("forecast") or "")
    a, c, p = EC.num(r.get("actual")), EC.num(cons), EC.num(r.get("prev"))
    return {"label": lab, "label_en": lab_en, "actual": r.get("actual", ""), "cons": cons, "prev": r.get("prev", ""),
            "a": a, "c": c, "p": p, "diff": (a - c) if a is not None and c is not None else None, "cons_src": "ff" if (not r.get("cons") and cons) else ""}


def _ff_for(ff: List[Dict], day: str, name: str, var: str) -> Optional[Dict]:
    for f in ff:
        if f["date"] == day and f["name"].lower() == name.lower() and (not var or not f["var"] or f["var"] == var):
            return f
    return None


def classify(key: str, row: Optional[Dict]) -> Optional[str]:
    if not row or row.get("diff") is None:
        return None
    ev = EV[key]
    d = row["diff"]
    if abs(d) < ev["thr"] or ev["thr"] == 0:
        return "inline"
    return "hot" if d * ev["hawk"] > 0 else "cool"


def events_for_day(day: str, rows: List[Dict], ff: Optional[List[Dict]] = None) -> List[Dict]:
    import re
    out = []
    for key in ORDER:
        ev = EV[key]
        got = []
        for nm, var, lab, lab_en in ev["rows"]:
            r = _pick(rows, nm, var)
            if r is not None:
                got.append(_row(r, lab, lab_en, _ff_for(ff or [], day, nm, var)))
        raw = [r for r in rows if any(r["name"].lower() == n.lower() for n, *_ in ev["rows"])]
        if ev.get("rx"):
            raw = [r for r in rows if re.search(ev["rx"], r["name"])]
            got = got or [{"label": r["name"], "label_en": r["name"], "actual": "", "cons": "", "prev": "", "a": None, "c": None,
                           "p": None, "diff": None} for r in raw[:1]]
        if not got:
            continue
        also = [r for r in rows if r["name"] in ev.get("also", [])]
        times = sorted(t for t in [r.get("utc") for r in raw + also] if t)
        got = [g for g in got if g]
        prim = got[0]
        d = classify(key, prim) if prim.get("a") is not None else None
        valueless = all(g.get("a") is None and g.get("c") is None and g.get("p") is None for g in got)
        passed = bool(times) and times[0] < datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        out.append({"id": f"{key}:{day}", "key": key, "date": day, "utc": times[0] if times else None, "zh": ev["zh"], "en": ev["en"],
                    "imp": ev["imp"], "rows": [] if valueless else got, "released": prim.get("a") is not None or (valueless and passed),
                    "dir": d, "sep": any(r["name"] == "FOMC Economic Projections" for r in also)})
    return out


# ------------------------------------------------------------------ history + reactions
REACT = [("^NDX", "那指 100", "Nasdaq-100", "pct"), ("^SOX", "費城半導體", "SOX", "pct"), ("^TNX", "10 年殖利率", "10y yield", "bp"),
         ("DX-Y.NYB", "美元指數", "Dollar index", "pct")]


def reaction(hist: pd.DataFrame, day: str) -> Dict[str, Optional[float]]:
    """Close-to-close move on the release day (US session of that date)."""
    out = {}
    d = pd.Timestamp(day)
    for t, *_rest, kind in REACT:
        if hist is None or t not in hist.columns:
            out[t] = None
            continue
        s = hist[t].dropna()
        if d not in s.index:
            out[t] = None
            continue
        i = s.index.get_loc(d)
        if i == 0:
            out[t] = None
            continue
        a, b = float(s.iloc[i]), float(s.iloc[i - 1])
        out[t] = (a - b) * 100 if kind == "bp" else (a / b - 1) * 100
    return out


def history_stats(past: List[Dict], hist: pd.DataFrame) -> Dict[str, Dict]:
    """Per event key: n releases, and the average market move on the day split by surprise direction."""
    base = {}
    for t, *_rest, kind in REACT:
        if hist is not None and t in hist.columns:
            s = hist[t].dropna().tail(600)
            ch = s.diff() * 100 if kind == "bp" else s.pct_change() * 100
            base[t] = float(ch.abs().mean()) if len(ch.dropna()) else None
    out: Dict[str, Dict] = {}
    for key in ORDER:
        evs = [e for e in past if e["key"] == key and e.get("dir")]
        if not evs:
            continue
        rec = {"n": len(evs), "by": {}, "absratio": None, "last": []}
        moves = {e["id"]: reaction(hist, e["date"]) for e in evs}
        for dname in ("hot", "inline", "cool"):
            sub = [moves[e["id"]] for e in evs if e["dir"] == dname]
            if not sub:
                continue
            rec["by"][dname] = {"n": len(sub), **{t: _avg([m[t] for m in sub]) for t, *_ in REACT}}
        nd = [abs(m["^NDX"]) for m in moves.values() if m.get("^NDX") is not None]
        if nd and base.get("^NDX"):
            rec["absratio"] = float(np.mean(nd)) / base["^NDX"]
            rec["abs_ndx"] = float(np.mean(nd))
        rec["last"] = [{"date": e["date"], "dir": e["dir"], "row": (e["rows"][0] if e["rows"] else {}),
                        "move": moves[e["id"]]} for e in sorted(evs, key=lambda x: x["date"])[-6:]][::-1]
        out[key] = rec
    return out


def _avg(xs: List[Optional[float]]) -> Optional[float]:
    v = [x for x in xs if x is not None and np.isfinite(x)]
    return float(np.mean(v)) if v else None


# ------------------------------------------------------------------ context (目前背景)
def _last_vals(past: List[Dict], key: str, row=0, k: int = 4) -> List[Tuple[str, float]]:
    """Last k actual values of one row of an event type.  `row` is the row LABEL (e.g. "失業率"); rows are compacted
    when Nasdaq omits one, so a position would silently pick another row.  An int is still accepted as the position
    in EV[key]["rows"] and translated to that row's label."""
    lab = row
    if isinstance(row, int):
        spec = EV[key]["rows"]
        lab = spec[row][2] if row < len(spec) else None
    out = []
    for e in sorted([e for e in past if e["key"] == key], key=lambda x: x["date"]):
        r = _row_by(e, lab)
        if r is not None and r.get("a") is not None:
            out.append((e["date"], r["a"]))
    return out[-k:]


def _row_by(e: Dict, label) -> Optional[Dict]:
    return next((r for r in e.get("rows") or [] if label and r.get("label") == label), None)


def context(past: List[Dict], upcoming: List[Dict], hist: pd.DataFrame) -> Dict[str, str]:
    """One data-backed sentence per theme, used under every event card."""
    ctx: Dict[str, str] = {}
    cc = _last_vals(past, "cpi", "核心 CPI 年增")
    pc = _last_vals(past, "pce", "核心 PCE 年增")
    rate = _last_vals(past, "fomc", "政策利率（上限）", 2)
    nxt = next((e for e in upcoming if e["key"] == "fomc"), None)
    fed = ""
    if rate:
        fed = f"聯準會政策利率上限 {rate[-1][1]:.2f}%"
        if nxt:
            c = (_row_by(nxt, "政策利率（上限）") or {}).get("c")
            exp = ("" if c is None else ("，市場預期維持" if abs(c - rate[-1][1]) < 0.01 else
                                          f"，市場預期{'降' if c < rate[-1][1] else '升'}息至 {c:.2f}%"))
            fed += f"；下次會議 {nxt['date']}{exp}"
    infl = []
    if cc:
        infl.append(f"核心 CPI 年增 {cc[-1][1]:.1f}%" + (f"（{len(cc) - 1} 次前 {cc[0][1]:.1f}%）" if len(cc) > 1 else ""))
    if pc:
        infl.append(f"核心 PCE 年增 {pc[-1][1]:.1f}%（聯準會目標 2%）")
    ur = _last_vals(past, "nfp", "失業率")
    nf = _last_vals(past, "nfp", "非農新增就業（千人）", 3)
    lab = []
    if ur:
        lab.append(f"失業率 {ur[-1][1]:.1f}%" + (f"（{len(ur) - 1} 次前 {ur[0][1]:.1f}%）" if len(ur) > 1 else ""))
    if nf:
        lab.append(f"近 {len(nf)} 個月非農平均 {np.mean([v for _, v in nf]):+.0f}K")
    mk = []
    if hist is not None and "^TNX" in hist.columns:
        s = hist["^TNX"].dropna()
        if len(s) > 21:
            mk.append(f"10 年期殖利率 {s.iloc[-1]:.2f}%（20 日 {(s.iloc[-1] - s.iloc[-21]) * 100:+.0f}bp）")
    if hist is not None and "^VIX" in hist.columns:
        v = hist["^VIX"].dropna()
        if len(v):
            mk.append(f"VIX {v.iloc[-1]:.1f}")
    ctx["inflation"] = "；".join(infl)
    ctx["labor"] = "；".join(lab)
    ctx["fed"] = fed
    ctx["market"] = "；".join(mk)
    return ctx


CTX_FOR = {"cpi": ("inflation", "fed"), "ppi": ("inflation", "fed"), "pce": ("inflation", "fed"), "nfp": ("labor", "fed"),
           "jolts": ("labor", "fed"), "claims": ("labor",), "fomc": ("fed", "inflation", "labor"), "minutes": ("fed",),
           "fedchair": ("fed", "inflation"), "gdp": ("labor", "fed"), "retail": ("labor",), "ism_mfg": ("market",),
           "ism_svc": ("inflation",), "umich": ("inflation",)}


# ------------------------------------------------------------------ build
def _fmt_times(utc: Optional[str]) -> Tuple[str, str]:
    if not utc:
        return "", ""
    from zoneinfo import ZoneInfo
    t = datetime.fromisoformat(utc.replace("Z", "+00:00"))
    et = t.astimezone(ZoneInfo("America/New_York"))
    tp = t.astimezone(ZoneInfo("Asia/Taipei"))
    day = "" if tp.date() == et.date() else ("（隔日）" if tp.date() > et.date() else "")
    return et.strftime("%H:%M"), tp.strftime("%m/%d %H:%M") + day


def _et_utc(day: str, hh: int, mm: int) -> str:
    from zoneinfo import ZoneInfo
    d = date.fromisoformat(day)
    t = datetime(d.year, d.month, d.day, hh, mm, tzinfo=ZoneInfo("America/New_York"))
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def all_events(days: Dict[str, Dict], ff: Optional[List[Dict]] = None) -> List[Dict]:
    out = []
    for d in sorted(days):
        out += events_for_day(d, days[d].get("rows") or [], ff)
    return out


def build(eng, now: Optional[datetime] = None) -> Dict:
    ec = getattr(eng, "econ", None)
    if ec is None or not ec.days:
        return {"available": False}
    today = EC.us_today() if now is None else now.date()
    evs = all_events(ec.days, ec.ff)
    hist = getattr(getattr(eng, "market", None), "history", None)
    past = [e for e in evs if e["date"] < today.isoformat() or e["released"]]
    ahead = int(EC.cfg().get("days_ahead", 45))
    lo, hi = (today - timedelta(days=7)).isoformat(), (today + timedelta(days=ahead)).isoformat()
    window = [e for e in evs if lo <= e["date"] <= hi]
    have = {e["date"] for e in window if e["key"] == "fomc"}
    for m in ec.fomc or []:                                       # FOMC meetings beyond the Nasdaq horizon (dates only)
        if today.isoformat() <= m["date"] <= (today + timedelta(days=200)).isoformat() and m["date"] not in have:
            window.append({"id": f"fomc:{m['date']}", "key": "fomc", "date": m["date"],
                           "utc": _et_utc(m["date"], 14, 0), "zh": EV["fomc"]["zh"], "en": EV["fomc"]["en"], "imp": 3, "rows": [],
                           "released": False, "dir": None, "sep": m.get("sep", False), "fed_only": True})
    seps = {m["date"]: m.get("sep", False) for m in ec.fomc or []}
    stats = history_stats(past, hist)
    upcoming = sorted([e for e in window if not e["released"]], key=lambda e: (e["date"], e.get("utc") or ""))
    ctx = context(past, upcoming, hist)
    for e in window:
        if e["key"] == "fomc":
            e["sep"] = e.get("sep") or seps.get(e["date"], False)
        e["et"], e["tpe"] = _fmt_times(e.get("utc"))
        e["dir_label"] = dir_label(e["key"], e["dir"]) if e.get("dir") else None
        e["scen"] = SCEN.get(e["key"])
        e["stats"] = stats.get(e["key"])
        e["ctx"] = "；".join(x for x in (ctx.get(k) for k in CTX_FOR.get(e["key"], ())) if x)
        if e["released"] and e["date"] >= (today - timedelta(days=3)).isoformat():
            e["move"] = reaction(hist, e["date"])
    window.sort(key=lambda e: (e["date"], e.get("utc") or "", -e["imp"]))
    nxt_fomc = next((e for e in upcoming if e["key"] == "fomc"), None)
    wk_end = (today + timedelta(days=7)).isoformat()
    return {"available": True, "asof": today.isoformat(), "events": window, "stats": stats, "context": ctx,
            "next_fomc": nxt_fomc, "week": [e["id"] for e in window if today.isoformat() <= e["date"] <= wk_end and e["imp"] >= 2],
            "n_hist": len(past), "hist_from": min((e["date"] for e in past), default=None)}


def summary_lines(res: Dict, days: int = 7) -> List[str]:
    """For the AI data pack: upcoming key releases with consensus, and the latest surprises."""
    if not res or not res.get("available"):
        return []
    today = res["asof"]
    lim = (pd.Timestamp(today) + pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    up = [e for e in res["events"] if not e["released"] and e["date"] <= lim and e["imp"] >= 2]
    done = [e for e in res["events"] if e["released"] and e.get("dir") and e["imp"] >= 2][-6:]
    L = []
    if up:
        L.append("未來一週重要經濟數據：" + "；".join(
            f"{e['date']} {e['et']}ET {e['zh']}" + (f"（預期 {e['rows'][0]['cons']}，前值 {e['rows'][0]['prev']}）" if e["rows"] and e["rows"][0]["cons"] else "")
            for e in up[:10]))
    if done:
        L.append("近期公布：" + "；".join(f"{e['date']} {e['zh']} {e['rows'][0]['label']} {e['rows'][0]['actual']}（預期 {e['rows'][0]['cons'] or '—'}）→ {e['dir_label'][0]}"
                                     for e in done))
    return L

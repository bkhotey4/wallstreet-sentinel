"""主線追蹤：把每天的新聞串成幾條長期主線（2026-11-21 盲點檢討，使用者：「再仔細想一下是不是也是我們目前網頁跟 discord bot 的盲點?」）。

盲點：即時新聞只看最近 36 小時，每則各自判斷；Discord 只在價格急動、證交會申報或 3 家以上媒體同時報時推播。
所以像「美中科技脫鉤」這種一週內一則接一則、但每則都不大的事（11/16 商務部遠端使用晶片新規、11/19 台積電收緊中國客戶、
11/20 國會報告與 Cursor 研究停用中國 AI 模型），網站和 Discord 都沒有把它當成一件事。

做法：每次建置把 /api/news 的新聞存進 30 天的檔案（data_cache/econ_threads_news.json，雲端快取會保留），
用關鍵字把每則新聞歸到主線，算「48 小時幾則」對「過去 14 天平常每 48 小時幾則」。
  升溫：48 小時 ≥ 3 則，而且是平常的 2 倍以上。
  官方新文件：48 小時內有官方來源（央行、國會委員會、交易所等 off=true 的來源）。
只是「新聞變多」的統計，不是讀過內文的判斷，也不代表市場一定會動。
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Dict, List, Optional

log = logging.getLogger(__name__)
KEEP_DAYS = 30
ROUTINE_OFF = ("fed", "ecb", "boj")   # central-bank feeds post daily (speeches, surveys); rate decisions have their own alert (cbSurprise)
MIN_DAYS = 5          # 「升溫」要先有 5 天的新聞當「平常」；之前只顯示「有消息」（官方新文件不受影響）

# id, 中文名, 關鍵字（英文整字比對、中文子字串）, 相關行情, 一句話說明
THREADS = [
    ("uscn_tech", "美中科技脫鉤",
     ["出口管制", "實體清單", "華為", "中芯", "DeepSeek", "中國 AI", "中國AI", "中共", "美中", "export control", "export controls", "Entity List",
      "Huawei", "SMIC", "Chinese AI", "Chinese models", "Chinese chip", "Chinese chips", "China AI", "China chip", "China chips", "chip curbs",
      "AI chips to China", "CCP", "PRC", "decoupling", "tech war", "Bureau of Industry and Security",
      "chips to China", "chip smuggling", "晶片走私"],   # 11-27: 「Funneling Nvidia Chips to China」 and 晶片走私 stories missed
     [("^SOX", "費城半導體"), ("TSM", "台積電 ADR"), ("CNY=X", "美元兌人民幣")],
     "美國與中國在晶片、AI 模型、資料中心上一層一層切開，台灣供應鏈夾在中間。"),
    ("ai_capex", "AI 資本支出與獲利",
     ["資本支出", "資料中心", "雲端", "capex", "data center", "data centers", "hyperscaler", "hyperscalers", "AI spending", "AI bubble",
      "GPU", "GPUs", "Anthropic", "OpenAI", "CoreWeave", "Nvidia", "輝達",
      # 11-28: Warsh's 11/16 remarks on the Fed's AI scenarios said "super intelligence", never "AI"
      "super intelligence", "superintelligence", "超級智慧"],
     [("^SOX", "費城半導體"), ("NVDA", "輝達"), ("^TWII", "台股加權")],
     "大公司花在 AI 的錢賺不賺得回來，決定台灣伺服器與晶片訂單。"),
    ("fed_path", "聯準會與美國利率",
     ["聯準會", "鮑爾", "美國升息", "美國降息", "美債殖利率", "Fed", "FOMC", "Federal Reserve", "Powell", "Waller", "rate hike", "rate cut", "rate hikes", "rate cuts",
      "Treasury yields", "PCE"],
     [("^TNX", "美債 10 年殖利率"), ("DX-Y.NYB", "美元指數")],
     "借錢成本的方向，影響所有資產的評價與新台幣。"),
    ("japan_yen", "日圓與日本央行",
     ["日銀", "日本央行", "日圓", "日元", "BOJ", "Bank of Japan", "yen", "JGB", "JGBs", "Ueda", "carry trade"],
     [("JPY=X", "美元兌日圓"), ("^N225", "日經 225")],
     "日本升息與日圓急升，可能讓借日圓投資的錢被迫平倉。"),
    ("tw_leverage", "台股槓桿與被迫賣",
     ["融資", "斷頭", "追繳", "限空", "放空", "融券", "借券", "平盤以下", "國安基金", "維持率", "當沖", "權證", "margin call", "margin calls",
      "Taiwan stocks"],   # not English "short selling": US short-interest stories are not 台股槓桿
     [("^TWII", "台股加權"), ("TWD=X", "美元兌新台幣")],
     "借錢買股的人被迫賣，常是台股急跌的放大器。"),
    ("china_econ", "中國經濟與政策",
     ["人行", "中國人民銀行", "降準", "刺激", "房地產", "地方債", "PBOC", "People's Bank of China", "stimulus", "Evergrande", "Country Garden",
      "Chinese economy", "China's economy", "yuan",
      # 11-27: 0 items in 7 days while 「China’s $1 Trillion Trade Surplus」「China’s $1.7 Trillion AI Rout」 ran (curly apostrophes, markets words)
      "China's", "China’s", "Chinese stocks", "China stocks", "A-shares", "trade surplus", "renminbi",
      "中國經濟", "陸股", "人民幣", "中國出口", "陸港股", "港股", "恆生", "恒生",
      # 11-28: the State Council's 11/27 midday market-support statement (state funds, Central Huijin) moved HK chip stocks
      "State Council", "national team", "Central Huijin", "國務院", "國家隊", "中央匯金"],
     [("^HSI", "恆生指數"), ("CNY=X", "美元兌人民幣"), ("HG=F", "銅")],
     "中國景氣與政策，牽動香港股市、原物料與台灣的對中出口。"),
    # 11-21 self-review (user: 「我希望你可以自己思考哪裡有漏，你可以直接新增」): four threads a Taiwan / AI-chain reader needs
    ("cross_strait", "兩岸與台海",
     ["台海", "兩岸", "解放軍", "共軍", "軍演", "海警", "封鎖", "Taiwan Strait", "PLA", "cross-strait", "blockade of Taiwan"],
     [("^TWII", "台股加權"), ("TWD=X", "美元兌新台幣"), ("TSM", "台積電 ADR")],
     "台海緊張會直接打到台股與新台幣，也牽動全球晶片供應的風險溢價。"),
    # 11-28: 九合一選舉當晚網站沒有任何台灣政治的主線（和美國期中選舉同一類缺口）
    ("tw_politics", "台灣政治與政策",
     ["九合一", "地方選舉", "縣市長", "立法院", "立委", "總預算", "特別預算", "國防預算", "罷免", "公投", "賴清德", "行政院", "卓榮泰",
      "國民黨", "民進黨", "民眾黨", "鄭麗文", "黃國昌", "Lai Ching-te", "Legislative Yuan", "Kuomintang", "KMT", "DPP"],
     [("^TWII", "台股加權"), ("TWD=X", "美元兌新台幣"), ("2330.TW", "台積電")],
     "選舉與立法院決定預算、國防、能源與兩岸政策怎麼走；政策方向和政治穩定度會反映在外資對台股和新台幣的信心。"),
    ("minerals", "關鍵礦產與稀土",
     ["稀土", "鎵", "鍺", "銻", "關鍵礦產", "rare earth", "rare earths", "gallium", "germanium", "antimony", "critical minerals"],
     [("^SOX", "費城半導體"), ("HG=F", "銅"), ("CNY=X", "美元兌人民幣")],
     "中國反制美國時常用的手段；半導體、電動車、國防材料會先受影響，台灣與日本的材料供應鏈首當其衝。"),
    ("ai_power", "AI 電力與核能",
     ["電網", "核能", "核電", "電價", "小型模組化反應爐", "nuclear power", "nuclear energy", "nuclear plant", "nuclear plants", "nuclear reactor",
      "nuclear reactors", "SMR", "small modular reactor", "power grid", "electricity demand", "power demand", "uranium"],   # not bare "nuclear": Iran
     [("^TNX", "美債 10 年殖利率"), ("^SOX", "費城半導體")],
     "AI 資料中心要的電越來越多，電網、核能與電力設備是 AI 的第二條供應鏈；也牽動台灣的電價與產業用電。"),
    ("memory", "記憶體循環",
     ["記憶體", "DRAM", "HBM", "NAND", "memory chip", "memory chips", "Micron", "SK Hynix", "Samsung Electronics", "南亞科", "華邦電"],
     [("MU", "美光"), ("^SOX", "費城半導體"), ("^TWII", "台股加權")],
     "AI 伺服器吃掉大量高頻寬記憶體，記憶體價格的循環常是台股記憶體族群與韓國出口的領先指標。"),
    ("energy_geo", "能源與地緣衝突",
     ["油價", "原油", "荷姆茲", "伊朗", "以色列", "烏克蘭", "俄羅斯", "OPEC", "oil", "crude", "Hormuz", "Iran", "Israel", "Ukraine", "Russia"],
     [("BZ=F", "布蘭特原油"), ("GC=F", "黃金"), ("^VIX", "VIX")],
     "戰爭與能源供給，經由油價傳到通膨與利率。"),
    # 11-25: 美國依 301 條款對 14 個經濟體（含台灣）提議加關稅，主線裡沒有「關稅」這條，網站沒把它串起來
    ("tariffs", "關稅與貿易協定",
     ["關稅", "對等關稅", "301條款", "301 條款", "301調查", "232條款", "232 條款", "貿易協定", "貿易談判", "經貿", "產能過剩",
      "tariff", "tariffs", "Section 301", "Section 232", "Section 122", "USTR", "trade deal", "trade deals", "trade war", "reciprocal trade",
      "overcapacity", "duties", "levies"],
     [("TWD=X", "美元兌新台幣"), ("^TWII", "台股加權"), ("DX-Y.NYB", "美元指數")],
     "美國關稅稅率與各國貿易協定，決定台灣出口的成本與新台幣；也會經由進口物價推高美國通膨。"),
    # 11-26: 永豐銀遭駭盜轉（11/5 起、418 人 4,176 萬元，金管會召 76 家資安長）、11/13 微軟大當機後台股資安股十多檔漲停，網站一個字都沒寫
    ("cyber", "資安事件與資安股",
     ["駭客", "遭駭", "資安", "網攻", "網路攻擊", "個資外洩", "資料外洩", "勒索軟體", "盜轉", "微軟當機", "系統當機", "cyberattack", "cyber attack",
      "cyberattacks", "hack", "hacked", "hackers", "data breach", "breach", "ransomware", "service outage", "system outage", "CrowdStrike",
      "Palo Alto Networks", "zero-day"],
     [("CRWD", "CrowdStrike"), ("PANW", "Palo Alto"), ("^TWII", "台股加權")],
     "駭客入侵銀行或大型系統當機，會讓金融監管加嚴、企業資安支出增加；台股資安股常在事件後幾天集體漲停，事件本身則可能讓被駭公司的股價與信用受傷。"),
    # 11-28 gap review: Democrats won the midterms (House 258+ seats and the Senate, BBC 11-22) and the site had no thread for what the
    # new Congress (seated 2027-01-03) means for tariffs, AI rules, the budget and Fed oversight
    ("us_politics", "美國政治與政策路徑",
     ["期中選舉", "國會", "眾議院", "參議院", "眾議長", "民主黨", "共和黨", "白宮", "預算案", "撥款", "midterm", "midterms", "Congress",
      "House Democrats", "Senate", "Speaker", "Democrats", "Republicans", "White House", "appropriations", "filibuster", "impeachment"],
     [("^GSPC", "標普 500"), ("^TNX", "美國 10 年期殖利率"), ("DX-Y.NYB", "美元指數")],
     "選舉結果決定 2027 年後的關稅權限、AI 監管、預算與債務上限怎麼走；國會換人，政策的方向和不確定性都會跟著變，影響利率、美元與科技股。"),
    # 11-28 gap review: Section 232 (national-security tariffs, incl. semiconductors) had zero coverage — closer to Taiwan than 301
    ("s232_chips", "232 條款與半導體關稅",
     ["232條款", "232 條款", "232調查", "Section 232", "232 investigation", "semiconductor tariff", "semiconductor tariffs", "chip tariff",
      "chip tariffs", "半導體關稅", "晶片關稅", "CHIPS Act", "晶片法案"],
     [("TSM", "台積電 ADR"), ("^SOX", "費城半導體"), ("^TWII", "台股加權")],
     "美國以國家安全為由對半導體等產品課關稅（232 條款），稅率與豁免條件直接決定台積電與台灣供應鏈在美國的成本，以及赴美設廠的壓力。"),
]
ASCII = re.compile(r"^[ -~’]+$")


def _rx(words: List[str]):
    en = [w for w in words if ASCII.match(w)]
    zh = [w for w in words if not ASCII.match(w)]
    rx = re.compile(r"(?<![A-Za-z])(?:" + "|".join(re.escape(w) for w in en) + r")(?![A-Za-z])", re.I) if en else None
    return rx, zh


_RX = [(tid, _rx(words)) for tid, _zh, words, _a, _w in THREADS]


def match(title: str) -> List[str]:
    t = title or ""
    return [tid for tid, (rx, zh) in _RX if (rx and rx.search(t)) or any(w in t for w in zh)]


def _file():
    from ..config import DATA_DIR
    return DATA_DIR / "econ_threads_news.json"


def load_archive() -> List[Dict]:
    try:
        d = json.loads(_file().read_text(encoding="utf-8"))
        return d.get("items") or []
    except (OSError, ValueError):
        return []


def archive(items: List[Dict], now: Optional[float] = None, old: Optional[List[Dict]] = None, save: bool = True) -> List[Dict]:
    """Merge /api/news items (t, u, s, o, ts, off, lang) into the 30-day archive, one row per link."""
    now = time.time() if now is None else now
    have = {x["u"]: x for x in (load_archive() if old is None else old) if x.get("u")}
    for x in items or []:
        if not isinstance(x, dict) or not x.get("u") or not x.get("t") or x.get("q"):
            continue
        if x["u"] not in have:
            have[x["u"]] = {k: x.get(k) for k in ("t", "u", "s", "o", "ts", "off", "lang")}
    keep = sorted((x for x in have.values() if now - float(x.get("ts") or 0) < KEEP_DAYS * 86400), key=lambda x: -float(x.get("ts") or 0))
    if save:
        try:
            f = _file()
            tmp = f.with_suffix(".tmp")
            tmp.write_text(json.dumps({"ts": now, "items": keep}, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, f)
        except OSError as e:
            log.warning("thread archive not saved: %s", e)
    return keep


def view(items: List[Dict], now: Optional[float] = None) -> Dict:
    now = time.time() if now is None else now
    days = (now - min((float(x.get("ts") or now) for x in items), default=now)) / 86400
    out = []
    for tid, zh, _w, assets, why in THREADS:
        hits = [x for x in items if tid in match(x.get("t", ""))]
        n48 = [x for x in hits if now - float(x.get("ts") or 0) < 48 * 3600]
        n14 = [x for x in hits if now - float(x.get("ts") or 0) < 14 * 86400]
        base = max(0.0, (len(n14) - len(n48)) / 6.0)              # per 48 h over the 12 days before the last 48 h
        hot = len(n48) >= 3 and len(n48) >= 2 * max(1.0, base) and days >= MIN_DAYS   # no baseline yet → no 升溫
        off = [x for x in n48 if x.get("off") and x.get("o") not in ROUTINE_OFF]
        state = "升溫" if hot else ("官方新文件" if off else ("有消息" if n48 else "安靜"))
        out.append({"id": tid, "zh": zh, "why": why, "assets": assets, "n48": len(n48), "n14": len(n14), "base": round(base, 1),
                    "state": state, "official": [x["u"] for x in off],
                    "items": [{k: x.get(k) for k in ("t", "u", "s", "ts", "off")} for x in hits[:12]]})
    return {"ts": now, "days": round(days, 1), "threads": out}

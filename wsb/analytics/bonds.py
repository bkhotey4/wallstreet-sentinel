"""全球債市: government bonds across the US, Japan, Europe and Asia-Pacific; corporate bonds in the US, Europe and emerging /
Asian markets; cross-border flows (Japan MOF weekly, US TIC); and a plain-language read of what the bond market is saying.
Every sentence is chosen by rules on the numbers.  Description and history, not a forecast or advice."""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

# 10-year government bond yields: (key, zh, source, id). FRED's OECD series are monthly; the US and Japan are daily.
SOVEREIGN = [("us", "美國", "fred", "DGS10"), ("jp", "日本", "jgb", "10Y"), ("de", "德國", "fred", "IRLTLT01DEM156N"),
             ("gb", "英國", "fred", "IRLTLT01GBM156N"), ("fr", "法國", "fred", "IRLTLT01FRM156N"), ("it", "義大利", "fred", "IRLTLT01ITM156N"),
             ("es", "西班牙", "fred", "IRLTLT01ESM156N"), ("gr", "希臘", "fred", "IRLTLT01GRM156N"), ("kr", "韓國", "fred", "IRLTLT01KRM156N"),
             ("au", "澳洲", "fred", "IRLTLT01AUM156N"), ("ca", "加拿大", "fred", "IRLTLT01CAM156N")]
# corporate bonds (ICE BofA option-adjusted spreads over government bonds, %); FRED serves 3 years, the archive grows
CORP = [("us_ig", "美國投資級公司債", "BAMLC0A0CM", "BAMLC0A0CMEY", "ig"), ("us_bbb", "美國 BBB（投資級最低一級）", "BAMLC0A4CBBB", None, "ig"),
        ("us_hy", "美國高收益債（垃圾債）", "BAMLH0A0HYM2", "BAMLH0A0HYM2EY", "hy"), ("us_ccc", "美國 CCC（最弱的公司）", "BAMLH0A3HYC", None, "hy"),
        ("eu_hy", "歐洲高收益債", "BAMLHE00EHYIOAS", "BAMLHE00EHYIEY", "hy"), ("em", "新興市場公司債", "BAMLEMCBPIOAS", None, "ig"),
        ("asia", "亞洲新興市場公司債", "BAMLEMRACRPIASIAOAS", None, "ig"), ("em_hy", "新興市場高收益債", "BAMLEMHBHYCRPIOAS", None, "hy")]
FRED_IDS = tuple(i for _, _, s, i in SOVEREIGN if s == "fred") + tuple(x for c in CORP for x in (c[2], c[3]) if x)


def _fred(eng, sid) -> pd.Series:
    try:
        return eng.fred.get(sid).dropna()
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)


def _ago(s: pd.Series, days: int) -> Optional[float]:
    p = s[s.index <= s.index[-1] - pd.Timedelta(days=days)]
    return float(p.iloc[-1]) if len(p) else None


def sovereign(eng) -> List[Dict]:
    out = []
    for k, zh, src, sid in SOVEREIGN:
        if src == "jgb":
            try:
                s = eng.global_yields.get(sid)
            except Exception:  # noqa: BLE001
                s = pd.Series(dtype=float)
        else:
            s = _fred(eng, sid)
        if len(s) < 24:
            continue
        now, y1 = float(s.iloc[-1]), _ago(s, 365)
        out.append({"k": k, "zh": zh, "now": now, "date": s.index[-1].strftime("%Y-%m-%d"), "chg1y": None if y1 is None else now - y1,
                    "pct": float((s.iloc[:-1] < now).mean() * 100), "since": s.index[0].strftime("%Y"),
                    "hi": float(s.max()), "hi_d": s.idxmax().strftime("%Y-%m"), "daily": src == "jgb" or sid.startswith("DGS")})
    us = next((r for r in out if r["k"] == "us"), None)
    de = next((r for r in out if r["k"] == "de"), None)
    for r in out:
        r["vs_us"] = None if not us or r is us else r["now"] - us["now"]
        r["vs_de"] = r["now"] - de["now"] if de and r["k"] in ("fr", "it", "es", "gr") else None
    return out


def corporate(eng) -> List[Dict]:
    out = []
    for k, zh, oas_id, ey_id, kind in CORP:
        s = _fred(eng, oas_id)
        if len(s) < 60:
            continue
        now, m3 = float(s.iloc[-1]), _ago(s, 91)
        ch = None if m3 is None else now - m3
        pct = float((s.iloc[:-1] < now).mean() * 100)
        fast = ch is not None and m3 and ch / m3 >= 0.25 and ch >= (0.3 if kind == "hy" else 0.1)
        state = "急速擴大" if fast else "緊張" if pct >= 80 else "很放心" if pct <= 20 else "正常"
        ey = _fred(eng, ey_id) if ey_id else pd.Series(dtype=float)
        out.append({"k": k, "zh": zh, "kind": kind, "oas": now, "chg3m": ch, "pct": pct, "since": s.index[0].strftime("%Y-%m"),
                    "date": s.index[-1].strftime("%Y-%m-%d"), "state": state,
                    "ey": float(ey.iloc[-1]) if len(ey) else None, "ey_1y": (float(ey.iloc[-1]) - _ago(ey, 365)) if len(ey) > 260 and _ago(ey, 365) is not None else None})
    return out


def flows() -> Dict:
    from ..data import bondflows as BF
    d = BF.load()
    return {"mof": BF.mof_view(d), "tic": BF.tic_view(d)}


def term_premium(eng) -> Optional[Dict]:
    s = _fred(eng, "THREEFYTP10")
    if len(s) < 260:
        return None
    return {"now": float(s.iloc[-1]), "chg1y": float(s.iloc[-1]) - (_ago(s, 365) or float(s.iloc[-1])),
            "pct": float((s.iloc[:-1] < s.iloc[-1]).mean() * 100), "since": s.index[0].strftime("%Y")}


def build(eng) -> Dict:
    sv, cp, fl, tp = sovereign(eng), corporate(eng), flows(), term_premium(eng)
    return {"available": bool(sv or cp), "sov": sv, "corp": cp, "flows": fl, "tp": tp}


def read(r: Dict) -> Dict:
    """One sentence + plain-language implications, all chosen from the numbers."""
    sv, cp, fl, tp = r["sov"], r["corp"], r["flows"], r.get("tp")
    up = [x for x in sv if (x["chg1y"] or 0) >= 0.25]
    dn = [x for x in sv if (x["chg1y"] or 0) <= -0.25]
    hy = [x for x in cp if x["kind"] == "hy"]
    wide = [x for x in cp if x["state"] in ("緊張", "急速擴大")]
    calm = [x for x in cp if x["state"] == "很放心"]
    mof, tic = fl.get("mof") or {}, fl.get("tic") or {}
    jp = next((x for x in tic.get("rows") or [] if x["name"] == "Japan"), None)
    parts = []
    if sv:
        parts.append(f"政府借錢變貴（{len(sv)} 國中 {len(up)} 國的 10 年期公債利率比一年前高）" if len(up) * 2 > len(sv) else
                     f"政府借錢變便宜（{len(sv)} 國中 {len(dn)} 國的長債利率比一年前低）" if len(dn) * 2 > len(sv) else "各國長債利率漲跌互見")
    if cp:
        weak_only = wide and all(x["kind"] == "hy" or x["k"] in ("asia", "em") for x in wide) and not any(x["k"] in ("us_ig", "us_bbb") for x in wide)
        parts.append(("體質較弱的公司（垃圾債）利差在擴大，好公司還正常：債市開始擔心弱體質企業還不出錢" if weak_only else
                      "公司債利差在擴大：債市開始擔心企業還不出錢") if wide else
                     "公司債利差在歷史低檔：借錢給企業的人很放心" if len(calm) * 2 >= len(cp) else "公司債利差正常")
    if mof.get("sum5") is not None and mof["pct5"] <= 10 and mof["sum5"] < 0:
        parts.append(f"日本資金在回家（5 週賣超外國債券 {abs(mof['sum5']):.1f} 兆日圓）")
    elif mof.get("sum5") is not None and mof["pct5"] >= 90 and mof["sum5"] > 0:
        parts.append(f"日本資金大舉買外國債券（5 週 {mof['sum5']:.1f} 兆日圓）")
    head = "一句話看懂：" + "；".join(parts) + "。"
    imp = []
    if len(up) * 2 > len(sv or [0]):
        imp.append("利率上升時，房貸、企業借錢和政府利息都變貴；未來獲利折算回今天的價值變少，高本益比的成長股最受影響。")
    if (tp or {}).get("now") is not None and tp["pct"] >= 80:
        imp.append(f"美國 10 年期的期限溢酬 {tp['now']:.2f}%（{tp['since']} 年以來第 {tp['pct']:.0f} 百分位）：投資人要求更多補償才願意長期借錢給美國政府，反映對財政赤字與通膨的擔心。")
    if jp and (jp.get("chg6") or 0) <= -5:
        imp.append(f"日本是美債最大的海外持有者，半年減少 {abs(jp['chg6']):.0f}%：美國長債少了一個大買家，長天期利率比較容易往上。")
    if calm and up and not wide:
        imp.append("政府借錢成本在升、公司債利差卻還很低：市場對企業違約相當放心，也可能太放心；經濟一轉弱，利差常會一次補漲（擴大）。")
    if wide:
        imp.append("公司債利差擴大通常和股市下跌同時發生，代表資金開始避開體質較弱的公司；最弱的 CCC 等級先動時要特別留意。")
    if any(x["k"] in ("it", "gr") and (x["vs_de"] or 0) >= 2 for x in sv):
        imp.append("南歐國家比德國多付的利息偏高：歐債壓力的老問題，詳見「全球行情」頁的歐洲卡片。")
    imp.append("對台灣：美債利率高、美元強時，外資較容易把錢匯回美國；台灣壽險業持有大量海外債券，利率與匯率的大波動會影響它們的淨值與股價。")
    return {"head": head, "imp": imp, "n_up": len(up), "n_sov": len(sv), "hy": hy}


def corp_read(r: Dict) -> Dict:
    """Corporate bonds only: who is being asked to pay more, where, and what it means for refinancing."""
    cp = r["corp"]
    by = {x["k"]: x for x in cp}
    wide = [x for x in cp if x["state"] in ("緊張", "急速擴大")]
    calm = [x for x in cp if x["state"] == "很放心"]
    good_ok = all(by[k]["state"] not in ("緊張", "急速擴大") for k in ("us_ig", "us_bbb") if k in by)
    if wide and good_ok:
        head = "一句話看懂：體質較弱的公司借錢變難了（垃圾債利差在擴大），體質好的公司還很正常：壓力集中在最弱的那一群。"
    elif wide:
        head = "一句話看懂：連體質好的公司都被要求付更高的利息：信用壓力已經不只在最弱的公司。"
    elif calm and len(calm) * 2 >= len(cp):
        head = "一句話看懂：借錢給企業的人很放心，各類公司債利差大多在自己歷史的低檔；放心也可能代表太放心。"
    else:
        head = "一句話看懂：公司債利差大致正常，沒有明顯的違約擔心。"
    imp = []
    mv = sorted([x for x in cp if x["chg3m"] is not None], key=lambda x: -x["chg3m"])
    if mv and mv[0]["chg3m"] > 0:
        imp.append(f"近 3 個月利差擴大最多的是{mv[0]['zh']}（+{mv[0]['chg3m'] * 100:.0f} bp）" +
                   (f"，其次是{mv[1]['zh']}（+{mv[1]['chg3m'] * 100:.0f} bp）" if len(mv) > 1 and mv[1]["chg3m"] > 0 else "") + "。")
    hy = by.get("us_hy")
    if hy and hy.get("ey") is not None:
        imp.append(f"美國垃圾債公司現在借錢要付約 {hy['ey']:.1f}%" + (f"，比一年前{'多' if hy['ey_1y'] >= 0 else '少'} {abs(hy['ey_1y']):.1f} 個百分點" if hy.get("ey_1y") is not None else "")
                   + "：之後一兩年有債務到期、要借新還舊的公司，利息負擔會" + ("變重。" if (hy.get("ey_1y") or 0) > 0 else "變輕。"))
    ccc = by.get("us_ccc")
    if ccc and ccc["state"] in ("緊張", "急速擴大"):
        imp.append(f"最弱的 CCC 等級利差 {ccc['oas']:.1f}%，{ccc['state']}：歷史上違約增加前，常常是 CCC 先擴大、再傳到 B 與 BB，最後才到投資級。")
    eu = by.get("eu_hy")
    if eu and hy and eu.get("chg3m") is not None and hy.get("chg3m") is not None and eu["chg3m"] > hy["chg3m"] + 0.2:
        imp.append("歐洲垃圾債擴大得比美國多：歐洲企業的壓力比美國大，可以對照「歐債」頁看南歐國家的利差有沒有一起上升。")
    em = [by[k] for k in ("em", "asia", "em_hy") if k in by]
    if em and any(x["state"] in ("緊張", "急速擴大") for x in em):
        imp.append("新興市場與亞洲公司債利差也在擴大：通常和美元走強、美國利率上升一起出現，借美元的新興市場企業還款壓力變大。")
    up = [x for x in r["sov"] if (x["chg1y"] or 0) >= 0.25]
    if calm and up and not wide:
        imp.append("公債利率在升、公司債利差卻很低：投資人對企業違約相當放心，一旦景氣轉弱，利差常會一次補漲。")
    if not wide:
        imp.append("公司債利差平穩時，股市的大跌多半來自估值或利率，而不是企業違約。")
    return {"head": head, "imp": imp}

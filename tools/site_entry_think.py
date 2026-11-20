"""每日總經情勢：「想進場前，可以從哪裡想」（2026-11-21，使用者：「每日總經是不是新增如果要入場，可以從哪裡思考？」）。

不是叫人進場或離場的訊號，也不給日期或價位。三部分，全部由程式從本站資料算出：
  1. 六個問題的燈號：被迫賣的人賣完了嗎（融資餘額）、恐慌退燒了嗎（VIX）、還在創新低嗎（加權指數）、
     信用市場有沒有壞（高收益債）、債市穩不穩（MOVE）、外資有沒有在把錢匯走（新台幣）。
  2. 歷史對照：加權指數單日跌 5% 以上之後（相隔 20 個交易日以上才算新的一次），20 天與 60 天後的結果，以及之後最深又跌多少。
  3. 先問自己的四件事（錢多久用不到、最壞能承受多少、一次還是分批、自己的假設）。
燈號門檻是自己設計的常用警戒線，不是回測過的預測模型。"""
from __future__ import annotations

import html
import logging
from typing import Dict, List, Optional

log = logging.getLogger(__name__)
LIGHT = {"g": "🟢", "y": "🟡", "r": "🔴"}


def _s(eng, sym):
    try:
        from tools.site_macro_dash import _series
        s = _series(eng, "px", sym).dropna()
        return s[s > 0]
    except Exception:  # noqa: BLE001
        return None


def margin_check(mg: Dict[str, List[float]]) -> Optional[Dict]:
    """mg = {date: [previous balance, balance]} in 億元 (TWSE MI_MARGN)."""
    days = sorted(d for d, v in (mg or {}).items() if isinstance(v, (list, tuple)) and len(v) == 2 and v[0] and v[1])
    if not days:
        return None
    ch = [(mg[d][1] / mg[d][0] - 1) * 100 for d in days[-3:]]
    last = ch[-1]
    lt = "r" if last <= -3 else ("y" if last <= -1 or min(ch) <= -3 else "g")
    return {"q": "被迫賣的人賣完了嗎？", "light": lt,
            "now": f"融資餘額 {mg[days[-1]][1]:,.0f} 億元，{days[-1][5:].replace('-', '/')} 一天 {last:+.1f}%",
            "rule": "🔴 一天減少 3% 以上（還在斷頭）；🟡 減少 1～3%，或近 3 天內有一天減少 3% 以上；🟢 變化在 1% 以內。",
            "why": "大跌時最先被迫賣的是借錢買股的人。融資減幅縮小，代表被迫賣的壓力在退。"}


def vix_check(s) -> Optional[Dict]:
    if s is None or len(s) < 25:
        return None
    now, hi = float(s.iloc[-1]), float(s.tail(20).max())
    lt = "r" if now >= 25 and now >= hi * 0.95 else ("g" if now < 25 and now <= hi * 0.8 else "y")
    return {"q": "恐慌退燒了嗎？", "light": lt, "now": f"VIX {now:.1f}，20 天內最高 {hi:.1f}",
            "rule": "🔴 在 25 以上且接近 20 天內最高；🟢 低於 25 且比最高點少兩成以上；其他 🟡。",
            "why": "VIX 是美股的恐慌指數。歷史上大跌常在恐慌從高點明顯回落之後才止穩，而不是在恐慌最高的那天。"}


def low_check(s) -> Optional[Dict]:
    if s is None or len(s) < 30:
        return None
    lows = s.rolling(20).min()
    hit = [i for i in range(len(s) - 15, len(s)) if s.iloc[i] <= lows.iloc[i] + 1e-9]
    since = (len(s) - 1 - hit[-1]) if hit else 99
    lt = "r" if since == 0 else ("y" if since < 5 else "g")
    return {"q": "還在創新低嗎？", "light": lt,
            "now": f"加權指數 {float(s.iloc[-1]):,.0f} 點，" + ("今天是 20 天內新低" if since == 0 else f"距上次 20 天內新低 {since} 個交易日"),
            "rule": "🔴 今天創 20 天內新低；🟡 5 個交易日內創過；🟢 5 個交易日以上沒有再創新低。",
            "why": "止跌通常是先「不再創新低」，再慢慢回穩。還在創新低時，沒人知道底在哪裡。"}


def credit_check(s) -> Optional[Dict]:
    if s is None or len(s) < 25:
        return None
    ch = (float(s.iloc[-1]) / float(s.iloc[-21]) - 1) * 100
    lt = "r" if ch <= -3 else ("y" if ch <= -1.5 else "g")
    return {"q": "信用市場有沒有壞？", "light": lt, "now": f"高收益債 ETF 20 天 {ch:+.1f}%",
            "rule": "🔴 20 天跌 3% 以上；🟡 跌 1.5～3%；🟢 跌不到 1.5%。",
            "why": "股票跌但公司債沒事，通常是評價修正；連借錢給公司的人都在逃，比較可能是景氣或金融出問題。"}


def move_check(s) -> Optional[Dict]:
    if s is None or len(s) < 10:
        return None
    now, p5 = float(s.iloc[-1]), float(s.iloc[-6])
    up = (now / p5 - 1) * 100
    lt = "r" if now > 130 else ("y" if now > 110 or up >= 10 else "g")
    return {"q": "債市穩不穩？", "light": lt, "now": f"MOVE {now:.0f}，5 天 {up:+.0f}%",
            "rule": "🔴 高於 130；🟡 高於 110 或 5 天升 10% 以上；🟢 其他。",
            "why": "MOVE 是美債的恐慌指數。債市不穩時，大型機構會一起降低風險，股市很難單獨止穩。"}


def twd_check(s) -> Optional[Dict]:
    if s is None or len(s) < 25:
        return None
    ch = (float(s.iloc[-1]) / float(s.iloc[-21]) - 1) * 100
    lt = "r" if ch >= 2 else ("y" if ch >= 1 else "g")
    return {"q": "外資有沒有在把錢匯走？", "light": lt, "now": f"美元兌新台幣 {float(s.iloc[-1]):.2f}，20 天 {ch:+.1f}%",
            "rule": "🔴 新台幣 20 天貶 2% 以上；🟡 貶 1～2%；🟢 其他。",
            "why": "外資賣台股後要把台幣換回美元。新台幣沒有急貶，代表錢還沒大舉離開台灣。"}


def drops(s, th: float = -5.0, gap: int = 20) -> List[Dict]:
    """Every one-day fall of `th`% or more (a new episode only after `gap` trading days), with what followed."""
    if s is None or len(s) < 80:
        return []
    r = s.pct_change(fill_method=None) * 100
    out, last_i = [], -10 ** 9
    for i in range(1, len(s)):
        if r.iloc[i] <= th and i - last_i >= gap:
            last_i = i
            c = float(s.iloc[i])
            f20 = float(s.iloc[i + 20]) / c - 1 if i + 20 < len(s) else None
            f60 = float(s.iloc[i + 60]) / c - 1 if i + 60 < len(s) else None
            win = s.iloc[i + 1:i + 61]
            dd = min(0.0, float(win.min()) / c - 1) if len(win) else None     # 0 = never closed below that day again
            out.append({"date": s.index[i].strftime("%Y-%m-%d"), "drop": float(r.iloc[i]), "f20": f20, "f60": f60, "dd60": dd,
                        "full": i + 60 < len(s)})
    return out


def _med(xs: List[float]) -> float:
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def base_rates(ev: List[Dict]) -> Optional[Dict]:
    done = [e for e in ev if e["full"]]
    if len(done) < 5:
        return None
    f20 = [e["f20"] for e in done]
    f60 = [e["f60"] for e in done]
    dd = [e["dd60"] for e in done]
    return {"n": len(done), "since": ev[0]["date"][:4], "up20": sum(x > 0 for x in f20) / len(f20), "up60": sum(x > 0 for x in f60) / len(f60),
            "med20": _med(f20), "med60": _med(f60), "med_dd": _med(dd), "worst_dd": min(dd), "best60": max(f60), "worst60": min(f60)}


def _mg() -> Dict:
    try:
        from wsb.data import tw_preopen as TP
        return TP.load().get("mg") or {}
    except Exception:  # noqa: BLE001
        return {}


def checks(eng, mg: Optional[Dict] = None) -> List[Dict]:
    out = []
    for f in (lambda: margin_check(mg if mg is not None else _mg()), lambda: vix_check(_s(eng, "^VIX")),
              lambda: low_check(_s(eng, "^TWII")), lambda: credit_check(_s(eng, "HYG")),
              lambda: move_check(_s(eng, "^MOVE")), lambda: twd_check(_s(eng, "TWD=X"))):
        try:
            c = f()
        except Exception:  # noqa: BLE001
            log.exception("entry check failed")
            c = None
        if c:
            out.append(c)
    return out


def _dd(x: Optional[float]) -> str:
    if x is None:
        return "之後還沒有資料"
    return "之後 60 天內沒有再跌破當天收盤" if x >= 0 else f"之後 60 天內最深再跌 {_pc(x)}"


def _pc(x: float) -> str:
    return f"{x * 100:+.1f}%"


def block(eng, mg: Optional[Dict] = None) -> str:
    cs = checks(eng, mg)
    if not cs:
        return ""
    e = html.escape
    g = sum(c["light"] == "g" for c in cs)
    r = sum(c["light"] == "r" for c in cs)
    lead = (f"{len(cs)} 個問題裡，🟢 {g} 個、🔴 {r} 個。"
            + ("多數還是紅燈：被迫賣壓和恐慌看起來還沒過去。" if r * 2 >= len(cs) else
               "多數已轉綠：被迫賣壓和恐慌比較可能已經過去，但這不代表會漲。" if g * 2 > len(cs) else "紅綠混雜：還在過渡期。"))
    rows = "".join(f'<tr><td>{LIGHT[c["light"]]}</td><td><b>{e(c["q"])}</b><div class="small muted">{e(c["why"])}</div></td>'
                   f'<td class="small">{e(c["now"])}<div class="muted">{e(c["rule"])}</div></td></tr>' for c in cs)
    tbl = f'<div class="scroll"><table class="mini"><thead><tr><th></th><th>問題</th><th>現在</th></tr></thead><tbody>{rows}</tbody></table></div>'
    hist = ""
    ev = drops(_s(eng, "^TWII"))
    br = base_rates(ev)
    if br:
        recent = [x for x in ev if not x["full"]]
        lst = "".join(f'<li>{x["date"]}：當天 {x["drop"]:.1f}%，20 天後 {_pc(x["f20"]) if x["f20"] is not None else "—"}，'
                      f'60 天後 {_pc(x["f60"]) if x["f60"] is not None else "還沒到"}，' + _dd(x["dd60"]) + '</li>'
                      for x in reversed(ev))
        hist = (f'<h3>歷史上台股單日跌 5% 以上之後</h3><p class="small">{br["since"]} 年以來共 {br["n"]} 次（已滿 60 個交易日的才算）：'
                f'20 天後比當天高的有 {br["up20"] * 100:.0f}%，中位數 {_pc(br["med20"])}；60 天後比當天高的有 {br["up60"] * 100:.0f}%，中位數 {_pc(br["med60"])}。'
                f'<b>但之後 60 天內，中位數還會再跌 {_pc(br["med_dd"])}，最慘一次再跌 {_pc(br["worst_dd"])}。</b>'
                f'意思是：大跌之後長一點看多半回得來，但「跌完還會再跌」很常見，能不能撐過那一段才是關鍵。</p>'
                + (f'<p class="small muted">還沒滿 60 天的：{"、".join(x["date"] for x in recent)}。</p>' if recent else "")
                + f'<details class="sgx"><summary>看每一次（{len(ev)} 次）</summary><ul class="small">{lst}</ul></details>')
    ask = ('<h3>看燈號之前，先問自己四件事</h3><ul class="small">'
           '<li><b>這筆錢多久用不到？</b>三到五年內要用的錢（婚禮、買房頭期款、學費），不適合放在會一年跌三成的地方。</li>'
           '<li><b>最壞的情況能承受多少？</b>用上面「之後最深再跌」的數字，換算成你的金額，想像帳面少掉那麼多時你會怎麼做。</li>'
           '<li><b>一次還是分批？</b>分批投入不必猜底，代價是如果馬上反彈會少賺；一次投入剛好相反。沒有一定比較好，看你比較受不了哪一種後悔。</li>'
           '<li><b>你自己的假設怎麼說？</b>你追蹤的「台股 2027 下半年泡沫破裂」如果成立，現在這一跌是泡沫前的修正，還是提早破了？'
           '「台股總經展望」卡每天更新支持與反對的證據。</li></ul>')
    return (f'<details class="sgx"><summary>想進場前，可以從哪裡想（{LIGHT["g"]} {g}／{len(cs)}）</summary>'
            f'<p class="small"><b>{e(lead)}</b></p>{tbl}{hist}{ask}'
            '<p class="note">燈號由程式從本站資料算出（融資：證交所；VIX、MOVE、高收益債、新台幣、加權指數：Yahoo 收盤），門檻是常用警戒線，不是回測過的預測模型；'
            '歷史對照用加權指數收盤，不含股息。這裡描述的是「現在的狀況」，不是叫你進場或離場的訊號，也不提供日期或價位。不構成投資建議。</p></details>')

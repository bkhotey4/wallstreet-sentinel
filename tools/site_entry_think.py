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
# 11-28 audit P3-17: the light thresholds live in settings.yaml (entry_think); these are the defaults, and the rule text on the
# card is built from the same numbers so the two cannot drift apart.
DEFAULT_TH = {"margin_red": -3.0, "margin_yellow": -1.0, "vix_line": 25.0, "vix_near_hi": 0.95, "vix_off_hi": 0.8, "low_days": 5,
              "credit_red": -3.0, "credit_yellow": -1.5, "move_red": 130.0, "move_yellow": 110.0, "move_jump": 10.0,
              "twd_red": 2.0, "twd_yellow": 1.0}


def th() -> Dict:
    try:
        from wsb.config import SETTINGS
        user = SETTINGS.get("entry_think") or {}
    except Exception:  # noqa: BLE001
        user = {}
    return {**DEFAULT_TH, **{k: v for k, v in user.items() if k in DEFAULT_TH and isinstance(v, (int, float))}}


def _g(x: float) -> str:
    return f"{x:g}"


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
    last, t = ch[-1], th()
    r_, y_ = t["margin_red"], t["margin_yellow"]
    lt = "r" if last <= r_ else ("y" if last <= y_ or min(ch) <= r_ else "g")
    return {"q": "被迫賣的人賣完了嗎？", "light": lt,
            "now": f"融資餘額 {mg[days[-1]][1]:,.0f} 億元，{days[-1][5:].replace('-', '/')} 一天 {last:+.1f}%",
            "rule": f"🔴 一天減少 {_g(-r_)}% 以上（還在斷頭）；🟡 減少 {_g(-y_)}～{_g(-r_)}%，或近 3 天內有一天減少 {_g(-r_)}% 以上；🟢 變化在 {_g(-y_)}% 以內。",
            "why": "大跌時最先被迫賣的是借錢買股的人。融資減幅縮小，代表被迫賣的壓力在退。"}


def vix_check(s) -> Optional[Dict]:
    if s is None or len(s) < 25:
        return None
    now, hi, t = float(s.iloc[-1]), float(s.tail(20).max()), th()
    line, near, off = t["vix_line"], t["vix_near_hi"], t["vix_off_hi"]
    lt = "r" if now >= line and now >= hi * near else ("g" if now < line and now <= hi * off else "y")
    return {"q": "恐慌退燒了嗎？", "light": lt, "now": f"VIX {now:.1f}，20 天內最高 {hi:.1f}",
            "rule": f"🔴 在 {_g(line)} 以上且接近 20 天內最高；🟢 低於 {_g(line)} 且比最高點少 {_g(round((1 - off) * 100))}% 以上；其他 🟡。",
            "why": "VIX 是美股的恐慌指數。歷史上大跌常在恐慌從高點明顯回落之後才止穩，而不是在恐慌最高的那天。"}


def low_check(s) -> Optional[Dict]:
    if s is None or len(s) < 30:
        return None
    lows = s.rolling(20).min()
    hit = [i for i in range(len(s) - 15, len(s)) if s.iloc[i] <= lows.iloc[i] + 1e-9]
    since = (len(s) - 1 - hit[-1]) if hit else 99
    nd = int(th()["low_days"])
    lt = "r" if since == 0 else ("y" if since < nd else "g")
    return {"q": "還在創新低嗎？", "light": lt,
            "now": f"加權指數 {float(s.iloc[-1]):,.0f} 點，" + ("今天是 20 天內新低" if since == 0 else f"距上次 20 天內新低 {since} 個交易日"),
            "rule": f"🔴 今天創 20 天內新低；🟡 {nd} 個交易日內創過；🟢 {nd} 個交易日以上沒有再創新低。",
            "why": "止跌通常是先「不再創新低」，再慢慢回穩。還在創新低時，沒人知道底在哪裡。"}


def credit_check(s) -> Optional[Dict]:
    if s is None or len(s) < 25:
        return None
    ch, t = (float(s.iloc[-1]) / float(s.iloc[-21]) - 1) * 100, th()
    r_, y_ = t["credit_red"], t["credit_yellow"]
    lt = "r" if ch <= r_ else ("y" if ch <= y_ else "g")
    return {"q": "信用市場有沒有壞？", "light": lt, "now": f"高收益債 ETF 20 天 {ch:+.1f}%",
            "rule": f"🔴 20 天跌 {_g(-r_)}% 以上；🟡 跌 {_g(-y_)}～{_g(-r_)}%；🟢 跌不到 {_g(-y_)}%。",
            "why": "股票跌但公司債沒事，通常是評價修正；連借錢給公司的人都在逃，比較可能是景氣或金融出問題。"}


def move_check(s) -> Optional[Dict]:
    if s is None or len(s) < 10:
        return None
    now, p5 = float(s.iloc[-1]), float(s.iloc[-6])
    up, t = (now / p5 - 1) * 100, th()
    r_, y_, j_ = t["move_red"], t["move_yellow"], t["move_jump"]
    lt = "r" if now > r_ else ("y" if now > y_ or up >= j_ else "g")
    return {"q": "債市穩不穩？", "light": lt, "now": f"MOVE {now:.0f}，5 天 {up:+.0f}%",
            "rule": f"🔴 高於 {_g(r_)}；🟡 高於 {_g(y_)} 或 5 天升 {_g(j_)}% 以上；🟢 其他。",
            "why": "MOVE 是美債的恐慌指數。債市不穩時，大型機構會一起降低風險，股市很難單獨止穩。"}


def twd_check(s) -> Optional[Dict]:
    if s is None or len(s) < 25:
        return None
    ch, t = (float(s.iloc[-1]) / float(s.iloc[-21]) - 1) * 100, th()
    r_, y_ = t["twd_red"], t["twd_yellow"]
    lt = "r" if ch >= r_ else ("y" if ch >= y_ else "g")
    return {"q": "外資有沒有在把錢匯走？", "light": lt, "now": f"美元兌新台幣 {float(s.iloc[-1]):.2f}，20 天 {ch:+.1f}%",
            "rule": f"🔴 新台幣 20 天貶 {_g(r_)}% 以上；🟡 貶 {_g(y_)}～{_g(r_)}%；🟢 其他。",
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
    try:
        hist += wait_block({k: _s(eng, k) for k in ("^TWII", "^VIX", "HYG", "^MOVE", "TWD=X")})
    except Exception:  # noqa: BLE001
        log.exception("wait-vs-now failed")
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


# ------------------------------------------------------------------ 等燈號轉綠 vs 大跌當天（歷史，2026-11-21）
# 使用者 11-21 問「何時可以進場或出場」。本站不給日期與價位；這裡回答一個能用歷史檢驗的問題：
# 大跌之後，「等五個市場燈號大多轉綠」和「大跌當天」相比，過去差在哪裡（少賺多少、少挨多少跌）。
# 融資燈號沒有長期歷史，只用另外五個（VIX、創新低、高收益債、MOVE、新台幣），同一套門檻。
def green_frame(px: Dict) -> "object":
    import pandas as pd
    tw, vix, hyg, mv, fx = (px.get(k) for k in ("^TWII", "^VIX", "HYG", "^MOVE", "TWD=X"))
    idx = tw.index
    al = lambda s: s.reindex(idx).ffill(limit=3) if s is not None and len(s) else pd.Series(index=idx, dtype=float)  # noqa: E731
    vix, hyg, mv, fx = al(vix), al(hyg), al(mv), al(fx)
    g, t = pd.DataFrame(index=idx), th()           # same thresholds as the lights above
    g["vix"] = (vix < t["vix_line"]) & (vix <= vix.rolling(20).max() * t["vix_off_hi"])
    newlow = tw <= tw.rolling(20).min() + 1e-9
    g["low"] = ~newlow.rolling(int(t["low_days"])).max().astype(bool)
    g["credit"] = (hyg / hyg.shift(20) - 1) * 100 > t["credit_yellow"]
    g["move"] = (mv <= t["move_yellow"]) & ((mv / mv.shift(5) - 1) * 100 < t["move_jump"])
    g["twd"] = (fx / fx.shift(20) - 1) * 100 < t["twd_yellow"]
    have = pd.DataFrame({"vix": vix.notna(), "low": tw.notna(), "credit": hyg.shift(20).notna(), "move": mv.shift(5).notna(), "twd": fx.shift(20).notna()})
    return g.where(have), have


def wait_vs_now(px: Dict, need: int = 4, look: int = 120) -> List[Dict]:
    tw = px.get("^TWII")
    if tw is None or len(tw) < 300:
        return []
    g, have = green_frame(px)
    n_ok = have.sum(axis=1)
    n_g = (g == True).sum(axis=1)  # noqa: E712  (NaN = no data → not green)
    out = []
    for e in drops(tw):
        i = tw.index.get_loc(e["date"])
        if n_ok.iloc[i] < 5:                         # only episodes where all five measures existed (2007 onward)
            continue
        j = next((k for k in range(i + 1, min(i + look, len(tw))) if n_g.iloc[k] >= need), None)
        c0 = float(tw.iloc[i])
        row = {"date": e["date"], "drop": e["drop"], "wait": None, "open": i + look > len(tw),
               "dd_now": min(0.0, float(tw.iloc[i + 1:i + 61].min()) / c0 - 1) if i + 61 <= len(tw) else None}
        if j is not None:
            cj = float(tw.iloc[j])
            row.update({"wait": j - i, "green": tw.index[j].strftime("%Y-%m-%d"), "move": cj / c0 - 1,
                        "dd_before": float(tw.iloc[i:j + 1].min()) / c0 - 1,
                        "f60_now": float(tw.iloc[i + 60]) / c0 - 1 if i + 60 < len(tw) else None,
                        "f60_wait": float(tw.iloc[j + 60]) / cj - 1 if j + 60 < len(tw) else None,
                        "dd_after": min(0.0, float(tw.iloc[j + 1:j + 61].min()) / cj - 1) if j + 1 < len(tw) else None})
        out.append(row)
    return out


def wait_block(px: Dict) -> str:
    rows = wait_vs_now(px)
    done = [r for r in rows if r["wait"] is not None and r.get("f60_wait") is not None]
    if len(done) < 4:
        return ""
    mv = [r["move"] for r in done]
    dd = [r["dd_before"] for r in done]
    ddw = [r["dd_after"] for r in done if r.get("dd_after") is not None]
    cheaper = sum(m < 0 for m in mv)
    lst = "".join(
        f'<li>{r["date"]}（當天 {r["drop"]:.1f}%）：' + (
            f'等了 {r["wait"]} 個交易日、{r["green"]} 轉綠；那時指數比大跌當天 {_pc(r["move"])}，'
            + ("等待期間沒有再跌破大跌當天收盤；" if r["dd_before"] >= 0 else f'等待期間最深 {_pc(r["dd_before"])}；')
            + (f'轉綠後 60 天 {_pc(r["f60_wait"])}，' if r.get("f60_wait") is not None else "轉綠後還不到 60 天，")
            + (_dd(r["dd_after"]).replace("之後 60 天內", "轉綠後 60 天內") if r.get("dd_after") is not None else "")
            if r["wait"] is not None else ("還沒轉綠（進行中）" if r.get("open") else "120 個交易日內都沒有轉綠")) + "</li>" for r in reversed(rows))
    pend = [r for r in rows if r["wait"] is None or r.get("f60_wait") is None]
    ddn = [r["dd_now"] for r in done if r.get("dd_now") is not None]
    m_mv, m_ddw, m_ddn = _med(mv), (_med(ddw) if ddw else None), (_med(ddn) if ddn else None)
    if cheaper * 2 < len(done) and m_ddw is not None and m_ddn is not None and m_ddw <= m_ddn + 0.01:
        verdict = ("<b>結論：這套燈號在歷史上不是好的「等待訊號」。</b>轉綠時指數多半已經比大跌當天高，而且轉綠之後一樣會再跌，"
                   "等待沒有讓人少挨跌。它比較適合用來看「被迫賣壓和恐慌是不是在退」，不適合拿來抓時間點。")
    elif cheaper * 2 >= len(done):
        verdict = "<b>結論：等待多半買得比較便宜。</b>但樣本少，不能當成規則。"
    else:
        verdict = "<b>結論：等待的代價是轉綠時通常已經比較貴，好處是之後少挨一些跌；兩種都有代價。</b>"
    return (f'<h3>如果等燈號大多轉綠，歷史上差在哪裡</h3><p class="small">2007 年以來（五個燈號都有資料）台股單日跌 5% 以上、'
            f'而且之後 120 天內有轉綠（五個裡至少四個 🟢）的 {len(done)} 次：轉綠那天的指數比大跌當天<b>更低的有 {cheaper} 次、更高的有 {len(done) - cheaper} 次</b>，'
            f'中位數 {_pc(m_mv)}；從大跌當天到轉綠之間，中位數最深再跌 {_pc(_med(dd))}。'
            + (f'轉綠之後 60 天內，中位數最深再跌 {_pc(m_ddw)}；如果在大跌當天就算，之後 60 天內中位數最深再跌 {_pc(m_ddn)}。' if m_ddw is not None and m_ddn is not None else "")
            + f'</p><p class="small">{verdict}</p>'
            + (f'<p class="small muted">還在進行中、或 120 天內沒有轉綠的：{"、".join(r["date"] for r in pend)}。</p>' if pend else "")
            + f'<details class="sgx"><summary>看每一次（{len(rows)} 次）</summary><ul class="small">{lst}</ul></details>'
            '<p class="small muted">歷史樣本少（十幾次），不能當成規則；只用收盤價、不含股息與手續費；融資燈號沒有長期資料，沒有算進去。</p>')

"""AI 解讀（財經數據公布後、科技財報公布後、財報季總結）——公開網站與 Discord 共用，結果快取，同一事件只寫一次。

只把事件本身的數字、規則劇本、歷史反應統計與當天市場變動交給模型；系統提示禁止任何買賣或部位建議，輸出再經
一次關鍵字過濾。沒有可用的 AI 時就跳過，頁面照樣顯示規則劇本與統計。"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR

log = logging.getLogger(__name__)
_FILE = DATA_DIR / "econ_ai.json"

SYSTEM = """你是華爾街總經與科技產業分析師，為公開的市場情報網頁撰寫簡短解讀，讀者是一般大眾。
【鐵律】
1. 只能使用提供的數字與事實，沒有的就不提，絕不編造數據、引述或公司說法。
2. 這是市場與數據描述，不是投資建議：不得提出買進、賣出、加碼、減碼、停損、目標價、部位比例等任何操作建議。
3. 說明「數據代表什麼、和預期差多少、通常怎麼影響利率／美元／股市與科技半導體、接下來要看什麼」。
4. 歷史統計樣本小，要誠實說明只是過去平均、不代表這次。
5. 台灣繁體中文、台灣用語，冷靜精準；金融術語可保留英文。純文字段落，不要標題、不要條列超過 4 點。"""

ADVICE_RX = re.compile(r"(減碼|加碼|停損|停利|買進|賣出|建議(?:買|賣|持有|布局|配置)|目標價|部位.{0,6}(?:調整|降低|提高))")


def load() -> Dict[str, Dict]:
    try:
        if _FILE.exists():
            return json.loads(_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    return {}


def _save(d: Dict[str, Dict]) -> None:
    try:
        keep = dict(sorted(d.items(), key=lambda kv: kv[1].get("ts", 0))[-400:])
        _FILE.write_text(json.dumps(keep, ensure_ascii=False), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log.warning("econ AI cache not saved: %s", e)


def scrub(text: str) -> str:
    return "\n".join(ln for ln in text.splitlines() if not ADVICE_RX.search(ln)).strip()


def _fmt(v, n=2, sign=False) -> str:
    if v is None:
        return "—"
    return f"{v:+.{n}f}" if sign else f"{v:.{n}f}"


def event_prompt(e: Dict) -> str:
    L = [f"事件：{e['zh']}（美東 {e['date']} {e.get('et', '')}）"]
    for r in e.get("rows", []):
        L.append(f"- {r['label']}：公布 {r['actual'] or '尚未公布'}，預期 {r['cons'] or '—'}，前值 {r['prev'] or '—'}")
    if e.get("dir_label"):
        L.append(f"判定：{e['dir_label'][0]}")
    sc = e.get("scen") or {}
    if sc:
        L.append(f"這個數據的意義：{sc['why']['zh']}")
        d = e.get("dir") or "inline"
        L.append(f"對應的規則劇本（{d}）：{sc[d]['zh']}")
        L.append(f"接下來要看：{sc['watch']['zh']}")
    st = (e.get("stats") or {}).get("by", {}).get(e.get("dir") or "", {})
    if st:
        L.append(f"過去約兩年同類『{(e.get('dir_label') or ('', ''))[0]}』共 {st['n']} 次，當天平均：那指 100 {_fmt(st.get('^NDX'), 2, True)}%、"
                 f"費半 {_fmt(st.get('^SOX'), 2, True)}%、10 年殖利率 {_fmt(st.get('^TNX'), 1, True)}bp、美元 {_fmt(st.get('DX-Y.NYB'), 2, True)}%")
    mv = e.get("move") or {}
    if any(v is not None for v in mv.values()):
        L.append(f"公布當天收盤變動：那指 100 {_fmt(mv.get('^NDX'), 2, True)}%、費半 {_fmt(mv.get('^SOX'), 2, True)}%、"
                 f"10 年殖利率 {_fmt(mv.get('^TNX'), 1, True)}bp、美元 {_fmt(mv.get('DX-Y.NYB'), 2, True)}%")
    if e.get("ctx"):
        L.append(f"目前背景：{e['ctx']}")
    L.append("請寫 180–280 字解讀：這次數據與預期的差距代表什麼、對降息路徑與利率美元的意義、對美股科技與半導體（以及台股電子）的可能影響、下一個要盯的數據。")
    return "\n".join(L)


def earnings_prompt(r: Dict) -> str:
    s = r["s"]
    L = [f"公司：{r['name']}（{r['sym']}，族群 {r['theme']}），最新一季（季末 {r.get('end', '—')}）"]
    L.append(f"營收 {_fmt((r.get('rev') or 0) / 1e9, 2)} 十億美元，年增 {_fmt(r.get('rev_yoy'), 1)}%，較上季年增率變化 {_fmt(r.get('accel'), 1, True)}pp，"
             f"季增 {_fmt(r.get('rev_qoq'), 1)}%")
    L.append(f"毛利率 {_fmt(r.get('gm'), 1)}%（年變化 {_fmt(r.get('gm_yoy'), 1, True)}pp）、營益率 {_fmt(r.get('om'), 1)}%（年變化 {_fmt(r.get('om_yoy'), 1, True)}pp）、"
             f"淨利率 {_fmt(r.get('nm'), 1)}%、EPS {_fmt(r.get('eps'), 2)}（年增 {_fmt(r.get('eps_yoy'), 1)}%）、研發占營收 {_fmt(r.get('rnd'), 1)}%")
    if s.get("rows"):
        L.append("近幾季 EPS 實際 vs 預期：" + "；".join(f"{x['fq']} {x['eps']} vs {x['cons']}（{_fmt(x['surp'], 1, True)}%）" for x in s["rows"]))
    if s.get("react_last") is not None:
        L.append(f"最近一次財報前後兩日股價 {_fmt(s['react_last'], 1, True)}%，過去平均波動 ±{_fmt(s.get('react_avg'), 1)}%")
    if r.get("next"):
        n = r["next"]
        L.append(f"下次財報 {n['date']}，EPS 預期 {n['eps_f']}（去年同期 {n['eps_ly']}）")
    L.append("規則標籤：" + "、".join(t for t, _ in r.get("tags", [])))
    L.append("請寫 150–250 字：這一季的成長品質（量、價、利潤率）、和預期相比如何、市場反應說明了什麼、下一季要看什麼。")
    return "\n".join(L)


def season_prompt(res: Dict) -> str:
    b = res["season"]
    L = [f"精選池科技／半導體近 45 天公布 {b['n']} 家，{b['beats']} 家 EPS 優於預期，平均驚喜 {_fmt(b.get('avg_surp'), 1, True)}%，"
         f"營收年增中位數 {_fmt(b.get('rev_yoy'), 0)}%，財報後兩日平均 {_fmt(b.get('avg_react'), 1, True)}%"]
    for g in res["groups"]:
        L.append(f"{g['theme']}（{g['n']} 家）：營收年增中位數 {_fmt(g.get('rev_yoy'), 0)}%、毛利率年變化中位數 {_fmt(g.get('gm_yoy'), 1, True)}pp、"
                 f"上季 EPS 優於預期比例 {_fmt(g.get('beat'), 0)}%；動能領先：{'、'.join(g['leaders'])}")
    for r in res["rows"][:12]:
        L.append(f"{r['name']}：{r['verdict']}")
    L.append("請寫 250–380 字的科技與半導體財報季總結：哪個族群最強或轉弱、AI 相關需求在數字上的證據、利潤率趨勢、值得注意的分歧；不要給操作建議。")
    return "\n".join(L)


async def _gen(key: str, prompt: str, cache: Dict[str, Dict], max_tokens: int = 900) -> Optional[Tuple[str, str]]:
    from . import llm
    text, name = await llm.complete(SYSTEM, prompt, max_tokens)
    if name == "none" or not text or text.startswith("⚠️"):
        return None
    text = scrub(text.replace("（輸出達長度上限，內容可能不完整）", ""))
    cache[key] = {"text": text, "engine": name, "ts": time.time()}
    _save(cache)
    return text, name


async def generate(eng, limit: int = 6) -> int:
    """Write the missing notes: released key events (last 3 days), curated tech reports (last 10 days), the season roll-up (daily)."""
    cache = load()
    n = 0
    ev = getattr(eng, "econ_view", None) or {}
    for e in (ev.get("events") or [])[::-1]:
        if n >= limit:
            break
        if not e.get("released") or e["imp"] < 2 or not e.get("rows") or e["id"] in cache or e.get("move") is None:
            continue                                   # "move" is only set for releases of the last 3 days
        if await _gen(e["id"], event_prompt(e), cache):
            n += 1
    te = getattr(eng, "techearn", None) or {}
    import datetime as _dt
    lim = (_dt.date.fromisoformat(te.get("asof", "2000-01-01")) - _dt.timedelta(days=10)).isoformat() if te.get("asof") else "9999"
    for r in te.get("rows") or []:
        if n >= limit:
            break
        d = r["s"].get("last_date")
        k = f"earn:{r['sym']}:{d}"
        if not d or d < lim or k in cache or r.get("rev_yoy") is None:
            continue
        if await _gen(k, earnings_prompt(r), cache):
            n += 1
    if te.get("available") and te["season"].get("n"):
        k = f"season:{te['asof']}"
        if k not in cache and await _gen(k, season_prompt(te), cache, 1400):
            n += 1
    return n


def attach(eng) -> None:
    """Copy cached notes onto the current results (no API calls)."""
    cache = load()
    ev = getattr(eng, "econ_view", None) or {}
    for e in ev.get("events") or []:
        if e["id"] in cache:
            e["ai"] = cache[e["id"]]
    te = getattr(eng, "techearn", None) or {}
    for r in te.get("rows") or []:
        k = f"earn:{r['sym']}:{r['s'].get('last_date')}"
        if k in cache:
            r["ai"] = cache[k]
    if te.get("asof"):
        ks = sorted(k for k in cache if k.startswith("season:"))
        if ks:
            te["ai_season"] = cache[ks[-1]]

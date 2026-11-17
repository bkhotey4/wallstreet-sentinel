"""本週串起來看（2026-11-17）：把網站各處已經抓到的事件排成一張時間表，找出「同一家公司、在不同種類的事件裡重複出現」的交集。

使用者 11-17：「不只這次 anthropic 或輝達……你是不是也可以建立這套機制，並延伸思考」「有時候不會只有表象」。
那週輝達同時出現在：人事（8-K 5.02，文件沒寫原因、立即生效、同日換董事長）、政策（BIS 由財政部與國安會主導的遠端存取規則，
主題是出口管制／半導體）、IPO（Anthropic 同步私募 100 億美元）、財報（11/17 盤後）。每一則單看都是新聞，串起來才像一個故事。

這支只做「程式能確定的部分」（不用 AI）：
  1 事件：SEC 重大申報與人事（含「沒說的」標記）、財報日、聯邦公報與 BIS 新聞稿（政策主題 → 產業鏈公司）、
          IPO（即將定價的公司、同步私募的出資者）——過去 10 天到未來 7 天
  2 交集：同一個代號在 ≥2 種事件裡出現 → 一組，依「種類數 × 重要度」排序
  3 輸出 data_cache/econ_dots.json（econ_* 會被 CI 快取保存）與網站卡片；每日排程（wss-daily-maintain-expand）挑前幾組讀原始文件、寫假設
     （research_feed/dots_read.json：支持的證據／反對或不確定／什麼消息能證實），卡片一起顯示。
交集只代表「值得一起看」，不代表有因果；假設由每日排程寫，而且要標明是假設。"""
from __future__ import annotations

import json
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
PAST, AHEAD = 10, 7
EARN_FLOOR = 1e11                                           # earnings of companies at least this big join the timeline
KIND_ZH = {"sec": "SEC 申報", "earn": "財報", "policy": "政策", "ipo": "IPO", "pp": "出資 IPO"}
WEIGHT = {"sec": 3, "policy": 3, "pp": 2, "ipo": 2, "earn": 1}
READ = ROOT / "research_feed" / "dots_read.json"            # written by the daily task (public repo)


def _d(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).date().isoformat()


def topic_syms() -> Dict[str, List[str]]:
    """Policy topic → companies on the AI supply chain that it hits first."""
    from wsb.analytics.ai_chain import CHAIN
    g = {zh: list(s) for zh, _en, s in CHAIN}
    chips = g.get("核心晶片", []) + g.get("半導體設備", []) + g.get("記憶體", [])
    return {"出口管制／半導體": chips + g.get("甲骨文與新雲端", []) + g.get("伺服器與組裝", []),
            "人工智慧": chips + g.get("雲端巨頭", []) + g.get("甲骨文與新雲端", []), "中國": chips}


def name_index(names: Dict[str, tuple]) -> Dict[str, str]:
    """{lower-case name word: sym} from the site's US list ({sym: (中文, English)}) for matching prospectus names."""
    out: Dict[str, str] = {}
    alias = {"GOOGL": ["google", "alphabet"], "TSM": ["tsmc", "taiwan semiconductor"], "META": ["meta", "facebook"]}
    for sym, v in names.items():
        en = str(v[1] if len(v) > 1 else "").lower()
        first = re.split(r"[\s,.(]", en)[0] if en else ""
        for k in [first] + alias.get(sym, []):
            if len(k) >= 4 and k not in out:
                out[k] = sym
    return out


def events(now: float, names: Dict[str, tuple], sof: Dict, days: Dict, fr: Dict, bis: Dict, ipo: Dict) -> List[Dict]:
    lo, hi = _d(now - PAST * 86400), _d(now + AHEAD * 86400)
    zh = {s: v[0] for s, v in names.items()}
    out: List[Dict] = []
    for a in sof.get("alerts") or []:                                     # SEC 重大申報（5.02 人事、13D、其他重大項）
        if lo <= _d(a["ts"]) <= hi:
            out.append({"kind": "sec", "date": _d(a["ts"]), "syms": [a["sym"]], "t": a.get("t") or "", "url": a.get("url"),
                        "flags": a.get("flags") or []})
    for day, v in days.items():                                           # 財報（市值 1,000 億美元以上）
        if lo <= day <= hi:
            for r in (v.get("rows") if isinstance(v, dict) else None) or []:
                if float(r.get("mcap") or 0) >= EARN_FLOOR and r.get("sym"):
                    out.append({"kind": "earn", "date": day, "syms": [r["sym"]], "t": f"{zh.get(r['sym'], r.get('name') or r['sym'])}財報"})
    tsyms = topic_syms()
    for x in fr.get("docs") or []:                                        # 聯邦公報正式刊登
        if lo <= (x.get("date") or "") <= hi and x.get("topic") in tsyms and not x.get("routine"):
            out.append({"kind": "policy", "date": x["date"], "syms": tsyms[x["topic"]], "t": f"聯邦公報：{x.get('title', '')[:90]}",
                        "url": x.get("url"), "topic": x["topic"]})
    from wsb.data import bis_news as BN
    for x in bis.get("items") or []:                                      # BIS 新聞稿（宣布）
        c = BN.classify(x)
        if c and lo <= _d(x["ts"]) <= hi and c.get("topic") in tsyms:
            out.append({"kind": "policy", "date": _d(x["ts"]), "syms": tsyms[c["topic"]], "t": f"BIS 宣布：{x['title'][:90]}",
                        "url": x["url"], "topic": c["topic"]})
    idx = name_index(names)
    for f in ((ipo.get("us") or {}).get("filers") or {}).values():       # IPO：即將定價的公司與同步私募出資者
        cv = f.get("cover") or {}
        late = max((y for y in (f.get("a12"), f.get("eff"), f.get("last")) if y), default="")
        if not (cv.get("pp") or f.get("a12")) or not (lo <= late <= hi) or f.get("priced"):
            continue
        nm = (f.get("name") or "").split(",")[0]
        if f.get("a12"):
            out.append({"kind": "ipo", "date": f["a12"], "syms": [cv.get("symbol") or nm], "t": f"{nm} 向交易所登記股票、即將上市"})
        for p in cv.get("pp") or []:
            w = re.split(r"[\s,.(]", p["name"].lower())[0]
            sym = idx.get(w)
            if sym:
                out.append({"kind": "pp", "date": late, "syms": [sym],
                            "t": f"{zh.get(sym, p['name'])}出資 {nm} IPO 同步私募 {p['usd'] / 1e8:,.0f} 億美元"})
    return out


def remember(evs: List[Dict], now: float, path: Path, keep_days: int = 30) -> List[Dict]:
    """Merge with the event archive: the sources keep only a few days (SEC alerts: 3), the timeline needs PAST days —
    NVIDIA's 11/12 resignation had already aged out of the SEC alert list by 11/17."""
    try:
        arc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError):
        arc = {}
    for e in evs:
        arc[f"{e['kind']}|{e['date']}|{e['t'][:80]}"] = e
    cut, lo, hi = _d(now - keep_days * 86400), _d(now - PAST * 86400), _d(now + AHEAD * 86400)
    arc = {k: e for k, e in arc.items() if e["date"] >= cut}
    path.write_text(json.dumps(arc, ensure_ascii=False), encoding="utf-8")
    return [e for e in arc.values() if lo <= e["date"] <= hi]


def clusters(evs: List[Dict], zh: Dict[str, str], min_kinds: int = 2) -> List[Dict]:
    """Companies that show up in ≥ min_kinds different kinds of events, most kinds and weight first.  A policy event that
    hits a whole chain counts only for companies that also have an event of their own."""
    by: Dict[str, List[Dict]] = {}
    seen = set()
    for e in evs:
        if e["kind"] in ("pp", "earn", "ipo"):              # one per company and day (a hand-added copy and the program's own)
            k = (e["kind"], e["date"], tuple(e["syms"]))
            if k in seen:
                continue
            seen.add(k)
        for s in e["syms"]:
            by.setdefault(s, []).append(e)
    out = []
    for s, es in by.items():
        kinds = {e["kind"] for e in es}
        own = kinds - {"policy"}
        if len(kinds) < min_kinds or not own:
            continue
        flags = sorted({f for e in es for f in e.get("flags") or []})
        score = sum(WEIGHT[k] for k in kinds) + len(flags)
        out.append({"sym": s, "zh": zh.get(s, s), "kinds": sorted(kinds, key=lambda k: -WEIGHT[k]), "flags": flags, "score": score,
                    "events": sorted(es, key=lambda e: e["date"])})
    return sorted(out, key=lambda c: (-c["score"], c["sym"]))


def build(now: Optional[float] = None) -> Dict:
    from wsb.config import DATA_DIR
    from wsb.data import bis_news as BN
    from wsb.data import fed_register as FR
    from wsb.data import ipo_data as I
    from wsb.data import sec_officers as SOF
    from wsb.data.stocks import universe
    now = now or time.time()
    names = (universe().get("us") or {}).get("symbols") or {}
    try:
        days = json.loads((DATA_DIR / "earn_days.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        days = {}
    evs = remember(events(now, names, SOF.load(), days, FR.load(), BN.load(), I.load()), now, DATA_DIR / "econ_dots_events.json")
    cl = clusters(evs, {s: v[0] for s, v in names.items()})
    out = {"ts": int(now), "n_events": len(evs), "clusters": cl[:12]}
    (DATA_DIR / "econ_dots.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def summary(d: Dict) -> str:
    lines = [f"事件 {d['n_events']} 則；交集 {len(d['clusters'])} 組："]
    for c in d["clusters"][:8]:
        lines.append(f"- {c['zh']}（{c['sym']}）：{'、'.join(KIND_ZH[k] for k in c['kinds'])}" + (f"；文件{'、'.join(c['flags'])}" if c["flags"] else ""))
        for e in c["events"]:
            lines.append(f"    {e['date']} [{KIND_ZH[e['kind']]}] {e['t'][:100]}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    print(summary(build()))

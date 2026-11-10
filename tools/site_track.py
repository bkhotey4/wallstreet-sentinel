"""全站預測成績單 (風險模型): how right the site's own calls have been, all read from stored records —
earnings previews (research_feed/earn_preview.json), the implied-move log, the crash model's walk-forward test, the alarm-rule
replay and the live alert log.  Every line has a sample size, hits, a baseline and false alarms where they mean something.
Below MIN_N a line says 樣本太少 and shows counts only; a verdict needs the 90% interval of the hit rate to clear the baseline."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tools.sitekit import T, card, esc, guard_safe

MIN_N = 20
VERDICT = {"win": ("贏過基準", "Beats baseline", "up"), "lose": ("輸給基準", "Below baseline", "dn"), "tie": ("和基準差不多", "About the baseline", ""),
           "small": ("樣本太少", "Too few cases", "muted"), "none": ("還沒有紀錄", "No record yet", "muted")}


def _verdict(k: float, n: float, base: Optional[float]) -> str:
    from wsb.analytics.implied_log import _wilson
    if not n:
        return "none"
    if n < MIN_N or base is None:
        return "small"
    lo, hi = _wilson(k, n)
    return "win" if lo > base else "lose" if hi < base else "tie"


def _row(zh: str, en: str, n: int, hits: int, base: Optional[float], base_zh: str, base_en: str, false=None, read: str = "",
         base_n: Optional[int] = None) -> Dict:
    """base_n: the baseline's own count, when it is measured on this same sample (shown as a count while the sample is small)."""
    return {"zh": zh, "en": en, "n": n, "hits": hits, "base": base, "base_zh": base_zh, "base_en": base_en, "false": false,
            "read": read, "base_n": base_n, "v": _verdict(hits, n, base)}


def preview_row() -> Dict:
    """Highest-probability option vs what happened; baseline = always saying 維持 on the same reports."""
    from tools import site_preview as SPV
    items = [x for x in (SPV.load().get("items") or []) if isinstance(x, dict)]
    done = [(x, SPV._probs(x.get("probs"))) for x in items if x.get("outcome") in SPV.OUTS]
    done = [(x, p) for x, p in done if p]
    sc = SPV.score(items) or {"n": 0, "hits": 0, "brier": None}
    stay = sum(x["outcome"] == "維持" for x, _p in done)
    tops = [(x, max(p, key=p.get), p) for x, p in done]
    false = sum(t != "維持" and x["outcome"] == "維持" for x, t, _p in tops)
    r = _row("財報前瞻：最高機率的選項", "Earnings preview: top option", sc["n"], sc["hits"], stay / sc["n"] * 100 if sc["n"] else None,
             "一律猜「維持」", "Always 維持", false, "誤報＝猜會上修或下修，結果維持", stay)
    r["miss"] = [{"name": x.get("name") or x.get("sym"), "date": x.get("date"), "top": t, "pct": p[t], "out": x["outcome"]}
                 for x, t, p in tops if t != x["outcome"]]
    r["brier"] = sc["brier"]
    return r


def implied_row() -> Dict:
    from wsb.analytics import implied_log as IL
    st = IL.stats(IL.load())
    n = st.get("n", 0)
    fair = 100 - st["fair_over"]
    r = _row("財報跳空：實際波動在選擇權預期內", "Earnings move within implied", n, n - st.get("over", 0), fair,
             f"定價剛好時約 {fair:.0f}%", f"Fair pricing ≈{fair:.0f}%", None, "這一項評的是選擇權市場，不是本站")
    r["pending"], r["start"] = st.get("pending", 0), st.get("start")
    r["over"] = [{"name": x.get("name") or x.get("sym"), "date": x.get("date"), "mv": x.get("mv"), "act": x.get("act")}
                 for x in st.get("recent") or [] if abs(x["act"]) > x["mv"]]
    return r


def crash_rows(eng) -> List[Dict]:
    """Out-of-sample walk-forward record of the model behind the shown probability, on non-overlapping windows."""
    out = []
    for h in (getattr(eng, "lab", None) or {}).get("horizons", []) or []:
        m = h.get("base_model") or {}
        t = m.get("track")
        if not t or t.get("base_rate") is None:
            continue
        d, dd = h.get("days"), float(h.get("drawdown_pct") or 0)
        r = _row(f"崩跌機率：{d} 日內跌 ≥{dd:.0f}%（機率偏高時）", f"Crash odds: ≥{dd:.0f}% in {d}d (when flagged)", t["alarm"], t["hits"], t["base_rate"],
                 f"任何時候 {t['base_rate']:.0f}%", f"Any time {t['base_rate']:.0f}%", t["alarm"] - t["hits"], f"另有 {t['misses']} 次大跌事前機率不高")
        r.update({"windows": t["n"], "events": t["events"], "skill": m.get("skill"), "auc": m.get("auc_oos"),
                  "calib": m.get("calibration") or [], "days": d, "dd": dd})
        out.append(r)
    return out


def rules_row(eng) -> Optional[Dict]:
    """The alarm rules re-run on history (the replay behind 大盤警報規則回測), added up; in-sample."""
    rb = (getattr(eng, "sx", None) or {}).get("rules") or {}
    rows = [r for r in rb.get("rows") or [] if r.get("n") and r.get("dd5") is not None and r.get("base_dd5") is not None]
    if not rows:
        return None
    n = sum(r["n"] for r in rows)
    hits = round(sum(r["n"] * r["dd5"] / 100 for r in rows))
    base = sum(r["n"] * r["base_dd5"] for r in rows) / n
    x = _row("大盤警報規則（歷史重跑，20 日內再跌 5%）", "Alarm rules, replayed (further 5% fall in 20d)", n, hits, base,
             f"任何一天 {base:.0f}%", f"Any day {base:.0f}%", n - hits, "歷史重跑不是即時紀錄；同一段行情可能被多條規則同時算到")
    x["rules"] = rows
    return x


SEED = Path(__file__).resolve().parents[1] / "research_feed" / "alert_track_seed.json"   # public site repo root, never synced over


def _track_file() -> Path:
    from wsb.config import DATA_DIR
    return DATA_DIR / "econ_alert_track.json"          # econ_* → kept by the Actions cache between builds


def _load(path: Path) -> List[list]:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("rows") or [] if path.exists() else []
    except Exception:  # noqa: BLE001
        return []


def sanitize(rows: List[tuple]) -> List[list]:
    """Public form of a logged alert: time, rule family only (no ticker, no title), severity, S&P 500 level."""
    from wsb.analytics.scorecard import FAMILIES
    out = []
    for ts, key, kind, sev, _title, spx, _ssi in rows:
        pre = next((p for p, _ in FAMILIES if key.startswith(p)), "other:")
        out.append([round(float(ts)), pre, kind, "🚨" if str(sev).startswith("🚨") else "⚠️", spx])
    return out


def log_site_alerts(eng, now: Optional[float] = None) -> int:
    """Each build: remember the first time every red (risk) pop-up alert appeared on the site, with the S&P 500 level.
    Gives the Actions-built site its own alert record — the bot's log lives only on the owner's computer."""
    items = [x for x in ((getattr(eng, "web_alerts", None) or {}).get("items") or [])
             if x.get("lv") == "alert" and x.get("tone", "risk") == "risk" and x.get("key")]
    if not items:
        return 0
    f = _track_file()
    rows = _load(f)
    seen = {r[1] for r in rows}
    try:
        spx = float(eng.market.series("^GSPC").dropna().iloc[-1])
    except Exception:  # noqa: BLE001
        spx = None
    now = now or time.time()
    new = [[round(now), x["key"], "risk", "⚠️", spx] for x in items if x["key"] not in seen]
    if new:
        rows = [r for r in rows + new if r[0] > now - 400 * 86400]
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps({"rows": rows}, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, f)
    return len(new)


def _alert_rows() -> Tuple[List[tuple], str]:
    """Rows for the scorecard and where they came from: the bot's own log when it exists (owner's computer), else the
    site's record (Actions) plus the bot history published once as a sanitized seed."""
    from wsb import store
    try:
        own = [r for r in store.tracked_alerts(365) if not store.is_private_alert(r[1])]     # holdings-derived alerts stay private
    except Exception:  # noqa: BLE001
        own = []
    if own:
        return own, "bot"
    site = _load(_track_file())
    seed = _load(SEED)
    cut = min([r[0] for r in site] or [time.time()])
    rows = [r for r in seed if r[0] < cut] + site
    return [(r[0], r[1], r[2], r[3], "", r[4], None) for r in sorted(rows) if r[0] > time.time() - 365 * 86400], "site"


def alert_rows(eng) -> List[Dict]:
    """Alerts actually sent and logged, S&P 500 afterwards, merged into episodes (wsb.analytics.scorecard)."""
    try:
        from wsb.analytics import scorecard as SC
        rows, src = _alert_rows()
        res = SC.evaluate(rows, eng.market.series("^GSPC")) if rows else {}
    except Exception:  # noqa: BLE001
        res = {}
    out = []
    for h in res.get("horizons") or []:
        days = h["days"]
        p = (((res.get("summary") or {}).get("risk") or {}).get("by_horizon") or {}).get(days) or {}
        n = p.get("episodes", 0)
        base = p.get("base_rate")
        dd = h["drawdown"] * 100
        if p.get("hit_rate") is None and n:
            continue                                  # no graded result yet: do not show it as all misses
        r = _row(f"已發出的風險警報：{days} 日內跌 ≥{dd:.0f}%", f"Sent alerts: ≥{dd:.0f}% in {days}d", n, round((p.get("hit_rate") or 0) * n / 100), base,
                 f"任何一天 {base:.0f}%" if base is not None else "—", f"Any day {base:.0f}%" if base is not None else "—", None,
                 "" if src == "bot" else "網站自己記的紅色警報（加上機器人過去的紀錄），同一天內的多次警報算一次")
        r["false"] = n - r["hits"]
        r["fam"] = [{"name": k, "n": ((v.get("by_horizon") or {}).get(days) or {}).get("episodes", 0),
                     "rate": ((v.get("by_horizon") or {}).get(days) or {}).get("hit_rate")} for k, v in (res.get("families") or {}).items()]
        out.append(r)
    return out


def rows_all(eng) -> List[Dict]:
    out: List[Dict] = []
    for f in (lambda: [preview_row()], lambda: [implied_row()], lambda: crash_rows(eng), lambda: [r for r in [rules_row(eng)] if r], lambda: alert_rows(eng)):
        try:
            out += f()
        except Exception:  # noqa: BLE001
            pass                                      # one broken record must not hide the others
    if not any("fam" in r for r in out):              # say it is missing rather than drop the line
        out.append(_row("已發出的風險警報", "Sent alerts", 0, 0, None, "—", "—", None, "這次更新讀不到警報紀錄"))
    return out


def _e(x) -> str:
    return esc(guard_safe(str(x if x is not None else "—")))


def _tr(r: Dict) -> str:
    zh, en, c = VERDICT[r["v"]]
    small = r["v"] in ("small", "none")
    rate = T(zh, en) if small else f'{r["hits"] / r["n"] * 100:.0f}%'
    if r["base_n"] is not None and r["n"]:
        base = f'{_e(r["base_zh"])} ' + (f'{r["base_n"]}/{r["n"]}' if small else f'{r["base_n"] / r["n"] * 100:.0f}%')
    else:
        base = T(guard_safe(r["base_zh"]), r["base_en"])
    false = "—" if r["false"] is None or not r["n"] else str(r["false"])
    read = f'<div class="small muted">{_e(r["read"])}</div>' if r["read"] else ""
    return (f'<tr><td>{T(guard_safe(r["zh"]), r["en"])}{read}</td><td class="r">{r["n"]}</td><td class="r">{r["hits"]}</td><td class="r">{rate}</td>'
            f'<td>{base}</td><td class="r">{false}</td><td class="{c}">{T(zh, en)}</td></tr>')


def _lead(rows: List[Dict]) -> Tuple[str, str]:
    has = [r for r in rows if r["v"] != "none"]
    win, lose, tie = (sum(r["v"] == k for r in rows) for k in ("win", "lose", "tie"))
    small = sum(r["v"] == "small" for r in rows)
    if not has:
        return "一句話看懂：目前還沒有可以對答案的紀錄。", "In short: nothing can be graded yet."
    if not win + lose + tie:
        return f"一句話看懂：有 {len(has)} 項已有紀錄，但樣本都太少，還不能說準不準。", f"In short: {len(has)} item(s) on record, all with too few cases to judge."
    return (f"一句話看懂：{win + lose + tie} 項樣本夠，其中 {win} 項贏過基準、{tie} 項和基準差不多、{lose} 項輸給基準；另有 {small} 項樣本太少。",
            f"In short: of {win + lose + tie} gradable items, {win} beat the baseline, {tie} match it, {lose} fall short; {small} have too few cases.")


def _preview_detail(r: Dict) -> str:
    li = "".join(f'<li>{_e(m["name"])} {_e(m["date"])}：最高機率是「{_e(m["top"])}」（{m["pct"]:.0f}%），結果是「{_e(m["out"])}」</li>' for m in r.get("miss") or [])
    b = (f'<p class="small">Brier 分數 {r["brier"]:.2f}（0 是完美，每次都猜三分之一是 0.67，越低越準）。</p>' if r.get("brier") is not None and r["n"] >= MIN_N else "")
    return f'<h3>{T("財報前瞻沒猜中的", "Preview misses")}</h3><ul class="small">{li}</ul>{b}' if li or b else ""


def _implied_detail(r: Dict) -> str:
    li = "".join(f'<li>{_e(m["name"])} {_e(m["date"])}：預期 ±{m["mv"]:.1f}%，實際 {m["act"]:+.1f}%</li>' for m in (r.get("over") or [])[:8])
    wait = f'等待公布 {r.get("pending", 0)} 次' + (f'，紀錄從 {_e(r["start"])} 開始。' if r.get("start") else "。")
    return f'<h3>{T("財報跳空超出預期的", "Moves beyond implied")}</h3><p class="small">{wait}</p>' + (f'<ul class="small">{li}</ul>' if li else "")


def _crash_detail(rs: List[Dict]) -> str:
    out = ""
    for r in rs:
        tr = "".join(f'<tr><td class="r">{c["pred"]:.0f}%</td><td class="r">{c["actual"]:.0f}%</td><td class="r">{c["n"]}</td></tr>' for c in r["calib"])
        au = f'樣本外 AUC {r["auc"]:.2f}（0.5 等於亂猜）。' if r.get("auc") is not None else ""
        sk = f'Brier 技能 {r["skill"]:+.2f}（大於 0 才比永遠報平常機率好）。' if r.get("skill") is not None else ""
        head = T(f'{r["days"]} 日內跌 ≥{r["dd"]:.0f}% 的校準', f'Calibration: {r["days"]}d')
        out += (f'<h3>{head}</h3><p class="small">共 {r["windows"]} 段不重疊的期間，真的大跌 {r["events"]} 段，其中事前機率偏高的 {r["n"]} 段。{au}{sk}</p>'
                + (f'<div class="scroll"><table class="mini"><thead><tr><th class="r">{T("模型當時說", "Said")}</th><th class="r">{T("實際發生", "Happened")}</th>'
                   f'<th class="r">{T("天數", "Days")}</th></tr></thead><tbody>{tr}</tbody></table></div>' if tr else ""))
    return out


def _rules_detail(r: Dict) -> str:
    def cell(x):
        return f'{x["dd5"]:.0f}%' if x["n"] >= MIN_N else T("樣本太少", "Too few cases")
    tr = "".join(f'<tr><td>{T(guard_safe(x["zh"]), x.get("en") or x["zh"])}</td><td class="r">{x["n"]}</td><td class="r">{cell(x)}</td>'
                 f'<td class="r">{x["base_dd5"]:.0f}%</td></tr>' for x in r["rules"])
    return (f'<h3>{T("各條警報規則", "Each alarm rule")}</h3><div class="scroll"><table class="mini"><thead><tr><th>{T("規則", "Rule")}</th><th class="r">{T("次數", "n")}</th>'
            f'<th class="r">{T("之後再跌 5%", "Further 5%")}</th><th class="r">{T("任何一天", "Any day")}</th></tr></thead><tbody>{tr}</tbody></table></div>')


def _fam_detail(rs: List[Dict]) -> str:
    r = rs[-1] if rs else {}
    li = "".join(f'<li>{_e(f["name"])}：{f["n"]} 起，' + (f'命中 {f["rate"]:.0f}%' if f["n"] >= MIN_N and f.get("rate") is not None else "樣本太少") + "</li>"
                 for f in r.get("fam") or [])
    return f'<h3>{T("已發出的警報，依類型", "Sent alerts by type")}</h3><ul class="small">{li}</ul>' if li else ""


def sec_track_record(eng) -> str:
    rows = rows_all(eng)
    lz, le = _lead(rows)
    pv = next((r for r in rows if "brier" in r), None)
    iv = next((r for r in rows if "pending" in r), None)
    ru = next((r for r in rows if "rules" in r), None)
    det = ((_preview_detail(pv) if pv else "") + (_implied_detail(iv) if iv else "") + _crash_detail([r for r in rows if "calib" in r])
           + (_rules_detail(ru) if ru else "") + _fam_detail([r for r in rows if "fam" in r]))
    note = T(f"命中＝事後真的發生。基準＝不用模型也能得到的成績，贏過基準要連 90% 信賴區間都高過它；樣本少於 {MIN_N} 次一律標「樣本太少」，只列次數，不算命中率。"
             "崩跌機率用彼此不重疊的期間計算，「機率偏高」指模型機率高於當時的歷史平均，用的是逐年只看當時資料的樣本外成績；校準表的天數彼此重疊，只看大方向。"
             "技術型態訊號的成績單在「技術型態觀察」頁。過去成績不代表未來，也不構成投資建議。",
             f"A hit means it really happened. The baseline is what you get with no model; beating it needs the 90% interval above it. Under {MIN_N} cases only counts are shown. "
             "Crash windows do not overlap and are out-of-sample. Past record, not advice.")
    body = (f'<p class="rimp big2"><b>{T(lz, le)}</b></p>'
            + (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("預測", "Call")}</th><th class="r">{T("樣本", "n")}</th><th class="r">{T("命中", "Hits")}</th>'
               f'<th class="r">{T("命中率", "Rate")}</th><th>{T("對照基準", "Baseline")}</th><th class="r">{T("誤報", "False")}</th><th>{T("結論", "Verdict")}</th></tr></thead>'
               f'<tbody>{"".join(_tr(r) for r in rows)}</tbody></table></div>' if rows else "")
            + (f'<details class="sgx"><summary>{T("細節：猜錯的案例、校準表和各條規則", "Details: misses, calibration, rules")}</summary>{det}</details>' if det else "")
            + f'<p class="note">{note}</p>')
    return card("全站預測成績單：本站說過的話準不準", "Site-wide track record", body, "wide")

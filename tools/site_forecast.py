"""每日總經情勢 and 一個月預判 (top of 總覽).
- 每日總經情勢: research_feed/macro_voice.json holds a spoken-style script from a daily cloud routine; the build turns it
  into market/macro.mp3 and the card plays it.  Without audio the card still shows the script.
- 一個月預判: research_feed/forecast.json, written by a cloud routine twice a week: dated calls with a probability and a
  measure, each scored afterwards, plus what this season's reports say about next quarter.
Static content: the routines commit the JSON and the site shows it as written."""
from __future__ import annotations

import asyncio
import hashlib
import html
import json
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

from tools.sitekit import card, guard_safe

log = logging.getLogger(__name__)
FILE = Path(__file__).resolve().parents[1] / "research_feed" / "forecast.json"   # public repo only
TREND = {"上修": "up", "下修": "dn"}
VOICE = "zh-TW-HsiaoChenNeural"
AUDIO = {"v": ""}            # set by make_audio when market/macro.mp3 was written for this build


def _json(f: Path) -> Dict:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def load() -> Dict:
    return _json(FILE)


def voice() -> Dict:
    return _json(FILE.with_name("macro_voice.json"))


def _e(x) -> str:
    return html.escape(guard_safe(str(x or "")))


def _src(xs) -> str:
    out = []
    for s in xs or []:
        if not isinstance(s, dict):
            continue
        u = str(s.get("url") or "")
        name = _e(s.get("name") or "來源")
        out.append(f'<a href="{html.escape(u)}" target="_blank" rel="noopener noreferrer">{name}</a>' if u.startswith("https://") else name)
    return "、".join(out)


def make_audio(dest: Path) -> None:
    """market/macro.mp3 from the daily script; a failure only means the card shows text."""
    AUDIO["v"] = ""
    script = guard_safe(str(voice().get("script") or "")).strip()
    if not script:
        return
    try:
        import edge_tts
        dest.mkdir(parents=True, exist_ok=True)
        job = lambda: asyncio.run(edge_tts.Communicate(script, VOICE).save(str(dest / "macro.mp3")))   # noqa: E731
        with ThreadPoolExecutor(1) as pool:   # its own thread: the site build already runs inside an event loop
            pool.submit(job).result(timeout=180)
        AUDIO["v"] = hashlib.sha1(script.encode("utf-8")).hexdigest()[:10]
    except Exception:  # noqa: BLE001
        log.exception("macro audio failed")


def voice_history(x: Dict, keep: int = 12) -> List[Dict]:
    """Every edition the build has seen (the routines overwrite macro_voice.json), newest first. Kept in data_cache/econ_* so
    the Actions cache carries it between builds; the current file is added when its `updated` is new."""
    try:
        from wsb.config import DATA_DIR
        f = DATA_DIR / "econ_voice_hist.json"
        hist = json.loads(f.read_text(encoding="utf-8")).get("items", []) if f.exists() else []
    except Exception:  # noqa: BLE001
        return [x]
    seen = {h.get("updated") for h in hist}                # editions published before the archive existed (public repo seed)
    hist = sorted(hist + [h for h in (_json(FILE.with_name("macro_voice_hist.json")).get("items") or []) if h.get("updated") not in seen],
                  key=lambda h: str(h.get("updated") or ""), reverse=True)
    if x.get("updated") and not any(h.get("updated") == x["updated"] for h in hist):
        hist = ([{k: x.get(k) for k in ("updated", "date", "edition", "one", "script")}] + hist)[:keep]
        try:
            tmp = f.with_suffix(".tmp")
            tmp.write_text(json.dumps({"items": hist}, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, f)
        except Exception:  # noqa: BLE001
            pass
    return hist


def _paras(x: Dict) -> str:
    return "".join(f"<p>{_e(p)}</p>" for p in str(x.get("script") or "").split("\n") if p.strip())


def _ed_pill(ed: str) -> str:
    return f'<span class="pill{" warn" if ed == "加班" else ""}">{_e("🚨 緊急加班" if ed == "加班" else ed)}</span> ' if ed else ""


def sec_macro_voice(eng) -> str:
    x = voice()
    if not x.get("script"):
        return ""
    earlier = [h for h in voice_history(x) if h.get("updated") != x.get("updated") and h.get("script")][:5]
    player = (f'<audio controls preload="none" style="width:100%" src="market/macro.mp3?v={AUDIO["v"]}">你的瀏覽器不支援播放。</audio>' if AUDIO["v"] else "")
    prev = ""
    if earlier:
        prev = (f'<details class="sgx"><summary>前幾班（{len(earlier)} 班）</summary>'
                + "".join(f'<div class="rpt"><p>{_ed_pill(str(h.get("edition") or ""))}<span class="muted small">{_e(h.get("updated"))}</span><br>'
                          f'<b>{_e(h.get("one"))}</b></p><details class="sgx"><summary>看文字稿</summary>{_paras(h)}</details></div>' for h in earlier)
                + '<p class="small muted">語音只有最新一班；前幾班保留文字稿。</p></details>')
    body = (f'<p class="rimp big2">{_ed_pill(str(x.get("edition") or ""))}<b>一句話看懂：{_e(x.get("one"))}</b></p>{player}'
            f'<details class="sgx"><summary>看文字稿</summary>{_paras(x)}</details>' + prev
            + f'<p class="note">{_e(x.get("updated") or x.get("date"))} 雲端 AI 撰稿。每天兩班：早上 6:30 講前一晚美國（週一含週末），平日晚上 8:00 預告今晚；'
            f'市場異常大動時會加班。語音由電腦合成。是對當下的解讀，不是預測保證。不構成投資建議。</p>')
    return card("每日總經情勢", "Daily macro", body, "wide", sub="用聽的，約兩三分鐘")


def _rows(xs, *keys) -> List[Dict]:
    return [x for x in xs or [] if isinstance(x, dict) and all(x.get(k) for k in keys)]


def _table(xs: List[Dict]) -> str:
    rows = "".join(f'<tr><td><b>{_e(x["name"])}</b></td><td>{_e(x["call"])}</td><td class="r">{_e(x.get("prob"))}%</td><td class="r">{_e(str(x.get("by") or "")[5:])}</td></tr>' for x in xs)
    return (f'<div class="scroll"><table class="mini"><thead><tr><th>項目</th><th>預判</th><th class="r">機率</th><th class="r">到期</th></tr></thead><tbody>{rows}</tbody></table></div>')


def _why(xs: List[Dict]) -> str:
    return "".join(f'<p class="small"><b>{_e(x["name"])}</b>：現在 {_e(x.get("now"))} {_e(x.get("why"))} 可能錯在：{_e(x.get("wrong"))} 算法：{_e(x.get("measure"))}</p>' for x in xs)


def _score(xs: List[Dict]) -> str:
    done = [x for x in xs if x.get("result") in ("對", "錯")]
    if not done:
        return ""
    hit = sum(x["result"] == "對" for x in done)
    ps = [float(x["prob"]) for x in done if x.get("prob") is not None]
    avg = sum(ps) / len(ps) if ps else 0.0
    rows = "".join(f'<p class="small"><b>{_e(x["name"])}</b>（估 {_e(x.get("prob"))}%）<b class="{"up" if x["result"] == "對" else "dn"}">{_e(x["result"])}</b>：{_e(x.get("note"))}</p>' for x in done)
    return (f'<p class="small"><b>過去成績</b>：{len(done)} 題對 {hit} 題（{hit / len(done) * 100:.0f}%），當時平均估 {avg:.0f}%，兩者越接近代表機率估得越準。</p>'
            f'<details class="sgx"><summary>看每一題結果</summary>{rows}</details>')


def sec_forecast(eng) -> str:
    d = load()
    calls = _rows(d.get("calls"), "name", "call")
    if not calls:
        return ""
    live = [x for x in calls if not x.get("result")]
    paths = _rows(d.get("paths"), "name")
    nq = _rows((d.get("nextq") or {}).get("groups"), "name", "read")
    pline = "｜".join(f'{_e(p["name"])} <b>{_e(p.get("prob"))}%</b>' for p in paths)
    nline = "｜".join(f'{_e(g["name"])} <b class="{TREND.get(g.get("trend"), "")}">{_e(g.get("trend"))}</b>' for g in nq)
    more = ("".join(f'<p class="small"><b>{_e(p["name"])}</b>：{_e(p.get("what"))}</p>' for p in paths)
            + "".join(f'<p class="small"><b>{_e(g["name"])}</b>：{_e(g["read"])} {_e(g.get("evidence"))}</p>' for g in nq)
            + _why(live) + (f'<p class="small muted">來源：{_src(d.get("sources"))}</p>' if d.get("sources") else ""))
    body = (f'<p class="rimp"><b>一句話看懂：{_e(d.get("one"))}</b></p>'
            + (f'<p class="small">三種走法：{pline}</p>' if pline else "") + _table(live)
            + (f'<p class="small"><b>下一季</b>：{_e((d.get("nextq") or {}).get("one"))}</p><p class="small">{nline}</p>' if nq else "")
            + _score(calls) + f'<details class="sgx"><summary>看依據</summary>{more}</details>'
            + f'<p class="note">機率是 AI 的主觀判斷，{_e(d.get("updated"))} 更新，每週兩次，到期公開對答案。不構成投資建議。</p>')
    return card("一個月後的總經，與財報裡的下一季", "One month ahead", body, "wide")

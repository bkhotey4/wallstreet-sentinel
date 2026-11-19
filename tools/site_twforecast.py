"""「AI 視角看台灣」頁：台灣總經展望卡。research_feed/tw_forecast.json（格式比照美國的 forecast.json）：
一句話、全球到台灣的因果鏈（每一環標明事實或假設）、三種走法與機率、附到期日與算法的可驗證判斷，到期後公開對答案。
靜態內容：由 AI 依官方資料撰寫後提交 JSON，網站照原樣顯示。"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict

from tools.site_forecast import _e, _json, _rows, _score, _src, _table, _why
from tools.sitekit import card

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "tw_forecast.json"   # public repo only
KIND = {"事實": "up", "假設": "warn", "推論": "warn"}


def load() -> Dict:
    return _json(FILE)


def _pick(x: Dict, *keys) -> str:
    for k in keys:
        if x.get(k):
            return str(x[k])
    return ""


def norm_chain(xs) -> list:
    """The daily routine owns the JSON: accept a few spellings of the chain fields (step/name/link, read/what/text,
    kind/type/label, evidence/source) and plain strings, so a wording change never blanks the card."""
    out = []
    for x in xs or []:
        if isinstance(x, str) and x.strip():
            out.append({"step": x.strip(), "kind": "", "read": "", "evidence": ""})
        elif isinstance(x, dict):
            step = _pick(x, "step", "name", "link", "title", "node")
            if step:
                out.append({"step": step, "kind": _pick(x, "kind", "type", "label", "fact_or_hypothesis"),
                            "read": _pick(x, "read", "what", "text", "detail", "now"), "evidence": _pick(x, "evidence", "source", "sources", "data")})
    return out


def _chain(xs) -> str:
    out = []
    for i, x in enumerate(norm_chain(xs), 1):
        k = str(x.get("kind") or "")
        out.append(f'<li><b>{i}. {_e(x["step"])}</b>' + (f' <span class="pill {KIND.get(k, "")}">{_e(k)}</span>' if k else "")
                   + (f'：{_e(x["read"])}' if x.get("read") else "")
                   + (f'<div class="small muted">依據：{_e(x["evidence"])}</div>' if x.get("evidence") else "") + "</li>")
    return f'<ol class="lines">{"".join(out)}</ol>' if out else ""


def _hyp(h) -> str:
    """The tracked user hypothesis (「台股 2027 下半年泡沫破裂」), if the routine writes one: a string or a dict."""
    if isinstance(h, str) and h.strip():
        return f'<h3>追蹤中的假設</h3><p class="small">{_e(h)}</p>'
    if not isinstance(h, dict):
        return ""
    parts = [f'<h3>追蹤中的假設：{_e(_pick(h, "name", "claim", "title") or "台股 2027 下半年泡沫破裂")}</h3>']
    for k, lab in (("status", "現在"), ("for", "支持的證據"), ("against", "反對的證據"), ("watch", "接下來看"), ("note", "說明")):
        v = h.get(k)
        if isinstance(v, list):
            v = "；".join(str(i) for i in v if i)
        if v:
            parts.append(f'<p class="small"><b>{lab}</b>：{_e(v)}</p>')
    return "".join(parts)


def sec_tw_forecast(eng) -> str:
    d = load()
    calls = _rows(d.get("calls"), "name", "call")
    if not calls or not d.get("one"):
        return ""
    today = date.today().isoformat()
    live = [x for x in calls if not x.get("result") and str(x.get("by") or "9999")[:10] >= today]
    overdue = [x for x in calls if not x.get("result") and str(x.get("by") or "9999")[:10] < today]
    paths = _rows(d.get("paths") or d.get("scenarios"), "name")
    chain = d.get("chain") or []
    pline = "｜".join(f'{_e(p["name"])} <b>{_e(p.get("prob"))}%</b>' for p in paths)
    ch = _chain(chain)
    more = (("<h3>全球到台灣的因果鏈</h3>" + ch if ch else "") + _hyp(d.get("hypothesis"))
            + "".join(f'<p class="small"><b>{_e(p["name"])}</b>：{_e(p.get("what"))}</p>' for p in paths)
            + _why(live) + (f'<p class="small muted">來源：{_src(d.get("sources"))}</p>' if d.get("sources") else ""))
    one = str(d.get("one") or "").removeprefix("一句話看懂：")
    body = (f'<p class="rimp big2"><b>一句話看懂：{_e(one)}</b></p>'
            + (f'<p class="small">三種走法：{pline}</p>' if pline else "") + _table(live)
            + (f'<p class="small muted">另有 {len(overdue)} 題已到期、等對答案：{"、".join(_e(x["name"]) for x in overdue)}。</p>' if overdue else "")
            + _score(calls) + f'<details class="sgx"><summary>看因果鏈、三種走法與依據</summary>{more}</details>'
            + f'<p class="note">AI 依央行、主計總處、國發會、財政部、證交所的公開資料撰寫；因果鏈每一環標明「事實」或「假設」。'
              f'機率是主觀判斷，{_e(d.get("updated"))} 更新，到期公開對答案。不構成投資建議。</p>')
    h = card("台灣總經展望：從聯準會、AI 訂單到新台幣與台股", "Taiwan macro outlook", body, "wide",
             sub="因果鏈、三種走法、附到期日的判斷")
    return h.replace('<section class="card', '<section id="twforecast" class="card', 1)

"""風險退潮・進場環境 page, part 1: the seven-gauge cool-down checklist and the history of past cool-downs.
Model data only; history, not a forecast, and never a buy signal or a price to buy at."""
from __future__ import annotations

from tools.sitekit import T, card, cls, esc, num

PHASE = {"stress": ("🔴 壓力還在", "dn"), "cooling": ("🟡 退燒中", "warn"), "mixed": ("🟡 部分偏緊", "warn"), "calm": ("🟢 平時狀態", "up")}

NOTE_CHECK = ("七項都是「壓力有沒有退」的同步指標，回到正常代表市場環境變穩，不代表價格便宜，也不保證不會再跌。"
              "危機底部常常出現在這些指標還很糟的時候（例如 2009 年 3 月），等它們全部轉好時，股價通常已經從低點漲了一段：這是「確認」和「價格」之間的取捨。"
              "高收益債用 HYG 對 50 日均線、股票廣度用本站評分池站上 200 日線的比例。不是投資建議。")
NOTE_HIST = ("「退燒日」的兩種算法：①VIX 收盤曾 ≥ 30，之後第一次收盤 < 20（{v_since} 年起）；②五項指標（VIX、期限結構、HYG、200 日線、OFR）"
             "在過去半年內曾經只剩 0–1 項正常，之後回到至少 4 項正常（{g_since} 年起）。每一波只算一次。"
             "「之後半年最深再跌」是退燒日之後 6 個月內，標普從當天往下跌最多的幅度；「半年內 VIX 又 ≥ 30」就是假退燒。"
             "最後一列「任何一天」是對照組：如果退燒日的數字沒有比它好，代表等退燒並沒有帶來額外好處，只是比較安心。"
             "樣本只有十幾次，數字會隨新事件變動。歷史統計，不是預測。")


def headline(r) -> str:
    from wsb.analytics import cooldown as CD
    ph = CD.phase(r)
    zh, _ = PHASE[ph]
    k, n = r["n_ok"], r["n"]
    tail = {"stress": f"{n} 項只有 {k} 項回到正常，市場還在緊張",
            "cooling": f"最近半年 VIX 曾經 ≥ 30，現在 {n} 項有 {k} 項回到正常",
            "mixed": f"最近半年沒有出現高壓（VIX ≥ 30），但 {n} 項只有 {k} 項正常，還沒轉好的：" + "、".join(c.get("short", c["k"]) for c in r["checks"] if c["ok"] is False),
            "calm": f"最近半年沒有出現高壓（VIX ≥ 30），{n} 項有 {k} 項正常"}[ph]
    return f"一句話看懂：{zh}——{tail}。"


def sec_cool_check(eng) -> str:
    from wsb.analytics import cooldown as CD
    try:
        r = CD.build(eng)
    except Exception:  # noqa: BLE001
        return ""
    if not r.get("available"):
        return ""
    eng._cooldown = r
    ph = CD.phase(r)
    rows = "".join(
        f'<li><b class="{"up" if c["ok"] else "dn" if c["ok"] is not None else "muted"}">{"✅" if c["ok"] else "⬜" if c["ok"] is not None else "—"}</b> '
        f'{T(c["zh"], "")}<span class="small muted">　{T(c["txt"], "")}</span></li>' for c in r["checks"])
    last = (f'VIX 上一次收盤 ≥ 30 是 {r["last_hot"]}（{r["since_hot"]} 個交易日前）。' if r.get("last_hot") else "")
    body = (f'<div class="bth"><span class="bign {PHASE[ph][1]}">{r["n_ok"]} / {r["n"]}</span>'
            f'<b>{T(headline(r), "")}</b></div><ul class="dlst">{rows}</ul>'
            + (f'<p class="small muted">{T(last, "")}</p>' if last else "")
            + f'<details class="sgx"><summary>{T("這張表怎麼看", "How to read")}</summary><p class="note">{T(NOTE_CHECK, "")}</p></details>')
    return card("退燒檢查表：壓力是不是真的在退", "Cool-down checklist", body, "wide")


def _cell(x, pct_up=True) -> str:
    if not x or x.get("med") is None:
        return '<span class="muted">—</span>'
    up = f'<div class="small muted">{T("上漲", "up")} {x["up"]:.0f}%</div>' if pct_up and x.get("up") is not None else ""
    return f'<b class="{cls(x["med"])}">{num(x["med"], 1, sign=True, pct=True)}</b>{up}'


def _row(label, s, n, muted=False) -> str:
    rf = s.get("reflare") or {}
    m = ' class="muted"' if muted else ""
    return (f'<tr><td{m}>{T(label, "")}</td><td class="r">{n}</td>'
            + "".join(f'<td class="r">{_cell(s.get(h))}</td>' for h in ("3m", "6m", "12m"))
            + f'<td class="r">{_cell(s.get("dd6"), False)}</td><td class="r">{num(rf.get("pct"), 0)}%</td></tr>')


def _verdict(name, x) -> str:
    s, b = x["sum"], x["base"]
    d_ret = (s["12m"]["med"] or 0) - (b["12m"]["med"] or 0)
    d_up = (s["12m"]["up"] or 0) - (b["12m"]["up"] or 0)
    calmer = (s["dd6"]["med"] or 0) > (b["dd6"]["med"] or 0) and (s["reflare"]["pct"] or 0) < (b["reflare"]["pct"] or 0)
    if d_ret < -3:
        how = f"之後 12 個月中位數 {num(s['12m']['med'], 1, sign=True, pct=True)}，反而比隨便挑一天的 {num(b['12m']['med'], 1, sign=True, pct=True)} 差（空頭市場裡第一次退燒常是假的）"
    elif d_ret > 3:
        how = f"之後 12 個月中位數 {num(s['12m']['med'], 1, sign=True, pct=True)}，比平常的 {num(b['12m']['med'], 1, sign=True, pct=True)} 好"
    else:
        how = (f"之後 12 個月報酬跟平常差不多（{num(s['12m']['med'], 1, sign=True, pct=True)} vs {num(b['12m']['med'], 1, sign=True, pct=True)}）"
               + (f"，但上漲機率較高（{num(s['12m']['up'], 0)}% vs {num(b['12m']['up'], 0)}%）、過程較平順" if d_up > 5 and calmer else ""))
    return f"{name}（{len(x['rows'])} 次）{how}"


def sec_cool_history(eng) -> str:
    r = getattr(eng, "_cooldown", None)
    if r is None:
        from wsb.analytics import cooldown as CD
        try:
            r = CD.build(eng)
        except Exception:  # noqa: BLE001
            return ""
    v, g = r.get("vix"), r.get("gauge")
    if not v:
        return ""
    rows = _row("① VIX 從 ≥ 30 回到 < 20", v["sum"], len(v["rows"])) + _row(f"　對照：{v['since']} 年起任何一天", v["base"], "—", muted=True)
    if g and g["rows"]:
        rows += _row("② 五項指標回到 ≥ 4 項正常", g["sum"], len(g["rows"])) + _row(f"　對照：{g['since']} 年起任何一天", g["base"], "—", muted=True)
    lead = "一句話看懂：" + "；".join(x for x in (_verdict("只看 VIX 退燒", v), _verdict("五項指標一起退燒", g) if g and g["rows"] else "") if x) + "。"
    recent = "、".join(x["date"] for x in v["rows"][-6:])
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("退燒的定義", "Definition")}</th><th class="r">{T("次數", "Episodes")}</th>'
            f'<th class="r">{T("3 個月後", "3m")}</th><th class="r">{T("6 個月後", "6m")}</th><th class="r">{T("12 個月後", "12m")}</th>'
            f'<th class="r">{T("之後半年最深再跌（中位數）", "Worst fall in 6m")}</th><th class="r">{T("半年內 VIX 又 ≥ 30", "Re-flare")}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            f'<p class="small muted">{T("最近幾次 VIX 退燒日：" + esc(recent), "")}</p>'
            f'<details class="sgx"><summary>{T("怎麼算的", "Method")}</summary><p class="note">'
            f'{T(NOTE_HIST.format(v_since=v["since"], g_since=(g or {}).get("since", "—")), "")}</p></details>')
    return card("退燒之後：歷史上標普怎麼走", "After past cool-downs", body, "wide")


CSS = ".warn{color:var(--warn)}"
